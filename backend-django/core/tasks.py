import logging

from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from .analytics import track

logger = logging.getLogger(__name__)


@shared_task
def run_data_pipeline(asset_id: int, max_pages: int = 1):
    """Run the high-level data pipeline for a newly added asset.

    Looks up the asset's address information and feeds it into
    :class:`orchestration.data_pipeline.DataPipeline`. The pipeline
    persists all collected records to the SQLAlchemy database and
    returns the created ``Listing`` IDs.
    """
    # Lazy import to avoid import errors during Django startup
    try:
        from orchestration.data_pipeline import DataPipeline
    except ImportError as e:
        logger.error("Failed to import orchestration module: %s", e)
        logger.error("Make sure the orchestration module is available in the Python path")
        raise ImportError("Orchestration module is required but not available") from e
    
    try:
        from .models import Asset

        asset = Asset.objects.get(id=asset_id)
    except Exception:
        logger.error("Asset %s not found", asset_id)
        return []

    pipeline = DataPipeline()
    address = asset.street or asset.city or ""
    house_number = asset.number or 0
    logger.info("Starting data pipeline for asset %s", asset_id)
    try:
        result = pipeline.run(address, house_number, max_pages=max_pages)
        track('asset_sync', asset_id=asset_id)
        logger.info(
            "Data pipeline completed for asset %s with %s listings",
            asset_id,
            len(result) if hasattr(result, '__len__') else result,
        )
        return result
    except Exception as e:
        track('asset_sync_fail', asset_id=asset_id, error_code=str(e))
        logger.exception("Data pipeline failed for asset %s", asset_id)
        raise


@shared_task
def cleanup_demo_data():
    """Delete demo users and assets older than 24 hours."""
    from .models import Asset

    cutoff = timezone.now() - timedelta(hours=24)
    User = get_user_model()
    User.objects.filter(is_demo=True, created_at__lt=cutoff).delete()
    Asset.objects.filter(is_demo=True, created_at__lt=cutoff).delete()


@shared_task
def rollup_analytics():
    """Aggregate raw analytics events into daily rollups."""
    from django.utils import timezone
    from .analytics import rollup_day

    today = timezone.now().date()
    rollup_day(today)


@shared_task
def alert_on_spikes():
    """Send an alert if today's errors exceed twice the 7-day average."""
    from django.utils import timezone
    from .models import AnalyticsDaily

    today = timezone.now().date()
    daily = AnalyticsDaily.objects.filter(date=today).first()
    if not daily:
        return False
    errors_today = daily.errors
    window = AnalyticsDaily.objects.filter(date__lt=today).order_by('-date')[:7]
    if not window:
        return False
    avg = sum(d.errors for d in window) / len(window)
    if errors_today > 2 * avg and errors_today > 0:
        track('error_spike', meta={'today': errors_today, 'avg': avg})
        return True
    return False

