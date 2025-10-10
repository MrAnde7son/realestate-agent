# -*- coding: utf-8 -*-
"""
Deal caching module for Nadlan scraper.

This module provides caching functionality to avoid re-fetching the same deals
and enables incremental updates for better performance.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path

from .models import Deal

logger = logging.getLogger(__name__)


class DealCache:
    """Cache for storing and retrieving deal data with incremental updates."""
    
    def __init__(self, cache_dir: str = "deal_cache", max_age_hours: int = 24):
        """Initialize the deal cache.
        
        Args:
            cache_dir: Directory to store cache files
            max_age_hours: Maximum age of cached data before refresh (in hours)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_age_hours = max_age_hours
        
    def _get_cache_file(self, address: str) -> Path:
        """Get cache file path for an address."""
        # Create a safe filename from the address
        safe_address = "".join(c for c in address if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_address = safe_address.replace(' ', '_')
        return self.cache_dir / f"{safe_address}.json"
    
    def _get_metadata_file(self, address: str) -> Path:
        """Get metadata file path for an address."""
        safe_address = "".join(c for c in address if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_address = safe_address.replace(' ', '_')
        return self.cache_dir / f"{safe_address}_meta.json"
    
    def get_cached_deals(self, address: str) -> Optional[List[Deal]]:
        """Get cached deals for an address if they exist and are fresh.
        
        Args:
            address: Address to get cached deals for
            
        Returns:
            List of cached deals or None if not cached, expired, or from error state
        """
        cache_file = self._get_cache_file(address)
        metadata_file = self._get_metadata_file(address)
        
        if not cache_file.exists() or not metadata_file.exists():
            return None
            
        try:
            # Check if cache is still fresh
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            last_update = datetime.fromisoformat(metadata['last_update'])
            if datetime.now() - last_update > timedelta(hours=self.max_age_hours):
                logger.info(f"Cache for {address} is expired (age: {datetime.now() - last_update})")
                return None
            
            # Check if cached results were from an error modal encounter
            error_modal_encountered = metadata.get('error_modal_encountered', False)
            if error_modal_encountered:
                logger.info(f"Not using cached deals for {address} due to previous error modal encounter")
                return None
                
            # Load cached deals
            with open(cache_file, 'r', encoding='utf-8') as f:
                deals_data = json.load(f)
                
            deals = [Deal.from_item(deal_dict) for deal_dict in deals_data]
            logger.info(f"Loaded {len(deals)} cached deals for {address}")
            return deals
            
        except Exception as e:
            logger.warning(f"Error loading cached deals for {address}: {e}")
            return None
    
    def store_deals(self, address: str, deals: List[Deal], error_modal_encountered: bool = False) -> None:
        """Store deals in cache.
        
        Args:
            address: Address the deals belong to
            deals: List of deals to cache
            error_modal_encountered: Whether an error modal was encountered during scraping
        """
        cache_file = self._get_cache_file(address)
        metadata_file = self._get_metadata_file(address)
        
        try:
            # Store deals data
            deals_data = [deal.to_dict() for deal in deals]
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(deals_data, f, ensure_ascii=False, indent=2)
                
            # Store metadata
            metadata = {
                'last_update': datetime.now().isoformat(),
                'deal_count': len(deals),
                'address': address,
                'error_modal_encountered': error_modal_encountered
            }
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Cached {len(deals)} deals for {address}")
            
        except Exception as e:
            logger.error(f"Error storing deals in cache for {address}: {e}")
    
    def get_last_update_time(self, address: str) -> Optional[datetime]:
        """Get the last update time for cached deals.
        
        Args:
            address: Address to check
            
        Returns:
            Last update time or None if not cached
        """
        metadata_file = self._get_metadata_file(address)
        
        if not metadata_file.exists():
            return None
            
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            return datetime.fromisoformat(metadata['last_update'])
        except Exception as e:
            logger.warning(f"Error reading metadata for {address}: {e}")
            return None
    
    def clear_cache(self, address: Optional[str] = None) -> None:
        """Clear cache for a specific address or all addresses.
        
        Args:
            address: Address to clear cache for, or None to clear all
        """
        if address:
            cache_file = self._get_cache_file(address)
            metadata_file = self._get_metadata_file(address)
            
            for file_path in [cache_file, metadata_file]:
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Cleared cache for {address}")
        else:
            # Clear all cache files
            for file_path in self.cache_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            logger.info("Cleared all cached deals")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        metadata_files = list(self.cache_dir.glob("*_meta.json"))
        
        total_deals = 0
        addresses = []
        
        for metadata_file in metadata_files:
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                total_deals += metadata.get('deal_count', 0)
                addresses.append(metadata.get('address', 'unknown'))
            except Exception:
                continue
                
        return {
            'total_addresses': len(addresses),
            'total_deals': total_deals,
            'cache_files': len(cache_files),
            'addresses': addresses
        }


class IncrementalDealCollector:
    """Collector that uses caching for incremental deal updates."""
    
    def __init__(self, scraper, cache: Optional[DealCache] = None):
        """Initialize the incremental collector.
        
        Args:
            scraper: NadlanDealsScraper instance
            cache: DealCache instance (optional)
        """
        self.scraper = scraper
        self.cache = cache or DealCache()
        
    def get_deals_incremental(self, address: str, force_refresh: bool = False, max_age_days: Optional[int] = None) -> List[Deal]:
        """Get deals with incremental updates using cache.
        
        Args:
            address: Address to get deals for
            force_refresh: Force refresh even if cache is fresh
            max_age_days: Override date filtering for this request
            
        Returns:
            List of deals (cached + any new ones)
        """
        # Check cache first
        if not force_refresh:
            cached_deals = self.cache.get_cached_deals(address)
            if cached_deals is not None:
                logger.info(f"Using cached deals for {address}")
                # Apply date filtering to cached deals if specified
                if max_age_days is not None:
                    original_max_age = self.scraper.max_age_days
                    self.scraper.max_age_days = max_age_days
                    cached_deals = self.scraper._filter_deals_by_age(cached_deals)
                    self.scraper.max_age_days = original_max_age
                return cached_deals
        
        # Fetch fresh deals
        logger.info(f"Fetching fresh deals for {address}")
        # Use force_refresh=True to bypass caching and prevent recursion
        fresh_deals = self.scraper.get_deals_by_address(address, max_age_days=max_age_days, force_refresh=True)
        
        # Check if error modal was encountered during scraping
        error_modal_encountered = getattr(self.scraper, 'error_modal_encountered', False)
        
        # Cache results if we have them, or if we encountered an error modal (to prevent re-fetching)
        # Mark error modal encounters in metadata to prevent using cached error results
        should_cache = len(fresh_deals) > 0 or error_modal_encountered
        
        if should_cache:
            # Store in cache (store ALL deals, not just filtered ones)
            # We need to fetch without date filtering to store complete data
            if max_age_days is not None:
                original_max_age = self.scraper.max_age_days
                self.scraper.max_age_days = 0  # Disable date filtering for caching
                # Use force_refresh=True to bypass caching and prevent recursion
                all_deals = self.scraper.get_deals_by_address(address, force_refresh=True)
                self.scraper.max_age_days = original_max_age
                self.cache.store_deals(address, all_deals, error_modal_encountered)
            else:
                self.cache.store_deals(address, fresh_deals, error_modal_encountered)
        else:
            logger.warning(f"Not caching empty results for {address}")
        
        return fresh_deals
    
    def get_new_deals_since(self, address: str, since_date: datetime) -> List[Deal]:
        """Get only new deals since a specific date.
        
        Args:
            address: Address to get deals for
            since_date: Only return deals after this date
            
        Returns:
            List of new deals
        """
        all_deals = self.get_deals_incremental(address)
        
        # Filter deals by date
        new_deals = []
        for deal in all_deals:
            if deal.deal_date:
                try:
                    # Parse deal date (simplified - you might want to use the scraper's date parsing)
                    deal_date = datetime.strptime(deal.deal_date, "%d/%m/%Y")
                    if deal_date > since_date:
                        new_deals.append(deal)
                except ValueError:
                    # If we can't parse the date, include the deal to be safe
                    new_deals.append(deal)
        
        logger.info(f"Found {len(new_deals)} new deals since {since_date} for {address}")
        return new_deals
