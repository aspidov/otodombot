from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from ..scraper.crawler import OtodomCrawler
from ..db.database import SessionLocal
from ..db.models import Listing, PriceHistory
from ..evaluation.location import evaluate_location
from ..evaluation.chatgpt import rate_listing
from ..notifications.telegram_bot import notify


def process_listings():
    crawler = OtodomCrawler()
    links = crawler.fetch_listings()
    session = SessionLocal()
    for url in links:
        html = crawler.fetch_listing_details(url)
        price = crawler.parse_price(html)
        if price is None:
            # skip listings without a price
            continue

        external_id = crawler.parse_listing_id(html)

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
        else:
            # simple placeholder evaluation
            notes = rate_listing(html, api_key="YOUR_OPENAI_API_KEY")
            location = evaluate_location("Warsaw", api_key="YOUR_GOOGLE_API_KEY")
            listing = Listing(url=url, external_id=external_id, title="", location=str(location), notes=notes, is_good=True, price=price)
            session.add(listing)
            session.commit()
            session.add(PriceHistory(listing=listing, price=price))
            session.commit()
            notify(token="YOUR_TELEGRAM_TOKEN", chat_id="CHAT_ID", messages=[f"Found listing: {url}"])
    session.close()


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(process_listings, "interval", hours=1, next_run_time=datetime.utcnow())
    scheduler.start()
