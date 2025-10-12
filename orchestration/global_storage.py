"""
Global storage operations for the data pipeline.

This module handles storing data in global tables and creating links to assets.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from db.models import (
    RealEstateTransactionGlobal, MavatPlanGlobal, RamiParcelGlobal,
    DecisiveRecordGlobal, Yad2ListingGlobal, GisDataGlobal, GovMapDataGlobal, GovDataGlobal,
    AssetToDeal, AssetToMavatPlan, AssetToRamiParcel,
    AssetToDecisiveRecord, AssetToYad2Listing, AssetToGisData, AssetToGovMapData, AssetToGovData
)


def compute_key_fingerprint(key_dict: Dict[str, Any]) -> str:
    """Compute a stable fingerprint from cadastral identifiers."""
    normalized = {}
    for key in sorted(key_dict.keys()):
        value = key_dict[key]
        if value is not None:
            normalized[key] = str(value).strip()
    
    key_json = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(key_json.encode('utf-8')).hexdigest()


def build_key_dict(city: str, street: str, number: Optional[int], 
                  block: Optional[str], parcel: Optional[str], 
                  subparcel: Optional[str] = None) -> Dict[str, Any]:
    """Build key dictionary from cadastral identifiers."""
    return {
        'city': city,
        'street': street,
        'number': number,
        'block': block,
        'parcel': parcel,
        'subparcel': subparcel,
    }


def store_transaction_global(
    session: Session,
    asset_id: int,
    deal_data: Dict[str, Any],
    key_dict: Dict[str, Any],
    ttl_days: int = 30
) -> Tuple[RealEstateTransactionGlobal, bool]:
    """Store or update a transaction in the global table and create link."""
    
    key_fp = compute_key_fingerprint(key_dict)
    
    # Build external ID (prefer deal_id, fallback to content hash)
    deal_id = deal_data.get('deal_id')
    if deal_id:
        external_id = str(deal_id)
    else:
        content = {
            'date': deal_data.get('deal_date'),
            'price': deal_data.get('deal_amount'),
            'address': deal_data.get('address'),
            'key_dict': key_dict,
        }
        content_json = json.dumps(content, sort_keys=True, separators=(',', ':'))
        external_id = hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]
    
    # Create or update global transaction
    global_transaction, created = session.query(RealEstateTransactionGlobal).filter_by(
        deal_id=external_id
    ).first(), False
    
    if not global_transaction:
        global_transaction = RealEstateTransactionGlobal(
            deal_id=external_id,
            key_fp=key_fp,
            key_json=key_dict,
            date=deal_data.get('deal_date'),
            price=deal_data.get('deal_amount'),
            rooms=deal_data.get('rooms'),
            area=deal_data.get('area'),
            floor=deal_data.get('floor'),
            address=deal_data.get('address'),
            raw=deal_data,
            ttl_expires_at=datetime.utcnow() + timedelta(days=ttl_days),
        )
        session.add(global_transaction)
        session.flush()  # Get the ID
        created = True
    else:
        # Update existing record
        global_transaction.key_fp = key_fp
        global_transaction.key_json = key_dict
        global_transaction.date = deal_data.get('deal_date')
        global_transaction.price = deal_data.get('deal_amount')
        global_transaction.rooms = deal_data.get('rooms')
        global_transaction.area = deal_data.get('area')
        global_transaction.floor = deal_data.get('floor')
        global_transaction.address = deal_data.get('address')
        global_transaction.raw = deal_data
        global_transaction.ttl_expires_at = datetime.utcnow() + timedelta(days=ttl_days)
    
    # Create link
    link, link_created = session.query(AssetToDeal).filter_by(
        asset_id=asset_id,
        transaction_id=global_transaction.id
    ).first(), False
    
    if not link:
        link = AssetToDeal(
            asset_id=asset_id,
            transaction_id=global_transaction.id
        )
        session.add(link)
        link_created = True
    
    return global_transaction, created


def store_mavat_plan_global(
    session: Session,
    asset_id: int,
    plan_data: Dict[str, Any],
    key_dict: Dict[str, Any],
    external_id: Optional[str] = None,
    ttl_days: int = 7
) -> Tuple[MavatPlanGlobal, bool]:
    """Store or update a MAVAT plan in the global table and create link."""
    
    key_fp = compute_key_fingerprint(key_dict)
    
    # Build external ID (prefer provided, fallback to content hash)
    if not external_id:
        content_json = json.dumps(plan_data, sort_keys=True, separators=(',', ':'))
        external_id = hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]
    
    # Create or update global plan
    global_plan, created = session.query(MavatPlanGlobal).filter_by(
        plan_id=external_id
    ).first(), False
    
    if not global_plan:
        global_plan = MavatPlanGlobal(
            plan_id=external_id,
            key_fp=key_fp,
            key_json=key_dict,
            plan_number=plan_data.get('plan_number'),
            plan_title=plan_data.get('plan_title'),
            status=plan_data.get('status'),
            effective_date=plan_data.get('effective_date'),
            plan_type=plan_data.get('plan_type'),
            raw=plan_data,
            ttl_expires_at=datetime.utcnow() + timedelta(days=ttl_days),
        )
        session.add(global_plan)
        session.flush()  # Get the ID
        created = True
    else:
        # Update existing record
        global_plan.key_fp = key_fp
        global_plan.key_json = key_dict
        global_plan.plan_number = plan_data.get('plan_number')
        global_plan.plan_title = plan_data.get('plan_title')
        global_plan.status = plan_data.get('status')
        global_plan.effective_date = plan_data.get('effective_date')
        global_plan.plan_type = plan_data.get('plan_type')
        global_plan.raw = plan_data
        global_plan.ttl_expires_at = datetime.utcnow() + timedelta(days=ttl_days)
    
    # Create link
    link, link_created = session.query(AssetToMavatPlan).filter_by(
        asset_id=asset_id,
        plan_id=global_plan.id
    ).first(), False
    
    if not link:
        link = AssetToMavatPlan(
            asset_id=asset_id,
            plan_id=global_plan.id
        )
        session.add(link)
        link_created = True
    
    return global_plan, created


def store_rami_parcel_global(
    session: Session,
    asset_id: int,
    parcel_data: Dict[str, Any],
    key_dict: Dict[str, Any],
    external_id: Optional[str] = None,
    ttl_days: int = 7
) -> Tuple[RamiParcelGlobal, bool]:
    """Store or update a RAMI parcel in the global table and create link."""
    
    key_fp = compute_key_fingerprint(key_dict)
    
    # Build external ID (prefer provided, fallback to content hash)
    if not external_id:
        content_json = json.dumps(parcel_data, sort_keys=True, separators=(',', ':'))
        external_id = hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]
    
    # Create or update global parcel
    global_parcel, created = session.query(RamiParcelGlobal).filter_by(
        rami_id=external_id
    ).first(), False
    
    if not global_parcel:
        global_parcel = RamiParcelGlobal(
            rami_id=external_id,
            key_fp=key_fp,
            key_json=key_dict,
            plan_number=parcel_data.get('plan_number'),
            plan_name=parcel_data.get('plan_name'),
            status=parcel_data.get('status'),
            status_date=parcel_data.get('status_date'),
            market_value=parcel_data.get('market_value'),
            building_rights=parcel_data.get('building_rights'),
            raw=parcel_data,
            ttl_expires_at=datetime.utcnow() + timedelta(days=ttl_days),
        )
        session.add(global_parcel)
        session.flush()  # Get the ID
        created = True
    else:
        # Update existing record
        global_parcel.key_fp = key_fp
        global_parcel.key_json = key_dict
        global_parcel.plan_number = parcel_data.get('plan_number')
        global_parcel.plan_name = parcel_data.get('plan_name')
        global_parcel.status = parcel_data.get('status')
        global_parcel.status_date = parcel_data.get('status_date')
        global_parcel.market_value = parcel_data.get('market_value')
        global_parcel.building_rights = parcel_data.get('building_rights')
        global_parcel.raw = parcel_data
        global_parcel.ttl_expires_at = datetime.utcnow() + timedelta(days=ttl_days)
    
    # Create link
    link, link_created = session.query(AssetToRamiParcel).filter_by(
        asset_id=asset_id,
        parcel_id=global_parcel.id
    ).first(), False
    
    if not link:
        link = AssetToRamiParcel(
            asset_id=asset_id,
            parcel_id=global_parcel.id
        )
        session.add(link)
        link_created = True
    
    return global_parcel, created


def store_decisive_record_global(
    session: Session,
    asset_id: int,
    record_data: Dict[str, Any],
    key_dict: Dict[str, Any],
    external_id: Optional[str] = None,
    url: Optional[str] = None,
    ttl_days: int = 7
) -> Tuple[DecisiveRecordGlobal, bool]:
    """Store or update a decisive record in the global table and create link."""
    
    key_fp = compute_key_fingerprint(key_dict)
    
    # Build external ID (prefer provided, fallback to content hash)
    if not external_id:
        content_json = json.dumps(record_data, sort_keys=True, separators=(',', ':'))
        external_id = hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]
    
    # Create or update global record
    global_record, created = session.query(DecisiveRecordGlobal).filter_by(
        decisive_id=external_id
    ).first(), False
    
    if not global_record:
        global_record = DecisiveRecordGlobal(
            decisive_id=external_id,
            key_fp=key_fp,
            key_json=key_dict,
            appraiser=record_data.get('appraiser'),
            date=record_data.get('date'),
            appraised_value=record_data.get('appraised_value'),
            url=url,
            raw=record_data,
            ttl_expires_at=datetime.utcnow() + timedelta(days=ttl_days),
        )
        session.add(global_record)
        session.flush()  # Get the ID
        created = True
    else:
        # Update existing record
        global_record.key_fp = key_fp
        global_record.key_json = key_dict
        global_record.appraiser = record_data.get('appraiser')
        global_record.date = record_data.get('date')
        global_record.appraised_value = record_data.get('appraised_value')
        global_record.url = url
        global_record.raw = record_data
        global_record.ttl_expires_at = datetime.utcnow() + timedelta(days=ttl_days)
    
    # Create link
    link, link_created = session.query(AssetToDecisiveRecord).filter_by(
        asset_id=asset_id,
        record_id=global_record.id
    ).first(), False
    
    if not link:
        link = AssetToDecisiveRecord(
            asset_id=asset_id,
            record_id=global_record.id
        )
        session.add(link)
        link_created = True
    
    return global_record, created


def store_yad2_listing_global(
    session: Session,
    asset_id: int,
    listing_data: Dict[str, Any],
    key_dict: Dict[str, Any],
    external_id: Optional[str] = None,
    url: Optional[str] = None,
    ttl_days: int = 1
) -> Tuple[Yad2ListingGlobal, bool]:
    """Store or update a Yad2 listing in the global table and create link."""
    
    key_fp = compute_key_fingerprint(key_dict)
    
    # Build external ID (prefer provided, fallback to content hash)
    if not external_id:
        content_json = json.dumps(listing_data, sort_keys=True, separators=(',', ':'))
        external_id = hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]
    
    # Create or update global listing
    global_listing, created = session.query(Yad2ListingGlobal).filter_by(
        external_id=external_id
    ).first(), False
    
    if not global_listing:
        global_listing = Yad2ListingGlobal(
            external_id=external_id,
            key_fp=key_fp,
            key_json=key_dict,
            title=listing_data.get('title'),
            price=listing_data.get('price'),
            address=listing_data.get('address'),
            rooms=listing_data.get('rooms'),
            area=listing_data.get('area'),
            property_type=listing_data.get('property_type'),
            url=url,
            raw=listing_data,
            ttl_expires_at=datetime.utcnow() + timedelta(days=ttl_days),
        )
        session.add(global_listing)
        session.flush()  # Get the ID
        created = True
    else:
        # Update existing record
        global_listing.key_fp = key_fp
        global_listing.key_json = key_dict
        global_listing.title = listing_data.get('title')
        global_listing.price = listing_data.get('price')
        global_listing.address = listing_data.get('address')
        global_listing.rooms = listing_data.get('rooms')
        global_listing.area = listing_data.get('area')
        global_listing.property_type = listing_data.get('property_type')
        global_listing.url = url
        global_listing.raw = listing_data
        global_listing.ttl_expires_at = datetime.utcnow() + timedelta(days=ttl_days)
    
    # Create link
    link, link_created = session.query(AssetToYad2Listing).filter_by(
        asset_id=asset_id,
        listing_id=global_listing.id
    ).first(), False
    
    if not link:
        link = AssetToYad2Listing(
            asset_id=asset_id,
            listing_id=global_listing.id
        )
        session.add(link)
        link_created = True
    
    return global_listing, created


def store_gis_data_global(
    session: Session,
    asset_id: int,
    gis_data: Dict[str, Any],
    key_dict: Dict[str, Any],
    external_id: Optional[str] = None,
    ttl_days: int = 7
) -> Tuple[GisDataGlobal, bool]:
    """Store or update GIS data in the global table and create link."""
    
    key_fp = compute_key_fingerprint(key_dict)
    
    # Build external ID (prefer provided, fallback to content hash)
    if not external_id:
        content_json = json.dumps(gis_data, sort_keys=True, separators=(',', ':'))
        external_id = hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]
    
    # Create or update global GIS data
    global_gis_data, created = session.query(GisDataGlobal).filter_by(
        gis_id=external_id
    ).first(), False
    
    if not global_gis_data:
        global_gis_data = GisDataGlobal(
            gis_id=external_id,
            key_fp=key_fp,
            key_json=key_dict,
            x=gis_data.get('x'),
            y=gis_data.get('y'),
            block=gis_data.get('block'),
            parcel=gis_data.get('parcel'),
            city=gis_data.get('city'),
            blocks_data=gis_data.get('blocks', []),
            parcels_data=gis_data.get('parcels', []),
            permits_data=gis_data.get('permits', []),
            rights_data=gis_data.get('rights', []),
            shelters_data=gis_data.get('shelters', []),
            green_areas_data=gis_data.get('green', []),
            noise_levels_data=gis_data.get('noise', []),
            antennas_data=gis_data.get('antennas', []),
            land_use_detailed_data=gis_data.get('land_use_detailed', []),
            preservation_data=gis_data.get('preservation', []),
            dangerous_buildings_data=gis_data.get('dangerous', []),
            local_plans_data=gis_data.get('local_plans', []),
            city_plans_data=gis_data.get('city_plans', []),
            addresses_data=gis_data.get('addresses', []),
            raw=gis_data,
            ttl_expires_at=datetime.utcnow() + timedelta(days=ttl_days),
        )
        session.add(global_gis_data)
        session.flush()  # Get the ID
        created = True
    else:
        # Update existing record
        global_gis_data.key_fp = key_fp
        global_gis_data.key_json = key_dict
        global_gis_data.x = gis_data.get('x')
        global_gis_data.y = gis_data.get('y')
        global_gis_data.block = gis_data.get('block')
        global_gis_data.parcel = gis_data.get('parcel')
        global_gis_data.city = gis_data.get('city')
        global_gis_data.blocks_data = gis_data.get('blocks', [])
        global_gis_data.parcels_data = gis_data.get('parcels', [])
        global_gis_data.permits_data = gis_data.get('permits', [])
        global_gis_data.rights_data = gis_data.get('rights', [])
        global_gis_data.shelters_data = gis_data.get('shelters', [])
        global_gis_data.green_areas_data = gis_data.get('green', [])
        global_gis_data.noise_levels_data = gis_data.get('noise', [])
        global_gis_data.antennas_data = gis_data.get('antennas', [])
        global_gis_data.land_use_detailed_data = gis_data.get('land_use_detailed', [])
        global_gis_data.preservation_data = gis_data.get('preservation', [])
        global_gis_data.dangerous_buildings_data = gis_data.get('dangerous', [])
        global_gis_data.local_plans_data = gis_data.get('local_plans', [])
        global_gis_data.city_plans_data = gis_data.get('city_plans', [])
        global_gis_data.addresses_data = gis_data.get('addresses', [])
        global_gis_data.raw = gis_data
        global_gis_data.ttl_expires_at = datetime.utcnow() + timedelta(days=ttl_days)
    
    # Create link
    link, link_created = session.query(AssetToGisData).filter_by(
        asset_id=asset_id,
        gis_data_id=global_gis_data.id
    ).first(), False
    
    if not link:
        link = AssetToGisData(
            asset_id=asset_id,
            gis_data_id=global_gis_data.id
        )
        session.add(link)
        link_created = True
    
    return global_gis_data, created


def store_govmap_data_global(
    session: Session,
    asset_id: int,
    govmap_data: Dict[str, Any],
    key_dict: Dict[str, Any],
    external_id: Optional[str] = None,
    ttl_days: int = 7
) -> Tuple[GovMapDataGlobal, bool]:
    """Store or update GovMap data in the global table and create link."""
    
    key_fp = compute_key_fingerprint(key_dict)
    
    # Build external ID (prefer provided, fallback to content hash)
    if not external_id:
        content_json = json.dumps(govmap_data, sort_keys=True, separators=(',', ':'))
        external_id = hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]
    
    # Create or update global GovMap data
    global_govmap_data, created = session.query(GovMapDataGlobal).filter_by(
        govmap_id=external_id
    ).first(), False
    
    if not global_govmap_data:
        global_govmap_data = GovMapDataGlobal(
            govmap_id=external_id,
            key_fp=key_fp,
            key_json=key_dict,
            address=govmap_data.get('address'),
            x=govmap_data.get('x'),
            y=govmap_data.get('y'),
            block=govmap_data.get('block'),
            parcel=govmap_data.get('parcel'),
            city=govmap_data.get('city'),
            autocomplete_data=govmap_data.get('api_data', {}).get('autocomplete', {}),
            parcel_data=govmap_data.get('api_data', {}).get('parcel', {}),
            layers_catalog_data=govmap_data.get('api_data', {}).get('layers_catalog', {}),
            search_types_data=govmap_data.get('api_data', {}).get('search_types', {}),
            raw=govmap_data,
            ttl_expires_at=datetime.utcnow() + timedelta(days=ttl_days),
        )
        session.add(global_govmap_data)
        session.flush()  # Get the ID
        created = True
    else:
        # Update existing record
        global_govmap_data.key_fp = key_fp
        global_govmap_data.key_json = key_dict
        global_govmap_data.address = govmap_data.get('address')
        global_govmap_data.x = govmap_data.get('x')
        global_govmap_data.y = govmap_data.get('y')
        global_govmap_data.block = govmap_data.get('block')
        global_govmap_data.parcel = govmap_data.get('parcel')
        global_govmap_data.city = govmap_data.get('city')
        global_govmap_data.autocomplete_data = govmap_data.get('api_data', {}).get('autocomplete', {})
        global_govmap_data.parcel_data = govmap_data.get('api_data', {}).get('parcel', {})
        global_govmap_data.layers_catalog_data = govmap_data.get('api_data', {}).get('layers_catalog', {})
        global_govmap_data.search_types_data = govmap_data.get('api_data', {}).get('search_types', {})
        global_govmap_data.raw = govmap_data
        global_govmap_data.ttl_expires_at = datetime.utcnow() + timedelta(days=ttl_days)
    
    # Create link
    link, link_created = session.query(AssetToGovMapData).filter_by(
        asset_id=asset_id,
        govmap_data_id=global_govmap_data.id
    ).first(), False
    
    if not link:
        link = AssetToGovMapData(
            asset_id=asset_id,
            govmap_data_id=global_govmap_data.id
        )
        session.add(link)
        link_created = True
    
    return global_govmap_data, created


def store_gov_data_global(
    session: Session,
    asset_id: int,
    gov_data: Dict[str, Any],
    key_dict: Dict[str, Any],
    external_id: Optional[str] = None,
    ttl_days: int = 7
) -> Tuple[GovDataGlobal, bool]:
    """Store or update Gov data in the global table and create link."""
    
    key_fp = compute_key_fingerprint(key_dict)
    
    # Build external ID (prefer provided, fallback to content hash)
    if not external_id:
        content_json = json.dumps(gov_data, sort_keys=True, separators=(',', ':'))
        external_id = hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]
    
    # Create or update global Gov data
    global_gov_data, created = session.query(GovDataGlobal).filter_by(
        gov_id=external_id
    ).first(), False
    
    if not global_gov_data:
        global_gov_data = GovDataGlobal(
            gov_id=external_id,
            key_fp=key_fp,
            key_json=key_dict,
            block=gov_data.get('block'),
            parcel=gov_data.get('parcel'),
            transactions_data=gov_data.get('transactions', []),
            decisive_data=gov_data.get('decisive', []),
            rami_plans_data=gov_data.get('rami_plans', []),
            raw=gov_data,
            ttl_expires_at=datetime.utcnow() + timedelta(days=ttl_days),
        )
        session.add(global_gov_data)
        session.flush()  # Get the ID
        created = True
    else:
        # Update existing record
        global_gov_data.key_fp = key_fp
        global_gov_data.key_json = key_dict
        global_gov_data.block = gov_data.get('block')
        global_gov_data.parcel = gov_data.get('parcel')
        global_gov_data.transactions_data = gov_data.get('transactions', [])
        global_gov_data.decisive_data = gov_data.get('decisive', [])
        global_gov_data.rami_plans_data = gov_data.get('rami_plans', [])
        global_gov_data.raw = gov_data
        global_gov_data.ttl_expires_at = datetime.utcnow() + timedelta(days=ttl_days)
    
    # Create link
    link, link_created = session.query(AssetToGovData).filter_by(
        asset_id=asset_id,
        gov_data_id=global_gov_data.id
    ).first(), False
    
    if not link:
        link = AssetToGovData(
            asset_id=asset_id,
            gov_data_id=global_gov_data.id
        )
        session.add(link)
        link_created = True
    
    return global_gov_data, created
