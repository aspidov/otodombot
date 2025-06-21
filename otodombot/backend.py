from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .db.database import init_db, SessionLocal
from .db.models import Listing

app = FastAPI(title="Otodom Listings API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/listings")
def get_listings():
    session = SessionLocal()
    listings = [
        {
            "id": l.id,
            "title": l.title,
            "lat": l.lat,
            "lng": l.lng,
            "price": l.price,
            "url": l.url,
        }
        for l in session.query(Listing).all()
        if l.lat is not None and l.lng is not None
    ]
    session.close()
    return listings

@app.get("/listings/{listing_id}")
def get_listing(listing_id: int):
    session = SessionLocal()
    listing = session.query(Listing).get(listing_id)
    session.close()
    if not listing:
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
    }

def main():
    uvicorn.run("otodombot.backend:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
