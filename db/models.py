"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, UniqueConstraint, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

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


class BuildingPermit(Base):
    """Building permit record fetched from municipal GIS."""

    __tablename__ = "building_permits"
    __table_args__ = (
        UniqueConstraint("permission_num", name="uq_permission_num"),
    )

    id = Column(Integer, primary_key=True)
    permission_num = Column(String, index=True)
    request_num = Column(String)
    url = Column(String)
    gush = Column(String)
    helka = Column(String)
    data = Column(JSON)
    scraped_at = Column(DateTime, default=datetime.utcnow)


class BuildingRights(Base):
    """Building rights or privilege page details from GIS."""

    __tablename__ = "building_rights"
    __table_args__ = (
        UniqueConstraint("gush", "helka", name="uq_rights_gush_helka"),
    )

    id = Column(Integer, primary_key=True)
    gush = Column(String, index=True)
    helka = Column(String, index=True)
    file_path = Column(String)
    content_type = Column(String)
    data = Column(JSON)
    scraped_at = Column(DateTime, default=datetime.utcnow)


class DecisiveAppraisal(Base):
    """Decisive appraisal decision from gov.il."""

    __tablename__ = "decisive_appraisals"
    __table_args__ = (
        UniqueConstraint("title", "pdf_url", name="uq_decisive_title_pdf"),
    )

    id = Column(Integer, primary_key=True)
    title = Column(String)
    date = Column(String)
    appraiser = Column(String)
    committee = Column(String)
    pdf_url = Column(String)
    data = Column(JSON)
    scraped_at = Column(DateTime, default=datetime.utcnow)


class RamiValuation(Base):
    """Valuation or plan record from RAMI."""

    __tablename__ = "rami_valuations"
    __table_args__ = (
        UniqueConstraint("plan_number", name="uq_rami_plan_number"),
    )

    id = Column(Integer, primary_key=True)
    plan_number = Column(String, index=True)
    name = Column(String)
    data = Column(JSON)
    scraped_at = Column(DateTime, default=datetime.utcnow)

# New models for asset enrichment pipeline
class Asset(Base):
    __tablename__ = 'assets'
    
    id = Column(Integer, primary_key=True)
    scope_type = Column(String(50), nullable=False)  # 'address', 'neighborhood', 'street', 'city', 'parcel'
    city = Column(String(100))
    neighborhood = Column(String(100))
    street = Column(String(200))
    number = Column(Integer)
    gush = Column(String(20))
    helka = Column(String(20))
    lat = Column(Float)
    lon = Column(Float)
    normalized_address = Column(String(500))
    status = Column(String(20), default='pending')  # 'pending', 'enriching', 'ready', 'error'
    meta = Column(JSON, default={})
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    source_records = relationship("SourceRecord", back_populates="asset")
    transactions = relationship("RealEstateTransaction", back_populates="asset")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_asset_scope_type', 'scope_type'),
        Index('idx_asset_city', 'city'),
        Index('idx_asset_neighborhood', 'neighborhood'),
        Index('idx_asset_street', 'street'),
        Index('idx_asset_gush', 'gush'),
        Index('idx_asset_helka', 'helka'),
        Index('idx_asset_normalized_address', 'normalized_address'),
        Index('idx_asset_status', 'status'),
    )

class SourceRecord(Base):
    __tablename__ = 'source_records'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    source = Column(String(50), nullable=False)  # 'yad2', 'nadlan', 'gis_permit', 'gis_rights', 'rami_plan', 'tabu'
    external_id = Column(String(100))
    title = Column(String(500))
    url = Column(String(500))
    file_path = Column(String(500))
    raw = Column(JSON)
    fetched_at = Column(DateTime, default=func.now())
    
    # Relationships
    asset = relationship("Asset", back_populates="source_records")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_source_record_asset_id', 'asset_id'),
        Index('idx_source_record_source', 'source'),
        Index('idx_source_record_external_id', 'external_id'),
        UniqueConstraint('source', 'external_id', name='uq_source_external_id'),
    )

class RealEstateTransaction(Base):
    __tablename__ = 'real_estate_transactions'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    deal_id = Column(String(100))
    date = Column(DateTime)
    price = Column(Integer)
    rooms = Column(Integer)
    area = Column(Float)
    floor = Column(Integer)
    address = Column(String(200))
    raw = Column(JSON)
    fetched_at = Column(DateTime, default=func.now())
    
    # Relationships
    asset = relationship("Asset", back_populates="transactions")
    
    # Indexes
    __table_args__ = (
        Index('idx_transaction_asset_id', 'asset_id'),
        Index('idx_transaction_deal_id', 'deal_id'),
    )
