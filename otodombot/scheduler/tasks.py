from datetime import datetime, timedelta, time
import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

from ..scraper.crawler import OtodomCrawler
from ..config import load_config
from ..db.database import SessionLocal
from ..db.models import Listing, CommuteTime
from ..evaluation.location import evaluate_location
from ..evaluation.chatgpt import rate_listing, extract_address
from ..notifications.telegram_bot import notify_listing


def next_commute_datetime(day_name: str, time_str: str) -> datetime:
    """Return next occurrence of given weekday name and HH:MM time in UTC."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    try:
        target = days.index(day_name.capitalize())
    except ValueError:
        target = 0
    hour, minute = (int(x) for x in time_str.split(":"))
    now = datetime.utcnow()
    days_ahead = (target - now.weekday() + 7) % 7
    if days_ahead == 0 and (now.time() > time(hour, minute)):
        days_ahead = 7
    date = now.date() + timedelta(days=days_ahead)
    return datetime.combine(date, time(hour, minute))


def process_listings():
    logging.info("Starting listings processing")
    config = load_config()
    crawler = OtodomCrawler(config.search, headless=config.headless)
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    session = SessionLocal()
    stale_cutoff = datetime.utcnow() - timedelta(days=1)
    stale_urls = [
        l.url
        for l in session.query(Listing)
        .filter((Listing.last_parsed == None) | (Listing.last_parsed < stale_cutoff))
    ]
    links = stale_urls + crawler.fetch_listings(max_pages=5)
    links = list(dict.fromkeys(links))
    logging.info("Processing %d links", len(links))
    for url in links:
        logging.info("Processing listing %s", url)
        html = crawler.fetch_listing_details(url)
        price = crawler.parse_price(html)
        if price is None:
            # skip listings without a price
            logging.info("Skipping %s due to missing price", url)
            continue

        external_id = crawler.parse_listing_id(html)
        is_new = False
        title = crawler.parse_title(html)
        description = crawler.parse_description(html)
        address = ''
        photos = crawler.parse_photos(html)
        if openai_key:
            address = extract_address(
                description=description,
                page_address=address,
                html=html,
                api_key=openai_key,
            )

        listing = session.query(Listing).filter_by(url=url).first()
        if not listing and external_id:
            listing = session.query(Listing).filter_by(external_id=external_id).first()
        if listing:
            if external_id and listing.external_id != external_id:
                listing.external_id = external_id
            listing.title = title
            listing.description = description
            listing.location = address
            listing.price = price
            # nothing to store for photos
            listing.last_parsed = datetime.utcnow()
            session.commit()
            logging.info("Updated listing %s", url)

        else:
            # Build a short summary for ChatGPT instead of sending full HTML
            summary_lines = [
                f"Title: {title}",
                f"Price: {price}",
            ]
            if address:
                summary_lines.append(f"Address: {address}")
            if description:
                summary_lines.append("Description:\n" + description[:4000])
            summary = "\n".join(summary_lines)

            listing = Listing(
                url=url,
                external_id=external_id,
                title=title,
                description=description,
                location=address,
                price=price,
                notes="",
                is_good=True,
            )
            session.add(listing)
            session.commit()
            listing.last_parsed = datetime.utcnow()
            session.commit()
            logging.info("Added new listing %s", url)
            is_new = True

        if listing and google_key and address:
            depart = next_commute_datetime(config.commute.day, config.commute.time)
            info = evaluate_location(address, config.commute.pois, depart, google_key)
            listing.lat = info.get("lat")
            listing.lng = info.get("lng")
            session.query(CommuteTime).filter_by(listing_id=listing.id).delete()
            for poi in config.commute.pois:
                session.add(
                    CommuteTime(
                        listing_id=listing.id,
                        destination=poi,
                        minutes=info.get(poi),
                    )
                )
            session.commit()
            if is_new and telegram_token and telegram_chat_id:
                thresholds = config.commute.thresholds
                ok = True
                if thresholds:
                    for poi in config.commute.pois:
                        limit = thresholds.get(poi)
                        minutes = info.get(poi)
                        if limit is not None and (minutes is None or minutes > limit):
                            ok = False
                            break
                if ok:
                    if openai_key and not listing.notes:
                        summary_lines = [
                            f"Title: {listing.title}",
                            f"Price: {listing.price}",
                        ]
                        if listing.location:
                            summary_lines.append(f"Address: {listing.location}")
                        if listing.description:
                            summary_lines.append(
                                "Description:\n" + listing.description[:4000]
                            )
                        summary = "\n".join(summary_lines)
                        listing.notes = rate_listing(summary, api_key=openai_key)
                        session.commit()

                    text_lines = [f"{listing.title}", f"Price: {listing.price}"]
                    if listing.location:
                        text_lines.append(f"Address: {listing.location}")
                    if listing.notes:
                        text_lines.append(f"AI summary:\n{listing.notes}")
                    for poi in config.commute.pois:
                        minutes = info.get(poi)
                        if minutes is not None:
                            text_lines.append(f"{poi}: {minutes} min")
                    text_lines.append(listing.url)
                    notify_listing(
                        token=telegram_token,
                        chat_id=telegram_chat_id,
                        text="\n".join(text_lines),
                        photos=photos[:3],
                    )
    session.close()


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        process_listings, "interval", hours=1, next_run_time=datetime.utcnow()
    )
    scheduler.start()
    logging.info("Scheduler started")
