from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text, Index, UniqueConstraint
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
    floor = Column(String(50))
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


# Global source tables (mapped to Django models)
class RealEstateTransactionGlobal(Base):
    """Global real estate transaction table for deduplication."""
    
    __tablename__ = "core_realestatetransactionglobal"
    
    id = Column(Integer, primary_key=True)
    deal_id = Column(String(100), unique=True, index=True)
    key_fp = Column(String(64), index=True)
    key_json = Column(JSON, default=dict)
    
    date = Column(DateTime)
    price = Column(Integer)
    rooms = Column(Integer)
    area = Column(Float)
    floor = Column(Integer)
    address = Column(String(200))
    raw = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ttl_expires_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_deal_id', 'deal_id'),
        Index('idx_key_fp', 'key_fp'),
        Index('idx_ttl_expires_at', 'ttl_expires_at'),
    )


class MavatPlanGlobal(Base):
    """Global MAVAT plan table for deduplication."""
    
    __tablename__ = "core_mavatplanglobal"
    
    id = Column(Integer, primary_key=True)
    plan_id = Column(String(100), unique=True, index=True)
    key_fp = Column(String(64), index=True)
    key_json = Column(JSON, default=dict)
    
    plan_number = Column(String(100))
    plan_title = Column(String(500))
    status = Column(String(100))
    effective_date = Column(DateTime)
    plan_type = Column(String(100))
    raw = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ttl_expires_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_plan_id', 'plan_id'),
        Index('idx_key_fp', 'key_fp'),
        Index('idx_ttl_expires_at', 'ttl_expires_at'),
    )


class RamiParcelGlobal(Base):
    """Global RAMI parcel table for deduplication."""
    
    __tablename__ = "core_ramiparcelglobal"
    
    id = Column(Integer, primary_key=True)
    rami_id = Column(String(100), unique=True, index=True)
    key_fp = Column(String(64), index=True)
    key_json = Column(JSON, default=dict)
    
    plan_number = Column(String(100))
    plan_name = Column(String(500))
    status = Column(String(100))
    status_date = Column(DateTime)
    market_value = Column(Float)
    building_rights = Column(Float)
    raw = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ttl_expires_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_rami_id', 'rami_id'),
        Index('idx_key_fp', 'key_fp'),
        Index('idx_ttl_expires_at', 'ttl_expires_at'),
    )


class DecisiveRecordGlobal(Base):
    """Global decisive appraisal record table for deduplication."""
    
    __tablename__ = "core_decisiverecordglobal"
    
    id = Column(Integer, primary_key=True)
    decisive_id = Column(String(100), unique=True, index=True)
    key_fp = Column(String(64), index=True)
    key_json = Column(JSON, default=dict)
    
    appraiser = Column(String(200))
    date = Column(DateTime)
    appraised_value = Column(Float)
    url = Column(String(500))
    raw = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ttl_expires_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_decisive_id', 'decisive_id'),
        Index('idx_key_fp', 'key_fp'),
        Index('idx_ttl_expires_at', 'ttl_expires_at'),
    )


class Yad2ListingGlobal(Base):
    """Global Yad2 listing table for deduplication."""
    
    __tablename__ = "core_yad2listingglobal"
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String(100), unique=True, index=True)
    key_fp = Column(String(64), index=True)
    key_json = Column(JSON, default=dict)
    
    title = Column(String(500))
    price = Column(Integer)
    address = Column(String(200))
    rooms = Column(Integer)
    area = Column(Float)
    property_type = Column(String(100))
    url = Column(String(500))
    raw = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ttl_expires_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_external_id', 'external_id'),
        Index('idx_key_fp', 'key_fp'),
        Index('idx_ttl_expires_at', 'ttl_expires_at'),
    )


class GisDataGlobal(Base):
    """Global GIS data table for deduplication."""
    
    __tablename__ = "core_gisdataglobal"
    
    id = Column(Integer, primary_key=True)
    gis_id = Column(String(100), unique=True, index=True)
    key_fp = Column(String(64), index=True)
    key_json = Column(JSON, default=dict)
    
    # Core GIS data fields
    x = Column(Float)
    y = Column(Float)
    block = Column(String(50))
    parcel = Column(String(50))
    city = Column(String(100))
    
    # GIS data components
    blocks_data = Column(JSON, default=list)
    parcels_data = Column(JSON, default=list)
    permits_data = Column(JSON, default=list)
    rights_data = Column(JSON, default=list)
    shelters_data = Column(JSON, default=list)
    green_areas_data = Column(JSON, default=list)
    noise_levels_data = Column(JSON, default=list)
    antennas_data = Column(JSON, default=list)
    land_use_detailed_data = Column(JSON, default=list)
    preservation_data = Column(JSON, default=list)
    dangerous_buildings_data = Column(JSON, default=list)
    local_plans_data = Column(JSON, default=list)
    city_plans_data = Column(JSON, default=list)
    addresses_data = Column(JSON, default=list)
    
    raw = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ttl_expires_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_gis_id', 'gis_id'),
        Index('idx_key_fp', 'key_fp'),
        Index('idx_ttl_expires_at', 'ttl_expires_at'),
        Index('idx_block_parcel', 'block', 'parcel'),
    )


class GovMapDataGlobal(Base):
    """Global GovMap data table for deduplication."""
    
    __tablename__ = "core_govmapdataglobal"
    
    id = Column(Integer, primary_key=True)
    govmap_id = Column(String(100), unique=True, index=True)
    key_fp = Column(String(64), index=True)
    key_json = Column(JSON, default=dict)
    
    # Core GovMap data fields
    address = Column(String(200))
    x = Column(Float)
    y = Column(Float)
    block = Column(String(50))
    parcel = Column(String(50))
    city = Column(String(100))
    
    # GovMap API data
    autocomplete_data = Column(JSON, default=dict)
    parcel_data = Column(JSON, default=dict)
    layers_catalog_data = Column(JSON, default=dict)
    search_types_data = Column(JSON, default=dict)
    
    raw = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ttl_expires_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_govmap_id', 'govmap_id'),
        Index('idx_key_fp', 'key_fp'),
        Index('idx_ttl_expires_at', 'ttl_expires_at'),
        Index('idx_block_parcel', 'block', 'parcel'),
    )


class GovDataGlobal(Base):
    """Global Gov data table for deduplication."""
    
    __tablename__ = "core_govdataglobal"
    
    id = Column(Integer, primary_key=True)
    gov_id = Column(String(100), unique=True, index=True)
    key_fp = Column(String(64), index=True)
    key_json = Column(JSON, default=dict)
    
    # Core Gov data fields
    block = Column(String(50))
    parcel = Column(String(50))
    
    # Gov data components
    transactions_data = Column(JSON, default=list)
    decisive_data = Column(JSON, default=list)
    rami_plans_data = Column(JSON, default=list)
    
    raw = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ttl_expires_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_gov_id', 'gov_id'),
        Index('idx_key_fp', 'key_fp'),
        Index('idx_ttl_expires_at', 'ttl_expires_at'),
        Index('idx_block_parcel', 'block', 'parcel'),
    )


# Link tables (mapped to Django models)
class AssetToDeal(Base):
    """Link table connecting assets to global real estate transactions."""
    
    __tablename__ = "core_assettodeal"
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("core_asset.id"), index=True)
    transaction_id = Column(Integer, ForeignKey("core_realestatetransactionglobal.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('asset_id', 'transaction_id', name='unique_asset_transaction'),
        Index('idx_asset_id', 'asset_id'),
        Index('idx_transaction_id', 'transaction_id'),
    )


class AssetToMavatPlan(Base):
    """Link table connecting assets to global MAVAT plans."""
    
    __tablename__ = "core_assettomavatplan"
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("core_asset.id"), index=True)
    plan_id = Column(Integer, ForeignKey("core_mavatplanglobal.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('asset_id', 'plan_id', name='unique_asset_plan'),
        Index('idx_asset_id', 'asset_id'),
        Index('idx_plan_id', 'plan_id'),
    )


class AssetToRamiParcel(Base):
    """Link table connecting assets to global RAMI parcels."""
    
    __tablename__ = "core_assettoramiparcel"
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("core_asset.id"), index=True)
    parcel_id = Column(Integer, ForeignKey("core_ramiparcelglobal.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('asset_id', 'parcel_id', name='unique_asset_parcel'),
        Index('idx_asset_id', 'asset_id'),
        Index('idx_parcel_id', 'parcel_id'),
    )


class AssetToDecisiveRecord(Base):
    """Link table connecting assets to global decisive records."""
    
    __tablename__ = "core_assettodecisiverecord"
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("core_asset.id"), index=True)
    record_id = Column(Integer, ForeignKey("core_decisiverecordglobal.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('asset_id', 'record_id', name='unique_asset_record'),
        Index('idx_asset_id', 'asset_id'),
        Index('idx_record_id', 'record_id'),
    )


class AssetToYad2Listing(Base):
    """Link table connecting assets to global Yad2 listings."""
    
    __tablename__ = "core_assettoyad2listing"
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("core_asset.id"), index=True)
    listing_id = Column(Integer, ForeignKey("core_yad2listingglobal.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('asset_id', 'listing_id', name='unique_asset_listing'),
        Index('idx_asset_id', 'asset_id'),
        Index('idx_listing_id', 'listing_id'),
    )


class AssetToGisData(Base):
    """Link table connecting assets to global GIS data."""
    
    __tablename__ = "core_assettogisdata"
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("core_asset.id"), index=True)
    gis_data_id = Column(Integer, ForeignKey("core_gisdataglobal.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('asset_id', 'gis_data_id', name='unique_asset_gis_data'),
        Index('idx_asset_id', 'asset_id'),
        Index('idx_gis_data_id', 'gis_data_id'),
    )


class AssetToGovMapData(Base):
    """Link table connecting assets to global GovMap data."""
    
    __tablename__ = "core_assettogovmapdata"
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("core_asset.id"), index=True)
    govmap_data_id = Column(Integer, ForeignKey("core_govmapdataglobal.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('asset_id', 'govmap_data_id', name='unique_asset_govmap_data'),
        Index('idx_asset_id', 'asset_id'),
        Index('idx_govmap_data_id', 'govmap_data_id'),
    )


class AssetToGovData(Base):
    """Link table connecting assets to global Gov data."""
    
    __tablename__ = "core_assettogovdata"
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("core_asset.id"), index=True)
    gov_data_id = Column(Integer, ForeignKey("core_govdataglobal.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('asset_id', 'gov_data_id', name='unique_asset_gov_data'),
        Index('idx_asset_id', 'asset_id'),
        Index('idx_gov_data_id', 'gov_data_id'),
    )


__all__ = [
    "Listing", "SourceRecord", "Transaction",
    "RealEstateTransactionGlobal", "MavatPlanGlobal", "RamiParcelGlobal", 
    "DecisiveRecordGlobal", "Yad2ListingGlobal", "GisDataGlobal", "GovMapDataGlobal", "GovDataGlobal",
    "AssetToDeal", "AssetToMavatPlan", "AssetToRamiParcel", 
    "AssetToDecisiveRecord", "AssetToYad2Listing", "AssetToGisData", "AssetToGovMapData", "AssetToGovData"
]
