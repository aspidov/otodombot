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
    description = Column(String)
    location = Column(String)
    price = Column(Integer)
    is_good = Column(Boolean, default=False)
    notes = Column(String)
    last_parsed = Column(DateTime, default=datetime.utcnow)

    photos = relationship("Photo", back_populates="listing", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    url = Column(String, nullable=False)
    path = Column(String, nullable=False)

    listing = relationship("Listing", back_populates="photos")
