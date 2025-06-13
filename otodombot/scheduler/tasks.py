from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from ..scraper.crawler import OtodomCrawler
from ..db.database import SessionLocal
from ..db.models import Listing
from ..evaluation.location import evaluate_location
from ..evaluation.chatgpt import rate_listing
from ..notifications.telegram_bot import notify


def process_listings():
    crawler = OtodomCrawler()
    links = crawler.fetch_listings()
    session = SessionLocal()
    for url in links:
        if session.query(Listing).filter_by(url=url).first():
            continue
        html = crawler.fetch_listing_details(url)
        # simple placeholder evaluation
        notes = rate_listing(html, api_key="YOUR_OPENAI_API_KEY")
        location = evaluate_location("Warsaw", api_key="YOUR_GOOGLE_API_KEY")
        listing = Listing(url=url, title="", location=str(location), notes=notes, is_good=True)
        session.add(listing)
        session.commit()
        notify(token="YOUR_TELEGRAM_TOKEN", chat_id="CHAT_ID", messages=[f"Found listing: {url}"])
    session.close()


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(process_listings, "interval", hours=1, next_run_time=datetime.utcnow())
    scheduler.start()
