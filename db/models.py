"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, UniqueConstraint

from .database import Base


class Listing(Base):
    """Generic real estate listing supporting multiple data sources."""

    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_external_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True)
    external_id = Column(String, index=True)
    title = Column(String)
    price = Column(Float)
    address = Column(String)
    rooms = Column(Float)
    floor = Column(String)
    size = Column(Float)
    property_type = Column(String)
    description = Column(String)
    images = Column(JSON)
    documents = Column(JSON)
    contact_info = Column(JSON)
    features = Column(JSON)
    url = Column(String)
    date_posted = Column(String)
    scraped_at = Column(DateTime, default=datetime.utcnow)
