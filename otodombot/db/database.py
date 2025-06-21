from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

from .models import Base

engine = create_engine("sqlite:///otodom.db")
SessionLocal = sessionmaker(bind=engine)


def init_db():
    logging.debug("Initializing database schema")
    Base.metadata.create_all(bind=engine)
