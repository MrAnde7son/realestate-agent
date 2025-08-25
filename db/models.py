from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from .database import Base


class Listing(Base):
    """Real estate listing scraped from external services."""

    __tablename__ = "listings"

    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    price = Column(Float)
    address = Column(String(255))
    rooms = Column(Float)
    floor = Column(Integer)
    size = Column(Float)
    property_type = Column(String(100))
    description = Column(Text)
    url = Column(String(500))
    listing_id = Column(String(100), unique=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    sources = relationship("SourceRecord", back_populates="listing", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="listing", cascade="all, delete-orphan")


class SourceRecord(Base):
    """Generic JSON record from an external data source."""

    __tablename__ = "source_records"

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), index=True)
    source = Column(String(50), index=True)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="sources")


class Transaction(Base):
    """Historical real estate transaction information."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), index=True)
    deal_date = Column(String(50))
    deal_amount = Column(Float)
    rooms = Column(String(50))
    floor = Column(String(50))
    asset_type = Column(String(50))
    year_built = Column(String(50))
    area = Column(Float)
    raw = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="transactions")


__all__ = ["Listing", "SourceRecord", "Transaction"]
