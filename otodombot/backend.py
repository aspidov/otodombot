from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn

from .db.database import init_db, SessionLocal
from .db.models import Listing, CommuteTime

app = FastAPI(title="Otodom Listings API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    logging.info("Initializing database")
    init_db()

@app.get("/listings")
def get_listings():
    logging.info("Fetching listings from database")
    session = SessionLocal()
    listings = []
    for l in session.query(Listing).all():
        if l.lat is None or l.lng is None:
            continue
        commutes = {c.destination: c.minutes for c in l.commutes}
        listings.append(
            {
                "id": l.id,
                "title": l.title,
                "lat": l.lat,
                "lng": l.lng,
                "price": l.price,
                "url": l.url,
                "commutes": commutes,
            }
        )
    session.close()
    logging.info("Returned %d listings", len(listings))
    return listings

@app.get("/listings/{listing_id}")
def get_listing(listing_id: int):
    logging.info("Fetching listing %s", listing_id)
    session = SessionLocal()
    listing = session.query(Listing).get(listing_id)
    session.close()
    if not listing:
        logging.warning("Listing %s not found", listing_id)
        return {"detail": "Listing not found"}
    return {
        "id": listing.id,
        "title": listing.title,
        "description": listing.description,
        "location": listing.location,
        "price": listing.price,
        "lat": listing.lat,
        "lng": listing.lng,
        "notes": listing.notes,
        "url": listing.url,
        "commutes": {c.destination: c.minutes for c in listing.commutes},
    }

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler("otodombot.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    uvicorn.run("otodombot.backend:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
