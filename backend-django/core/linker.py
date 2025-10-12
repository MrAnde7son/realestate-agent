"""
Fingerprint helpers for global source deduplication.

This module provides utilities for computing stable fingerprints from cadastral
identifiers and managing external IDs for deduplication across global source tables.
"""

import hashlib
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta


def compute_key_fingerprint(key_dict: Dict[str, Any]) -> str:
    """
    Compute a stable fingerprint from cadastral identifiers.
    
    Args:
        key_dict: Dictionary containing cadastral identifiers (block, parcel, subparcel, city, street, number)
        
    Returns:
        SHA-256 hash of the normalized key dictionary
    """
    # Normalize the key dictionary by sorting keys and handling None values
    normalized = {}
    for key in sorted(key_dict.keys()):
        value = key_dict[key]
        if value is not None:
            # Convert to string and strip whitespace
            normalized[key] = str(value).strip()
    
    # Create a stable JSON representation
    key_json = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
    
    # Compute SHA-256 hash
    return hashlib.sha256(key_json.encode('utf-8')).hexdigest()


def build_key_dict_from_asset(asset) -> Dict[str, Any]:
    """
    Build key dictionary from an Asset instance.
    
    Args:
        asset: Asset model instance
        
    Returns:
        Dictionary with cadastral identifiers
    """
    return {
        'block': asset.block,
        'parcel': asset.parcel,
        'subparcel': asset.subparcel,
        'city': asset.city,
        'street': asset.street,
        'number': asset.number,
    }


def build_key_dict_from_listing(listing) -> Dict[str, Any]:
    """
    Build key dictionary from a Listing instance (SQLAlchemy).
    
    Args:
        listing: Listing model instance
        
    Returns:
        Dictionary with cadastral identifiers
    """
    # Extract cadastral info from address or raw data
    key_dict = {
        'block': None,
        'parcel': None,
        'subparcel': None,
        'city': None,
        'street': None,
        'number': None,
    }
    
    # Try to extract from address
    if listing.address:
        # Simple address parsing - could be enhanced
        parts = listing.address.split(',')
        if len(parts) >= 2:
            key_dict['street'] = parts[0].strip()
            key_dict['city'] = parts[-1].strip()
    
    return key_dict


def build_external_id_for_deal(deal_data: Dict[str, Any], key_dict: Dict[str, Any]) -> str:
    """
    Build external ID for real estate transaction.
    
    Args:
        deal_data: Transaction data
        key_dict: Cadastral identifiers
        
    Returns:
        External ID (prefer deal_id, fallback to content hash)
    """
    # Prefer existing deal_id
    if deal_data.get('deal_id'):
        return str(deal_data['deal_id'])
    
    # Fallback to content hash
    content = {
        'date': deal_data.get('date'),
        'price': deal_data.get('price'),
        'address': deal_data.get('address'),
        'key_dict': key_dict,
    }
    content_json = json.dumps(content, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]


def build_external_id_for_mavat_plan(plan_data: Dict[str, Any], key_dict: Dict[str, Any]) -> str:
    """
    Build external ID for MAVAT plan.
    
    Args:
        plan_data: Plan data
        key_dict: Cadastral identifiers
        
    Returns:
        External ID (prefer plan_id, fallback to content hash)
    """
    # Prefer existing plan_id
    if plan_data.get('plan_id'):
        return str(plan_data['plan_id'])
    
    # Fallback to content hash
    content = {
        'plan_number': plan_data.get('plan_number'),
        'plan_title': plan_data.get('plan_title'),
        'key_dict': key_dict,
    }
    content_json = json.dumps(content, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]


def build_external_id_for_rami_parcel(parcel_data: Dict[str, Any], key_dict: Dict[str, Any]) -> str:
    """
    Build external ID for RAMI parcel.
    
    Args:
        parcel_data: Parcel data
        key_dict: Cadastral identifiers
        
    Returns:
        External ID (prefer rami_id, fallback to content hash)
    """
    # Prefer existing rami_id
    if parcel_data.get('rami_id'):
        return str(parcel_data['rami_id'])
    
    # Fallback to content hash
    content = {
        'plan_number': parcel_data.get('plan_number'),
        'plan_name': parcel_data.get('plan_name'),
        'key_dict': key_dict,
    }
    content_json = json.dumps(content, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]


def build_external_id_for_decisive_record(record_data: Dict[str, Any], key_dict: Dict[str, Any]) -> str:
    """
    Build external ID for decisive appraisal record.
    
    Args:
        record_data: Record data
        key_dict: Cadastral identifiers
        
    Returns:
        External ID (prefer decisive_id, fallback to content hash)
    """
    # Prefer existing decisive_id
    if record_data.get('decisive_id'):
        return str(record_data['decisive_id'])
    
    # Fallback to content hash
    content = {
        'appraiser': record_data.get('appraiser'),
        'date': record_data.get('date'),
        'appraised_value': record_data.get('appraised_value'),
        'key_dict': key_dict,
    }
    content_json = json.dumps(content, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]


def build_external_id_for_yad2_listing(listing_data: Dict[str, Any], key_dict: Dict[str, Any]) -> str:
    """
    Build external ID for Yad2 listing.
    
    Args:
        listing_data: Listing data
        key_dict: Cadastral identifiers
        
    Returns:
        External ID (prefer listing_id, fallback to content hash)
    """
    # Prefer existing listing_id
    if listing_data.get('listing_id'):
        return str(listing_data['listing_id'])
    
    # Fallback to content hash
    content = {
        'title': listing_data.get('title'),
        'price': listing_data.get('price'),
        'address': listing_data.get('address'),
        'key_dict': key_dict,
    }
    content_json = json.dumps(content, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(content_json.encode('utf-8')).hexdigest()[:32]


def compute_ttl_expiration(source_type: str, force: bool = False) -> Optional[datetime]:
    """
    Compute TTL expiration time for different source types.
    
    Args:
        source_type: Type of source ('nadlan', 'mavat', 'rami', 'decisive', 'yad2')
        force: Whether to force refresh regardless of TTL
        
    Returns:
        TTL expiration datetime or None if force=True
    """
    if force:
        return None
    
    now = datetime.now()
    
    # TTL periods by source type
    ttl_periods = {
        'nadlan': timedelta(days=30),      # Government transactions - longer TTL
        'mavat': timedelta(days=7),        # Planning documents - medium TTL
        'rami': timedelta(days=7),         # Planning documents - medium TTL
        'decisive': timedelta(days=7),     # Appraisals - medium TTL
        'yad2': timedelta(days=1),         # Listings - short TTL (frequent updates)
    }
    
    period = ttl_periods.get(source_type, timedelta(days=7))
    return now + period


def is_data_fresh(ttl_expires_at: Optional[datetime], force: bool = False) -> bool:
    """
    Check if data is fresh based on TTL.
    
    Args:
        ttl_expires_at: TTL expiration datetime
        force: Whether to force refresh regardless of TTL
        
    Returns:
        True if data is fresh or force=True, False otherwise
    """
    if force:
        return False
    
    if ttl_expires_at is None:
        return False
    
    return datetime.now() < ttl_expires_at


def upsert_global_transaction(deal_data: Dict[str, Any], key_dict: Dict[str, Any], force: bool = False) -> Tuple[Any, bool]:
    """
    Upsert a global real estate transaction.
    
    Args:
        deal_data: Transaction data
        key_dict: Cadastral identifiers
        force: Whether to force refresh regardless of TTL
        
    Returns:
        Tuple of (transaction_instance, created_flag)
    """
    from .models import RealEstateTransactionGlobal
    
    key_fp = compute_key_fingerprint(key_dict)
    external_id = build_external_id_for_deal(deal_data, key_dict)
    ttl_expires_at = compute_ttl_expiration('nadlan', force)
    
    defaults = {
        'key_fp': key_fp,
        'key_json': key_dict,
        'date': deal_data.get('date'),
        'price': deal_data.get('price'),
        'rooms': deal_data.get('rooms'),
        'area': deal_data.get('area'),
        'floor': deal_data.get('floor'),
        'address': deal_data.get('address'),
        'raw': deal_data,
        'ttl_expires_at': ttl_expires_at,
    }
    
    transaction, created = RealEstateTransactionGlobal.objects.update_or_create(
        deal_id=external_id,
        defaults=defaults
    )
    
    return transaction, created


def upsert_global_mavat_plan(plan_data: Dict[str, Any], key_dict: Dict[str, Any], force: bool = False) -> Tuple[Any, bool]:
    """
    Upsert a global MAVAT plan.
    
    Args:
        plan_data: Plan data
        key_dict: Cadastral identifiers
        force: Whether to force refresh regardless of TTL
        
    Returns:
        Tuple of (plan_instance, created_flag)
    """
    from .models import MavatPlanGlobal
    
    key_fp = compute_key_fingerprint(key_dict)
    external_id = build_external_id_for_mavat_plan(plan_data, key_dict)
    ttl_expires_at = compute_ttl_expiration('mavat', force)
    
    defaults = {
        'key_fp': key_fp,
        'key_json': key_dict,
        'plan_number': plan_data.get('plan_number'),
        'plan_title': plan_data.get('plan_title'),
        'status': plan_data.get('status'),
        'effective_date': plan_data.get('effective_date'),
        'plan_type': plan_data.get('plan_type'),
        'raw': plan_data,
        'ttl_expires_at': ttl_expires_at,
    }
    
    plan, created = MavatPlanGlobal.objects.update_or_create(
        plan_id=external_id,
        defaults=defaults
    )
    
    return plan, created


def upsert_global_rami_parcel(parcel_data: Dict[str, Any], key_dict: Dict[str, Any], force: bool = False) -> Tuple[Any, bool]:
    """
    Upsert a global RAMI parcel.
    
    Args:
        parcel_data: Parcel data
        key_dict: Cadastral identifiers
        force: Whether to force refresh regardless of TTL
        
    Returns:
        Tuple of (parcel_instance, created_flag)
    """
    from .models import RamiParcelGlobal
    
    key_fp = compute_key_fingerprint(key_dict)
    external_id = build_external_id_for_rami_parcel(parcel_data, key_dict)
    ttl_expires_at = compute_ttl_expiration('rami', force)
    
    defaults = {
        'key_fp': key_fp,
        'key_json': key_dict,
        'plan_number': parcel_data.get('plan_number'),
        'plan_name': parcel_data.get('plan_name'),
        'status': parcel_data.get('status'),
        'status_date': parcel_data.get('status_date'),
        'market_value': parcel_data.get('market_value'),
        'building_rights': parcel_data.get('building_rights'),
        'raw': parcel_data,
        'ttl_expires_at': ttl_expires_at,
    }
    
    parcel, created = RamiParcelGlobal.objects.update_or_create(
        rami_id=external_id,
        defaults=defaults
    )
    
    return parcel, created


def upsert_global_decisive_record(record_data: Dict[str, Any], key_dict: Dict[str, Any], force: bool = False) -> Tuple[Any, bool]:
    """
    Upsert a global decisive appraisal record.
    
    Args:
        record_data: Record data
        key_dict: Cadastral identifiers
        force: Whether to force refresh regardless of TTL
        
    Returns:
        Tuple of (record_instance, created_flag)
    """
    from .models import DecisiveRecordGlobal
    
    key_fp = compute_key_fingerprint(key_dict)
    external_id = build_external_id_for_decisive_record(record_data, key_dict)
    ttl_expires_at = compute_ttl_expiration('decisive', force)
    
    defaults = {
        'key_fp': key_fp,
        'key_json': key_dict,
        'appraiser': record_data.get('appraiser'),
        'date': record_data.get('date'),
        'appraised_value': record_data.get('appraised_value'),
        'url': record_data.get('url'),
        'raw': record_data,
        'ttl_expires_at': ttl_expires_at,
    }
    
    record, created = DecisiveRecordGlobal.objects.update_or_create(
        decisive_id=external_id,
        defaults=defaults
    )
    
    return record, created


def upsert_global_yad2_listing(listing_data: Dict[str, Any], key_dict: Dict[str, Any], force: bool = False) -> Tuple[Any, bool]:
    """
    Upsert a global Yad2 listing.
    
    Args:
        listing_data: Listing data
        key_dict: Cadastral identifiers
        force: Whether to force refresh regardless of TTL
        
    Returns:
        Tuple of (listing_instance, created_flag)
    """
    from .models import Yad2ListingGlobal
    
    key_fp = compute_key_fingerprint(key_dict)
    external_id = build_external_id_for_yad2_listing(listing_data, key_dict)
    ttl_expires_at = compute_ttl_expiration('yad2', force)
    
    defaults = {
        'key_fp': key_fp,
        'key_json': key_dict,
        'title': listing_data.get('title'),
        'price': listing_data.get('price'),
        'address': listing_data.get('address'),
        'rooms': listing_data.get('rooms'),
        'area': listing_data.get('area'),
        'property_type': listing_data.get('property_type'),
        'url': listing_data.get('url'),
        'raw': listing_data,
        'ttl_expires_at': ttl_expires_at,
    }
    
    listing, created = Yad2ListingGlobal.objects.update_or_create(
        external_id=external_id,
        defaults=defaults
    )
    
    return listing, created


def create_asset_link(asset, global_instance, link_type: str) -> bool:
    """
    Create a link between an asset and a global source instance.
    
    Args:
        asset: Asset instance
        global_instance: Global source instance
        link_type: Type of link ('deal', 'mavat', 'rami', 'decisive', 'yad2')
        
    Returns:
        True if link was created, False if it already existed
    """
    from .models import (
        AssetToDeal, AssetToMavatPlan, AssetToRamiParcel, 
        AssetToDecisiveRecord, AssetToYad2Listing
    )
    
    link_classes = {
        'deal': AssetToDeal,
        'mavat': AssetToMavatPlan,
        'rami': AssetToRamiParcel,
        'decisive': AssetToDecisiveRecord,
        'yad2': AssetToYad2Listing,
    }
    
    link_class = link_classes.get(link_type)
    if not link_class:
        raise ValueError(f"Unknown link type: {link_type}")
    
    # Create the link (Django will handle unique constraint)
    try:
        if link_type == 'deal':
            link_class.objects.create(asset=asset, transaction=global_instance)
        elif link_type == 'mavat':
            link_class.objects.create(asset=asset, plan=global_instance)
        elif link_type == 'rami':
            link_class.objects.create(asset=asset, parcel=global_instance)
        elif link_type == 'decisive':
            link_class.objects.create(asset=asset, record=global_instance)
        elif link_type == 'yad2':
            link_class.objects.create(asset=asset, listing=global_instance)
        return True
    except Exception:
        # Link already exists
        return False
