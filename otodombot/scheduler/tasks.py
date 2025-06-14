from datetime import datetime
import logging
from apscheduler.schedulers.background import BackgroundScheduler

from ..scraper.crawler import OtodomCrawler
from ..config import load_config
from ..db.database import SessionLocal
from ..db.models import Listing, PriceHistory
from ..evaluation.location import evaluate_location
from ..evaluation.chatgpt import rate_listing, extract_location
from ..notifications.telegram_bot import notify


def process_listings():
    logging.info("Starting listings processing")
    search = load_config()
    crawler = OtodomCrawler(search)
    links = crawler.fetch_listings(max_pages=5)
    logging.info("Processing %d links", len(links))
    session = SessionLocal()
    for url in links:
        logging.info("Processing listing %s", url)
        html = crawler.fetch_listing_details(url)
        price = crawler.parse_price(html)
        if price is None:
            # skip listings without a price
            logging.info("Skipping %s due to missing price", url)
            continue

        external_id = crawler.parse_listing_id(html)
        description = crawler.parse_description(html)
        address = crawler.parse_address(html)
        if not address and description:
            address = extract_location(description, api_key="YOUR_OPENAI_API_KEY")
        location = evaluate_location(address, api_key="YOUR_GOOGLE_API_KEY") if address else {}

        listing = session.query(Listing).filter_by(url=url).first()
        if not listing and external_id:
            listing = session.query(Listing).filter_by(external_id=external_id).first()
        if listing:
            if external_id and listing.external_id != external_id:
                listing.external_id = external_id
            if listing.price != price:
                listing.price = price
                session.add(PriceHistory(listing=listing, price=price))
            session.commit()
            logging.info("Updated listing %s", url)
        else:
            # simple placeholder evaluation
            notes = rate_listing(html, api_key="YOUR_OPENAI_API_KEY")
            listing = Listing(
                url=url,
                external_id=external_id,
                title="",
                description=description,
                location=str(location),
                notes=notes,
                is_good=True,
                price=price,
            )
            session.add(listing)
            session.commit()
            session.add(PriceHistory(listing=listing, price=price))
            session.commit()
            logging.info("Added new listing %s", url)
            notify(token="YOUR_TELEGRAM_TOKEN", chat_id="CHAT_ID", messages=[f"Found listing: {url}"])
    session.close()


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(process_listings, "interval", hours=1, next_run_time=datetime.utcnow())
    scheduler.start()
    logging.info("Scheduler started")
