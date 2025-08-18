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
