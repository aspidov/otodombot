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


def process_single_listing(url, crawler, session, config, openai_key, google_key, telegram_token, telegram_chat_ids):
    try:
        logging.info("Processing listing %s", url)
        html = crawler.fetch_listing_details(url)
        price = crawler.parse_price(html)
        if price is None:
            logging.info("Skipping %s due to missing price", url)
            return
        external_id = crawler.parse_listing_id(html)
        floor = crawler.parse_floor(html)
        if floor and config.search.ignore_floors and floor.lower() in config.search.ignore_floors:
            logging.info("Skipping %s due to floor %s", url, floor)
            return
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
        recent_cutoff = datetime.utcnow() - timedelta(days=config.reparse_after_days)
        if listing and listing.last_parsed and listing.last_parsed > recent_cutoff:
            logging.info("Skipping %s - already parsed recently", url)
            return
        if listing:
            if external_id and listing.external_id != external_id:
                setattr(listing, 'external_id', external_id)
            setattr(listing, 'title', title)
            setattr(listing, 'description', description)
            setattr(listing, 'location', address)
            setattr(listing, 'floor', floor)
            setattr(listing, 'price', price)
            setattr(listing, 'last_parsed', datetime.utcnow())
            session.commit()
            logging.info("Updated listing %s", url)
        else:
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
                floor=floor,
                price=price,
                notes="",
                is_good=True,
            )
            session.add(listing)
            session.commit()
            setattr(listing, 'last_parsed', datetime.utcnow())
            session.commit()
            logging.info("Added new listing %s", url)
            is_new = True
        if listing and google_key and address:
            depart = next_commute_datetime(config.commute.day, config.commute.time)
            info = evaluate_location(address, config.commute.pois, depart, google_key)
            lat_val = info.get("lat")
            lng_val = info.get("lng")
            if lat_val is not None:
                setattr(listing, 'lat', float(lat_val))
            if lng_val is not None:
                setattr(listing, 'lng', float(lng_val))
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
            if is_new and telegram_token and telegram_chat_ids:
                thresholds = config.commute.thresholds
                ok = True
                if thresholds:
                    for poi in config.commute.pois:
                        limit = thresholds.get(poi)
                        minutes = info.get(poi)
                        if limit is not None and (minutes is None or minutes > limit):
                            ok = False
                            break
                notes_val = getattr(listing, "notes", None)
                location_val = getattr(listing, "location", None)
                description_val = getattr(listing, "description", None)
                if ok:
                    if openai_key and (not notes_val or notes_val == ""):
                        summary_lines = [
                            f"Title: {getattr(listing, 'title', '')}",
                            f"Price: {getattr(listing, 'price', '')}",
                        ]
                        if location_val:
                            summary_lines.append(f"Address: {location_val}")
                        if description_val:
                            summary_lines.append(
                                "Description:\n" + str(description_val)[:4000]
                            )
                        summary = "\n".join(summary_lines)
                        setattr(listing, 'notes', rate_listing(summary, api_key=openai_key))
                        session.commit()
                        notes_val = getattr(listing, "notes", None)
                    text_lines = [f"<b>{getattr(listing, 'title', '')}</b>"]
                    text_lines.append(f"<b>💰 Price:</b> {getattr(listing, 'price', '')}")
                    if location_val:
                        text_lines.append(f"<b>📍 Address:</b> {location_val}")
                    if notes_val:
                        text_lines.append(f"<b>🤖 AI summary:</b>\n{notes_val[:400]}")
                    for poi in config.commute.pois:
                        minutes = info.get(poi)
                        if minutes is not None:
                            text_lines.append(f"<b>🚍 {poi}:</b> {minutes} min")
                    text_lines.append(str(getattr(listing, 'url', '')))
                    notify_listing(
                        token=telegram_token,
                        chat_id=telegram_chat_ids,
                        text="\n".join(text_lines),
                        photos=photos[:3],
                    )
    except Exception as e:
        logging.error(f"Error processing listing {url}: {e}", exc_info=True)


def process_listings():
    logging.info("Starting listings processing")
    config = load_config()
    crawler = OtodomCrawler(
        config.search, headless=config.headless, base_url=config.base_url
    )
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
    telegram_chat_ids: list[str] | None = None
    if chat_id_env:
        parts = (
            chat_id_env.replace(";", ",")
            .replace(" ", ",")
            .split(",")
        )
        telegram_chat_ids = [p for p in (part.strip() for part in parts) if p]
    session = SessionLocal()
    fetched: list[str] = []
    for sort in config.search.sorts:
        logging.info("Fetching listings using sort %s", sort)
        fetched.extend(crawler.fetch_listings(max_pages=config.max_pages, sort_by=sort))
    links = fetched
    links = list(dict.fromkeys(links))
    logging.info("Processing %d links", len(links))
    recent_cutoff = datetime.utcnow() - timedelta(days=config.reparse_after_days)
    for url in links:
        listing = session.query(Listing).filter_by(url=url).first()
        if listing and listing.last_parsed and listing.last_parsed > recent_cutoff:
            logging.info("Skipping %s - already parsed recently", url)
            continue
        process_single_listing(
            url,
            crawler,
            session,
            config,
            openai_key,
            google_key,
            telegram_token,
            telegram_chat_ids,
        )
    session.close()


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        process_listings, "interval", hours=1, next_run_time=datetime.utcnow()
    )
    scheduler.start()
    logging.info("Scheduler started")
