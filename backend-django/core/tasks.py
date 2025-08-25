import logging
from celery import shared_task

from orchestration.data_pipeline import DataPipeline

logger = logging.getLogger(__name__)


@shared_task
def run_data_pipeline(asset_id: int, max_pages: int = 1):
    """Run the high-level data pipeline for a newly added asset.

    Looks up the asset's address information and feeds it into
    :class:`orchestration.data_pipeline.DataPipeline`. The pipeline
    persists all collected records to the SQLAlchemy database and
    returns the created ``Listing`` IDs.
    """
    try:
        from .models import Asset

        asset = Asset.objects.get(id=asset_id)
    except Exception:
        logger.error("Asset %s not found", asset_id)
        return []

    pipeline = DataPipeline()
    address = asset.street or asset.city or ""
    house_number = asset.number or 0
    return pipeline.run(address, house_number, max_pages=max_pages)

