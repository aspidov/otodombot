from datetime import datetime
import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

from ..scraper.crawler import OtodomCrawler
from ..config import load_config
from ..db.database import SessionLocal
from ..db.models import Listing, PriceHistory, Photo
from ..evaluation.chatgpt import rate_listing, extract_location, extract_address
from ..notifications.telegram_bot import notify


def download_photo(url: str, listing_id: int, index: int) -> str:
    """Download photo to local storage if not already present."""
    photos_dir = Path("photos")
    photos_dir.mkdir(exist_ok=True)
    ext = Path(url).suffix
    if ext.lower() not in {".jpg", ".jpeg", ".png"}:
        ext = ".jpg"
    path = photos_dir / f"{listing_id}_{index}{ext}"
    if path.exists():
        return str(path)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        with path.open("wb") as f:
            f.write(resp.content)
    except Exception as exc:
        logging.warning("Failed to download photo %s: %s", url, exc)
    return str(path)


def process_listings():
    logging.info("Starting listings processing")
    config = load_config()
    crawler = OtodomCrawler(config.search, headless=config.headless)
    openai_key = os.getenv("OPENAI_API_KEY")
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
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
        title = crawler.parse_title(html)
        description = crawler.parse_description(html)
        address = crawler.parse_address(html)
        photos = crawler.parse_photos(html)
        if openai_key:
            address = extract_address(
                description=description,
                page_address=address,
                html=html,
                api_key=openai_key,
            )
        if not address and description and openai_key:
            # fallback to simple extraction from description
            address = extract_location(description, api_key=openai_key)

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
            # store new photos if not present
            for idx, photo_url in enumerate(photos):
                existing = (
                    session.query(Photo)
                    .filter_by(listing_id=listing.id, url=photo_url)
                    .first()
                )
                if not existing:
                    path = download_photo(photo_url, listing.id, idx)
                    session.add(Photo(listing_id=listing.id, url=photo_url, path=path))
            session.commit()
            logging.info("Updated listing %s", url)
        else:
            # simple placeholder evaluation
            notes = rate_listing(html, api_key=openai_key) if openai_key else ""
            listing = Listing(
                url=url,
                external_id=external_id,
                title=title,
                description=description,
                location=address,
                notes=notes,
                is_good=True,
                price=price,
            )
            session.add(listing)
            session.commit()
            session.add(PriceHistory(listing=listing, price=price))
            for idx, photo_url in enumerate(photos):
                path = download_photo(photo_url, listing.id, idx)
                session.add(Photo(listing_id=listing.id, url=photo_url, path=path))
            session.commit()
            logging.info("Added new listing %s", url)
            if telegram_token and telegram_chat_id:
                notify(
                    token=telegram_token,
                    chat_id=telegram_chat_id,
                    messages=[f"Found listing: {url}"],
                )
    session.close()


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        process_listings, "interval", hours=1, next_run_time=datetime.utcnow()
    )
    scheduler.start()
    logging.info("Scheduler started")
