from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    external_id = Column(Integer, unique=True)
    title = Column(String)
    location = Column(String)
    is_good = Column(Boolean, default=False)
    notes = Column(String)
    price = Column(Integer)

    price_history = relationship("PriceHistory", back_populates="listing", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    price = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="price_history")
