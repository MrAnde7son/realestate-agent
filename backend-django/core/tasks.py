
import logging
from celery import shared_task, chain

logger = logging.getLogger(__name__)

@shared_task
def enrich_asset(asset_id):
    """Main task to enrich an asset with data from multiple sources."""
    try:
        # Create the enrichment chain
        enrichment_chain = chain(
            geocode_and_ids.s(asset_id),
            parallel_tasks.s(asset_id),
            finalize.s(asset_id)
        )
        
        # Execute the chain
        result = enrichment_chain.apply_async()
        logger.info(f"Enrichment chain started for asset {asset_id}: {result.id}")
        return result.id
        
    except Exception as e:
        logger.error(f"Failed to start enrichment chain for asset {asset_id}: {e}")
        # Update asset status to error
        _update_asset_status(asset_id, 'error', {'error': str(e)})
        raise

@shared_task
def geocode_and_ids(asset_id):
    """Geocode address and extract IDs (gush, helka, neighborhood_id)."""
    try:
        logger.info(f"Starting geocoding for asset {asset_id}")
        
        # Get asset from database
        asset = _get_asset(asset_id)
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        # Update status to enriching
        _update_asset_status(asset_id, 'enriching', {})
        
        # Try to geocode using GIS client
        try:
            from gis.gis_client import TelAvivGS
            
            gis_client = TelAvivGS()
            
            # Determine what to geocode based on scope type
            if asset.scope_type == 'address' and asset.street and asset.number:
                # Geocode by street and number
                lat, lon = gis_client.geocode_address(asset.street, asset.number)
                gush, helka = _extract_gush_helka_from_address(asset.street, asset.number)
                
            elif asset.scope_type == 'parcel' and asset.gush and asset.helka:
                # Use existing gush/helka, need to get lat/lon
                lat, lon = _get_lat_lon_from_gush_helka(asset.gush, asset.helka)
                gush, helka = asset.gush, asset.helka
                
            elif asset.scope_type == 'neighborhood' and asset.neighborhood:
                # Get center point of neighborhood
                lat, lon = _get_neighborhood_center(asset.neighborhood, asset.city)
                gush, helka = None, None
                
            else:
                # Fallback geocoding
                lat, lon = _fallback_geocoding(asset)
                gush, helka = None, None
            
            # Update asset with geocoded data
            _update_asset_location(asset_id, lat, lon, gush, helka)
            
            # Get neighborhood ID if available
            neighborhood_id = _get_neighborhood_id(lat, lon, asset.neighborhood)
            
            context = {
                'asset_id': asset_id,
                'lat': lat,
                'lon': lon,
                'gush': gush,
                'helka': helka,
                'neighborhood_id': neighborhood_id,
                'radius': asset.meta.get('radius', 150)
            }
            
            logger.info(f"Geocoding completed for asset {asset_id}: {context}")
            return context
            
        except ImportError:
            logger.warning("GIS client not available, using fallback geocoding")
            # Fallback geocoding
            lat, lon = _fallback_geocoding(asset)
            _update_asset_location(asset_id, lat, lon, None, None)
            
            context = {
                'asset_id': asset_id,
                'lat': lat,
                'lon': lon,
                'radius': asset.meta.get('radius', 150)
            }
            return context
            
    except Exception as e:
        logger.error(f"Geocoding failed for asset {asset_id}: {e}")
        _update_asset_status(asset_id, 'error', {'geocoding_error': str(e)})
        raise

@shared_task
def parallel_tasks(context):
    """Execute parallel data collection tasks."""
    try:
        asset_id = context['asset_id']
        logger.info(f"Starting parallel data collection for asset {asset_id}")
        
        # Execute parallel tasks
        yad2_task = pull_yad2.delay(context)
        nadlan_task = pull_nadlan.delay(context)
        gis_task = pull_gis.delay(context)
        rami_task = pull_rami.delay(context)
        
        # Wait for all tasks to complete
        results = [
            yad2_task.get(),
            nadlan_task.get(),
            gis_task.get(),
            rami_task.get()
        ]
        
        logger.info(f"Parallel data collection completed for asset {asset_id}")
        return {
            'asset_id': asset_id,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Parallel tasks failed for asset {context.get('asset_id')}: {e}")
        raise

@shared_task
def pull_yad2(context):
    """Pull Yad2 data around the asset location."""
    try:
        asset_id = context['asset_id']
        lat = context.get('lat')
        lon = context.get('lon')
        radius = context.get('radius', 150)
        
        logger.info(f"Pulling Yad2 data for asset {asset_id} at ({lat}, {lon}) with radius {radius}m")
        
        if not lat or not lon:
            logger.warning(f"Missing coordinates for asset {asset_id}, skipping Yad2")
            return {'source': 'yad2', 'count': 0, 'error': 'Missing coordinates'}
        
        try:
            from yad2.scrapers.yad2_scraper import Yad2Scraper
            from yad2.core.parameters import Yad2SearchParameters
            
            # Get asset from database to access city information
            asset = _get_asset(asset_id)
            if not asset:
                logger.warning(f"Asset {asset_id} not found, using default city")
                city = 'תל אביב'
            else:
                city = getattr(asset, 'city', 'תל אביב') or 'תל אביב'
            
            # Since Yad2 doesn't support coordinate-based search directly,
            # we'll search by city and property type instead
            search_params = Yad2SearchParameters(
                property='1',  # Apartment
                city=city,
                max_pages=3
            )
            
            scraper = Yad2Scraper(search_params)
            results = scraper.scrape_all_pages(max_pages=3, delay=1)
            
            # Save results to database
            saved_count = _save_yad2_records(asset_id, results)
            
            logger.info(f"Yad2 data collected for asset {asset_id}: {saved_count} records")
            return {'source': 'yad2', 'count': saved_count}
            
        except ImportError:
            logger.warning("Yad2 client not available")
            return {'source': 'yad2', 'count': 0, 'error': 'Client not available'}
            
    except Exception as e:
        logger.error(f"Yad2 data collection failed for asset {context.get('asset_id')}: {e}")
        return {'source': 'yad2', 'count': 0, 'error': str(e)}

@shared_task
def pull_nadlan(context):
    """Pull Nadlan transaction data for the asset."""
    try:
        asset_id = context['asset_id']
        neighborhood_id = context.get('neighborhood_id')
        gush = context.get('gush')
        helka = context.get('helka')
        
        logger.info(f"Pulling Nadlan data for asset {asset_id}")
        
        try:
            from gov.nadlan.scraper import NadlanDealsScraper
            
            scraper = NadlanDealsScraper()
            
            if neighborhood_id:
                # Use neighborhood ID if available
                deals = scraper.get_deals_by_neighborhood_id(neighborhood_id)
            elif gush and helka:
                # Use gush/helka if available
                deals = scraper.get_deals_by_gush_helka(gush, helka)
            else:
                logger.warning(f"No neighborhood_id or gush/helka for asset {asset_id}")
                return {'source': 'nadlan', 'count': 0, 'error': 'No location identifiers'}
            
            # Save deals to database
            saved_count = _save_nadlan_transactions(asset_id, deals)
            
            logger.info(f"Nadlan data collected for asset {asset_id}: {saved_count} transactions")
            return {'source': 'nadlan', 'count': saved_count}
            
        except ImportError:
            logger.warning("Nadlan scraper not available")
            return {'source': 'nadlan', 'count': 0, 'error': 'Scraper not available'}
            
    except Exception as e:
        logger.error(f"Nadlan data collection failed for asset {context.get('asset_id')}: {e}")
        return {'source': 'nadlan', 'count': 0, 'error': str(e)}

@shared_task
def pull_gis(context):
    """Pull GIS data (permits and rights) for the asset."""
    try:
        asset_id = context['asset_id']
        lat = context.get('lat')
        lon = context.get('lon')
        radius = context.get('radius', 150)
        
        logger.info(f"Pulling GIS data for asset {asset_id} at ({lat}, {lon}) with radius {radius}m")
        
        if not lat or not lon:
            logger.warning(f"Missing coordinates for asset {asset_id}, skipping GIS")
            return {'source': 'gis', 'count': 0, 'error': 'Missing coordinates'}
        
        try:
            from gis.gis_client import TelAvivGS
            
            gis_client = TelAvivGS()
            
            # Get building permits
            permits = gis_client.get_building_permits(lat, lon, radius)
            
            # Get building privilege page (contains rights information)
            rights = gis_client.get_building_privilege_page(lat, lon)
            
            # Save to database
            saved_permits = _save_gis_records(asset_id, 'gis_permit', permits)
            saved_rights = _save_gis_records(asset_id, 'gis_rights', [rights] if rights else [])
            
            total_count = saved_permits + saved_rights
            
            logger.info(f"GIS data collected for asset {asset_id}: {total_count} records")
            return {'source': 'gis', 'count': total_count, 'permits': saved_permits, 'rights': saved_rights}
            
        except ImportError:
            logger.warning("GIS client not available")
            return {'source': 'gis', 'count': 0, 'error': 'Client not available'}
            
    except Exception as e:
        logger.error(f"GIS data collection failed for asset {context.get('asset_id')}: {e}")
        return {'source': 'gis', 'count': 0, 'error': str(e)}

@shared_task
def pull_rami(context):
    """Pull RAMI plans and documents for the asset."""
    try:
        asset_id = context['asset_id']
        gush = context.get('gush')
        helka = context.get('helka')
        
        logger.info(f"Pulling RAMI data for asset {asset_id}")
        
        if not gush or not helka:
            logger.warning(f"No gush/helka for asset {asset_id}, skipping RAMI")
            return {'source': 'rami', 'count': 0, 'error': 'No gush/helka'}
        
        try:
            from rami.rami_client import RamiClient
            
            rami_client = RamiClient()
            
            # Get plans and documents
            plans = rami_client.get_plans_by_gush_helka(gush, helka)
            
            # Save to database
            saved_count = _save_rami_records(asset_id, plans)
            
            logger.info(f"RAMI data collected for asset {asset_id}: {saved_count} records")
            return {'source': 'rami', 'count': saved_count}
            
        except ImportError:
            logger.warning("RAMI client not available")
            return {'source': 'rami', 'count': 0, 'error': 'Client not available'}
            
    except Exception as e:
        logger.error(f"RAMI data collection failed for asset {context.get('asset_id')}: {e}")
        return {'source': 'rami', 'count': 0, 'error': str(e)}

@shared_task
def finalize(context):
    """Finalize the asset enrichment process."""
    try:
        asset_id = context['asset_id']
        logger.info(f"Finalizing enrichment for asset {asset_id}")
        
        # Update asset status to ready
        _update_asset_status(asset_id, 'ready', {
            'enrichment_completed_at': _get_current_timestamp(),
            'final_context': context
        })
        
        logger.info(f"Asset {asset_id} enrichment completed successfully")
        return {'asset_id': asset_id, 'status': 'ready'}
        
    except Exception as e:
        logger.error(f"Finalization failed for asset {context.get('asset_id')}: {e}")
        _update_asset_status(asset_id, 'error', {'finalization_error': str(e)})
        raise

# Helper functions
def _get_asset(asset_id):
    """Get asset from database."""
    try:
        from .models import Asset
        return Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        logger.error(f"Asset {asset_id} not found")
        return None
    except Exception as e:
        logger.error(f"Failed to get asset {asset_id}: {e}")
        return None

def _update_asset_status(asset_id, status, meta_update):
    """Update asset status and meta."""
    try:
        from .models import Asset
        asset = Asset.objects.get(id=asset_id)
        asset.status = status
        if meta_update:
            asset.meta.update(meta_update)
        asset.save()
    except Asset.DoesNotExist:
        logger.error(f"Asset {asset_id} not found for status update")
    except Exception as e:
        logger.error(f"Failed to update asset {asset_id} status: {e}")

def _update_asset_location(asset_id, lat, lon, gush, helka):
    """Update asset location data."""
    try:
        from .models import Asset
        asset = Asset.objects.get(id=asset_id)
        asset.lat = lat
        asset.lon = lon
        if gush:
            asset.gush = gush
        if helka:
            asset.helka = helka
        asset.save()
    except Asset.DoesNotExist:
        logger.error(f"Asset {asset_id} not found for location update")
    except Exception as e:
        logger.error(f"Failed to update asset {asset_id} location: {e}")

def _save_yad2_records(asset_id, results):
    """Save Yad2 records to database."""
    try:
        from .models import SourceRecord
        saved_count = 0
        for result in results:
            SourceRecord.objects.create(
                asset_id=asset_id,
                source='yad2',
                external_id=str(result.get('id', '')),
                title=result.get('title', ''),
                url=result.get('url', ''),
                raw=result
            )
            saved_count += 1
        return saved_count
    except Exception as e:
        logger.error(f"Failed to save Yad2 records for asset {asset_id}: {e}")
        return 0

def _save_nadlan_transactions(asset_id, deals):
    """Save Nadlan transactions to database."""
    try:
        from .models import RealEstateTransaction, SourceRecord
        saved_count = 0
        for deal in deals:
            # Save transaction
            RealEstateTransaction.objects.create(
                asset_id=asset_id,
                deal_id=deal.get('deal_id', ''),
                date=deal.get('date'),
                price=deal.get('price'),
                rooms=deal.get('rooms'),
                area=deal.get('area'),
                floor=deal.get('floor'),
                address=deal.get('address', ''),
                raw=deal
            )
            
            # Save source record
            SourceRecord.objects.create(
                asset_id=asset_id,
                source='nadlan',
                external_id=deal.get('deal_id', ''),
                title=f"Transaction {deal.get('deal_id', '')}",
                raw=deal
            )
            
            saved_count += 1
        return saved_count
    except Exception as e:
        logger.error(f"Failed to save Nadlan transactions for asset {asset_id}: {e}")
        return 0

def _save_gis_records(asset_id, source_type, records):
    """Save GIS records to database."""
    try:
        from .models import SourceRecord
        saved_count = 0
        for record in records:
            SourceRecord.objects.create(
                asset_id=asset_id,
                source=source_type,
                external_id=str(record.get('id', '')),
                title=record.get('title', ''),
                url=record.get('url', ''),
                file_path=record.get('file_path', ''),
                raw=record
            )
            saved_count += 1
        return saved_count
    except Exception as e:
        logger.error(f"Failed to save GIS records for asset {asset_id}: {e}")
        return 0

def _save_rami_records(asset_id, plans):
    """Save RAMI records to database."""
    try:
        from .models import SourceRecord
        saved_count = 0
        for plan in plans:
            SourceRecord.objects.create(
                asset_id=asset_id,
                source='rami_plan',
                external_id=str(plan.get('id', '')),
                title=plan.get('title', ''),
                url=plan.get('url', ''),
                file_path=plan.get('file_path', ''),
                raw=plan
            )
            saved_count += 1
        return saved_count
    except Exception as e:
        logger.error(f"Failed to save RAMI records for asset {asset_id}: {e}")
        return 0

def _get_current_timestamp():
    """Get current timestamp string."""
    from datetime import datetime
    return datetime.now().isoformat()

# Placeholder functions for geocoding fallbacks
def _extract_gush_helka_from_address(street, number):
    """Extract gush/helka from address (placeholder)."""
    # This would integrate with actual GIS data
    return None, None

def _get_lat_lon_from_gush_helka(gush, helka):
    """Get lat/lon from gush/helka (placeholder)."""
    # This would integrate with actual GIS data
    return 32.0853, 34.7818  # Default Tel Aviv coordinates

def _get_neighborhood_center(neighborhood, city):
    """Get neighborhood center coordinates (placeholder)."""
    # This would integrate with actual GIS data
    return 32.0853, 34.7818  # Default Tel Aviv coordinates

def _get_neighborhood_id(lat, lon, neighborhood_name):
    """Get neighborhood ID from coordinates (placeholder)."""
    # This would integrate with actual GIS data
    return None

def _fallback_geocoding(asset):
    """Fallback geocoding when GIS client is not available."""
    # Return default coordinates based on city
    if asset.city == 'תל אביב':
        return 32.0853, 34.7818
    elif asset.city == 'ירושלים':
        return 31.7683, 35.2137
    elif asset.city == 'חיפה':
        return 32.7940, 34.9896
    else:
        return 32.0853, 34.7818  # Default to Tel Aviv
