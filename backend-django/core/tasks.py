import logging
import os
import pickle
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from contextlib import nullcontext

from celery import chain, shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
import psutil

from .analytics import track
from .email import send_email

if TYPE_CHECKING:  # pragma: no cover - imports are optional at runtime
    from orchestration.location import LocationQuery

logger = logging.getLogger(__name__)

_PIPELINE_STATE_DIR = Path(settings.BASE_DIR) / "tmp" / "pipeline_state"
_PIPELINE_STATE_DIR.mkdir(parents=True, exist_ok=True)


def log_worker_memory(prefix: str) -> None:
    """Log the current worker RSS in megabytes for observability."""

    try:
        process = psutil.Process(os.getpid())
        rss_mb = process.memory_info().rss / (1024**2)
        logger.info("Worker memory [%s]: %.1f MB RSS", prefix, rss_mb)
    except Exception:  # pragma: no cover - best-effort logging
        logger.debug("Unable to log worker memory for prefix '%s'", prefix)


def _state_path(asset_id: int) -> Path:
    return _PIPELINE_STATE_DIR / f"asset_{asset_id}.pkl"


def _save_state(asset_id: int, state: Dict[str, Any]) -> None:
    path = _state_path(asset_id)
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("wb") as fh:
        pickle.dump(state, fh)
    os.replace(tmp_path, path)


def _load_state(asset_id: int) -> Dict[str, Any]:
    path = _state_path(asset_id)
    if not path.exists():
        raise FileNotFoundError(f"Pipeline state missing for asset {asset_id}")
    with path.open("rb") as fh:
        return pickle.load(fh)


def _clear_state(asset_id: int) -> None:
    path = _state_path(asset_id)
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _mark_asset_failed(asset_id: int, error_message: str) -> None:
    from .models import Asset

    truncated = (error_message or "")[:512]
    Asset.objects.filter(id=asset_id).update(
        status="failed",
        last_enrich_error=truncated,
    )
    track("asset_sync_fail", asset_id=asset_id, error_code=truncated)


def _serialize_location(location: "LocationQuery") -> Dict[str, Any]:
    return {
        "city": location.city,
        "street": location.street,
        "house_number": location.house_number,
        "block": location.block,
        "parcel": location.parcel,
        "subparcel": location.subparcel,
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification_email(
    self,
    subject: str,
    to: List[str],
    text: str = "",
    html: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
):
    """Send an email asynchronously with retry support."""

    try:
        return send_email(subject, to, text=text, html=html, **(extra or {}))
    except Exception as exc:
        logger.exception("Resend delivery failed, retrying: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True)
def collect_asset_data(self, asset_id: int) -> Dict[str, Any]:
    """Collect raw payloads for an asset without further processing."""
    from .models import Asset
    from orchestration.data_pipeline import DataPipeline
    from orchestration.location import LocationQuery
    from orchestration.pipeline.listings import _object_to_payload

    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        logger.error("Asset %s not found", asset_id)
        return {"asset_id": asset_id, "halt": True}

    _clear_state(asset_id)

    log_worker_memory(f"collect_asset_data:start asset={asset_id}")

    asset.status = "enriching"
    asset.last_enrich_error = None
    asset.save(update_fields=["status", "last_enrich_error"])

    pipeline = DataPipeline()
    location = LocationQuery(
        city=asset.city,
        street=asset.street,
        house_number=asset.number,
        block=asset.block,
        parcel=asset.parcel,
        subparcel=asset.subparcel,
    )

    collect_summary: Dict[str, Any] = {}
    listings_payload: List[Dict[str, Any]] = []
    michrazim_listings_payload: List[Dict[str, Any]] = []

    try:
        # Use shared collection logic from DataPipeline
        collected = pipeline._collect_all_data(location, asset_id=asset_id)

        # Extract collected data
        location = collected["location"]
        govmap_data = collected["govmap_data"]
        gis_data = collected["gis_data"]
        handasa_archive = collected["handasa_archive"]
        tikbinyan_archive = collected["tikbinyan_archive"]
        gov_data = collected["gov_data"]
        plans = collected["plans"]
        mavat_plans = collected["mavat_plans"]
        listings = collected["listings"]
        madlan_listings = collected["madlan_listings"]
        michrazim_listings = collected["michrazim_listings"]
        x_itm = collected["x_itm"]
        y_itm = collected["y_itm"]
        lon_wgs84 = collected["lon_wgs84"]
        lat_wgs84 = collected["lat_wgs84"]
        block = collected["block"]
        parcel = collected["parcel"]
        subparcel = collected["subparcel"]

        # Build collect summary
        collect_summary["govmap"] = bool(govmap_data)
        collect_summary["gis"] = bool(gis_data)
        collect_summary["handasa"] = len(handasa_archive)
        collect_summary["tikbinyan"] = len(tikbinyan_archive)
        collect_summary["gov"] = bool(
            gov_data.get("decisive") or gov_data.get("transactions")
        )
        collect_summary["gov_rami"] = len(plans)
        collect_summary["mavat"] = len(mavat_plans)

        # Convert listings to payloads
        listings_payload = [_object_to_payload(item) for item in listings or []]
        collect_summary["yad2"] = len(listings_payload)

        michrazim_listings_payload = [
            _object_to_payload(item) for item in michrazim_listings or []
        ]
        collect_summary["michrazim"] = len(michrazim_listings_payload)

        # Always merge michrazim tenders into the listings payload
        listings_payload.extend(michrazim_listings_payload)

        madlan_listings_payload = [
            _object_to_payload(item) for item in madlan_listings or []
        ]
        collect_summary["madlan"] = len(madlan_listings_payload)
        # Combine with yad2 listings
        listings_payload.extend(madlan_listings_payload)

        state: Dict[str, Any] = {
            "asset_id": asset_id,
            "location": _serialize_location(location),
            "block": block,
            "parcel": parcel,
            "subparcel": subparcel,
            "govmap_data": govmap_data,
            "gis_data": gis_data,
            "gov_data": gov_data,
            "plans": plans,
            "mavat_plans": mavat_plans,
            "handasa_archive": handasa_archive,
            "tikbinyan_archive": tikbinyan_archive,
            "listings_raw": listings_payload,
            "x_itm": x_itm,
            "y_itm": y_itm,
            "lon_wgs84": lon_wgs84,
            "lat_wgs84": lat_wgs84,
        }
        _save_state(asset_id, state)

        log_worker_memory(f"collect_asset_data:finish asset={asset_id}")

        return {
            "asset_id": asset_id,
            "listing_count": len(listings_payload),
            "collect_summary": collect_summary,
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("Collection stage failed for asset %s", asset_id)
        _mark_asset_failed(asset_id, str(exc))
        _clear_state(asset_id)
        raise


@shared_task
def normalize_asset_data(previous: Dict[str, Any]) -> Dict[str, Any]:
    from orchestration.pipeline.listings import _normalize_listings

    if previous.get("halt"):
        return previous

    asset_id = previous["asset_id"]

    log_worker_memory(f"normalize_asset_data:start asset={asset_id}")

    try:
        state = _load_state(asset_id)
    except FileNotFoundError:
        previous["halt"] = True
        return previous

    normalized = _normalize_listings(state.get("listings_raw", []))
    state["listings_normalized"] = normalized
    _save_state(asset_id, state)

    previous["normalized_listings"] = len(normalized)

    log_worker_memory(f"normalize_asset_data:finish asset={asset_id}")
    return previous


def _append_result(results: List[Dict[str, Any]], source: str, data: Any) -> None:
    if data:
        results.append({"source": source, "data": data})


@shared_task
def persist_asset_data(previous: Dict[str, Any]) -> Dict[str, Any]:
    from orchestration.data_pipeline import DataPipeline
    from orchestration.pipeline import update_asset_with_collected_data

    if previous.get("halt"):
        return previous

    asset_id = previous["asset_id"]

    log_worker_memory(f"persist_asset_data:start asset={asset_id}")

    try:
        state = _load_state(asset_id)
    except FileNotFoundError:
        previous["halt"] = True
        return previous

    pipeline = DataPipeline()
    if pipeline.session is not None:
        session_factory = lambda: nullcontext(pipeline.session)
        manage_per_listing = False
    elif pipeline.db is not None:
        session_factory = pipeline.db.session_scope
        manage_per_listing = True
    else:
        raise RuntimeError("Data pipeline database session unavailable")

    govmap_data = state.get("govmap_data", {})
    gis_data = state.get("gis_data", {})
    gov_data = state.get("gov_data", {"decisive": [], "transactions": []})
    plans = state.get("plans", [])
    mavat_plans = state.get("mavat_plans", [])
    handasa_archive = state.get("handasa_archive", [])
    listings_raw = state.get("listings_raw", [])
    listings_normalized = state.get("listings_normalized", [])

    results: List[Dict[str, Any]] = []
    persisted = 0

    def _persist_listing(session, payload: Dict[str, Any]) -> None:
        listing_obj = SimpleNamespace(**payload)
        db_listing = pipeline._store_listing(session, listing_obj)

        autocomplete = govmap_data.get("api_data", {}).get("autocomplete")
        if autocomplete:
            pipeline._add_source_record(
                session, db_listing.id, "govmap_autocomplete", autocomplete
            )

        parcel_api = govmap_data.get("api_data", {}).get("parcel")
        if parcel_api:
            pipeline._add_source_record(
                session, db_listing.id, "govmap_parcel", parcel_api
            )

        if gis_data:
            pipeline._add_source_record(session, db_listing.id, "gis", gis_data)

        decisive = gov_data.get("decisive")
        if decisive:
            pipeline._add_source_record(
                session, db_listing.id, "gov_decisive", decisive
            )

        transactions = gov_data.get("transactions")
        if transactions:
            pipeline._add_source_record(
                session, db_listing.id, "gov_transactions", transactions
            )
            pipeline._add_transactions(session, db_listing.id, transactions)

        if plans:
            pipeline._add_source_record(session, db_listing.id, "gov_rami", plans)

        if mavat_plans:
            pipeline._add_source_record(session, db_listing.id, "mavat", mavat_plans)

        if handasa_archive:
            pipeline._add_source_record(
                session, db_listing.id, "handasa", handasa_archive
            )

        session.flush()

    try:
        if manage_per_listing:
            for payload in listings_raw:
                with session_factory() as session:
                    _persist_listing(session, payload)
                    persisted += 1
        else:
            with session_factory() as session:
                for payload in listings_raw:
                    _persist_listing(session, payload)
                    session.commit()
                    session.expunge_all()
                    persisted += 1
    except Exception as exc:  # noqa: BLE001
        if not manage_per_listing and pipeline.session is not None:
            try:
                pipeline.session.rollback()
            except Exception:  # pragma: no cover - best effort cleanup
                logger.debug("Failed to rollback shared pipeline session")
        logger.exception("Persistence stage failed for asset %s", asset_id)
        _mark_asset_failed(asset_id, str(exc))
        _clear_state(asset_id)
        raise

    log_worker_memory(f"persist_asset_data:after_persist asset={asset_id}")

    try:
        update_asset_with_collected_data(
            asset_id,
            state.get("block", ""),
            state.get("parcel", ""),
            govmap_data.get("api_data", {}).get("autocomplete", {}),
            govmap_data,
            gis_data,
            gov_data,
            plans,
            mavat_plans,
            handasa_archive,
            listings_normalized,
            state.get("x_itm"),
            state.get("y_itm"),
            state.get("lon_wgs84"),
            state.get("lat_wgs84"),
            subparcel=str(state.get("subparcel")) if state.get("subparcel") else None,
            tikbinyan_archive=state.get("tikbinyan_archive"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Asset update failed for asset %s", asset_id)
        _mark_asset_failed(asset_id, str(exc))
        _clear_state(asset_id)
        raise

    for normalized_listing in listings_normalized:
        _append_result(results, "listing", normalized_listing)
    _append_result(results, "govmap", govmap_data)
    _append_result(results, "gis", gis_data)
    _append_result(results, "gov_decisive", gov_data.get("decisive"))
    _append_result(results, "gov_transactions", gov_data.get("transactions"))
    _append_result(results, "gov_rami", plans)
    _append_result(results, "mavat", mavat_plans)
    _append_result(results, "handasa", handasa_archive)

    state["results"] = results
    _save_state(asset_id, state)

    previous["persisted_listings"] = persisted
    previous["result_sources"] = len(results)

    log_worker_memory(f"persist_asset_data:finish asset={asset_id}")
    return previous


@shared_task
def link_asset_data(previous: Dict[str, Any]) -> Dict[str, Any]:
    from orchestration.pipeline import (
        auto_expand_related_assets,
        create_asset_snapshot,
    )

    if previous.get("halt"):
        return previous

    asset_id = previous["asset_id"]

    log_worker_memory(f"link_asset_data:start asset={asset_id}")

    try:
        state = _load_state(asset_id)
    except FileNotFoundError:
        previous["halt"] = True
        return previous

    try:
        results = state.get("results", [])
        if results:
            create_asset_snapshot(asset_id, results)

        auto_created_assets = auto_expand_related_assets(
            asset_id,
            listings=state.get("listings_normalized"),
            govmap_data=state.get("govmap_data"),
            gis_data=state.get("gis_data"),
            gov_data=state.get("gov_data"),
            plans=state.get("plans"),
            mavat_plans=state.get("mavat_plans"),
            handasa_archive=state.get("handasa_archive"),
            tikbinyan_archive=state.get("tikbinyan_archive"),
        )

        from .models import Asset

        Asset.objects.filter(id=asset_id).update(
            status="done",
            last_enriched_at=timezone.now(),
            last_enrich_error=None,
        )

        track("asset_sync", asset_id=asset_id)

        try:
            evaluate_alerts_for_asset.delay(asset_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to enqueue alert evaluation for asset %s: %s", asset_id, exc
            )

        previous["linked_assets"] = len(auto_created_assets or [])
    except Exception as exc:  # noqa: BLE001
        logger.exception("Link stage failed for asset %s", asset_id)
        _mark_asset_failed(asset_id, str(exc))
        _clear_state(asset_id)
        raise
    finally:
        _clear_state(asset_id)

    log_worker_memory(f"link_asset_data:finish asset={asset_id}")
    return previous


@shared_task(bind=True)
def run_data_pipeline(self, asset_id: int):
    workflow = chain(
        collect_asset_data.s(asset_id=asset_id),
        normalize_asset_data.s(),
        persist_asset_data.s(),
        link_asset_data.s(),
    )
    raise self.replace(workflow)


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
    window = AnalyticsDaily.objects.filter(date__lt=today).order_by("-date")[:7]
    if not window:
        return False
    avg = sum(d.errors for d in window) / len(window)
    if errors_today > 2 * avg and errors_today > 0:
        track("error_spike", meta={"today": errors_today, "avg": avg})
        return True
    return False


@shared_task
def evaluate_alerts_for_asset(asset_id: int) -> int:
    """Evaluate alert rules for a specific asset after enrichment.

    Args:
        asset_id: ID of the asset to evaluate alerts for

    Returns:
        Number of alert events created
    """
    from .models import Asset, Snapshot

    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        logger.error("Asset %s not found for alert evaluation", asset_id)
        return 0

    # Get the latest snapshot
    latest_snapshot = (
        Snapshot.objects.filter(asset=asset).order_by("-created_at").first()
    )
    if not latest_snapshot:
        logger.warning("No snapshot found for asset %s", asset_id)
        return 0

    # Get previous snapshot for comparison
    previous_snapshot = (
        Snapshot.objects.filter(asset=asset).order_by("-created_at")[1:2].first()
    )

    # Get all active alert rules for this asset's owner
    user = asset.user if hasattr(asset, "user") else None
    if not user:
        logger.warning("No user found for asset %s", asset_id)
        return 0

    # Get both global and asset-specific rules
    from django.db import models
    from .models import AlertRule

    rules = AlertRule.objects.filter(user=user, active=True).filter(
        models.Q(scope="global") | models.Q(scope="asset", asset=asset)
    )

    events_created = 0

    for rule in rules:
        try:
            # Evaluate rule based on trigger type
            event_created = _evaluate_rule(
                rule, asset, latest_snapshot, previous_snapshot
            )
            if event_created:
                events_created += 1
        except Exception as e:
            logger.error(
                "Error evaluating rule %s for asset %s: %s", rule.id, asset_id, e
            )

    logger.info("Created %d alert events for asset %s", events_created, asset_id)
    return events_created


def _evaluate_rule(rule, asset, latest_snapshot, previous_snapshot) -> bool:
    """Evaluate a single alert rule and create event if triggered."""
    import hashlib
    from django.utils import timezone
    from .models import AlertEvent

    trigger_type = rule.trigger_type
    params = rule.params or {}

    # Create payload hash for deduplication
    date_bucket = timezone.now().date().isoformat()
    signature_fields = f"{rule.id}|{asset.id}|{trigger_type}|{date_bucket}"
    payload_hash = hashlib.sha256(signature_fields.encode()).hexdigest()

    # Check if event already exists
    if AlertEvent.objects.filter(payload_hash=payload_hash).exists():
        return False

    event_created = False

    if trigger_type == "PRICE_DROP":
        event_created = _evaluate_price_drop(
            rule, asset, latest_snapshot, previous_snapshot, payload_hash
        )
    elif trigger_type == "NEW_LISTING":
        event_created = _evaluate_new_listing(
            rule, asset, latest_snapshot, previous_snapshot, payload_hash
        )
    elif trigger_type == "MARKET_TREND":
        event_created = _evaluate_market_trend(
            rule, asset, latest_snapshot, previous_snapshot, payload_hash
        )
    elif trigger_type == "DOCS_UPDATE":
        event_created = _evaluate_docs_update(
            rule, asset, latest_snapshot, previous_snapshot, payload_hash
        )
    elif trigger_type == "PERMIT_STATUS":
        event_created = _evaluate_permit_status(
            rule, asset, latest_snapshot, previous_snapshot, payload_hash
        )
    elif trigger_type == "NEW_GOV_TX":
        event_created = _evaluate_new_gov_tx(
            rule, asset, latest_snapshot, previous_snapshot, payload_hash
        )
    elif trigger_type == "LISTING_REMOVED":
        event_created = _evaluate_listing_removed(
            rule, asset, latest_snapshot, previous_snapshot, payload_hash
        )

    return event_created


def _evaluate_price_drop(
    rule, asset, latest_snapshot, previous_snapshot, payload_hash: str
) -> bool:
    """Evaluate price drop alert."""
    from .models import AlertEvent

    if not previous_snapshot:
        return False

    price_old = previous_snapshot.payload.get("price")
    price_new = latest_snapshot.payload.get("price")

    if not price_old or not price_new:
        return False

    drop_pct = (price_old - price_new) / price_old * 100
    threshold = rule.params.get("pct", 3)

    if drop_pct >= threshold:
        payload = {
            "price_old": price_old,
            "price_new": price_new,
            "drop_pct": round(drop_pct, 2),
            "threshold": threshold,
        }

        event = AlertEvent.objects.create(
            alert_rule=rule, asset=asset, payload=payload, payload_hash=payload_hash
        )

        # Send immediate notification if configured
        if rule.frequency == "immediate":
            _send_immediate_notification(rule, event)

        return True

    return False


def _evaluate_new_listing(
    rule, asset, latest_snapshot, previous_snapshot, payload_hash: str
) -> bool:
    """Evaluate new listing alert."""
    from .models import AlertEvent

    # This would need to be implemented based on your listing detection logic
    # For now, we'll create a simple implementation
    if not previous_snapshot and latest_snapshot:
        payload = {
            "listing_id": latest_snapshot.payload.get("listing_id"),
            "address": asset.normalized_address
            or f"{asset.street} {asset.number}, {asset.city}",
            "price": latest_snapshot.payload.get("price"),
            "rooms": latest_snapshot.payload.get("rooms"),
            "area": latest_snapshot.payload.get("area"),
        }

        event = AlertEvent.objects.create(
            alert_rule=rule, asset=asset, payload=payload, payload_hash=payload_hash
        )

        if rule.frequency == "immediate":
            _send_immediate_notification(rule, event)

        return True

    return False


def _evaluate_market_trend(
    rule, asset, latest_snapshot, previous_snapshot, payload_hash: str
) -> bool:
    """Evaluate market trend alert."""
    from .models import AlertEvent, Snapshot
    from django.utils import timezone
    from datetime import timedelta
    import statistics

    if not previous_snapshot:
        return False

    # Get recent snapshots for trend analysis
    window_days = rule.params.get("window_days", 30)
    since = timezone.now() - timedelta(days=window_days)

    recent_snapshots = Snapshot.objects.filter(
        asset=asset, created_at__gte=since, ppsqm__isnull=False
    ).order_by("created_at")

    if len(recent_snapshots) < 2:
        return False

    ppsqm_values = [s.ppsqm for s in recent_snapshots if s.ppsqm]
    if len(ppsqm_values) < 2:
        return False

    old_median = statistics.median(ppsqm_values[: len(ppsqm_values) // 2])
    new_median = statistics.median(ppsqm_values[len(ppsqm_values) // 2 :])

    delta_pct = abs(new_median - old_median) / old_median * 100
    threshold = rule.params.get("delta_pct", 5)

    if delta_pct >= threshold:
        payload = {
            "ppsqm_old": old_median,
            "ppsqm_new": new_median,
            "delta_pct": round(delta_pct, 2),
            "threshold": threshold,
            "window_days": window_days,
        }

        event = AlertEvent.objects.create(
            alert_rule=rule, asset=asset, payload=payload, payload_hash=payload_hash
        )

        if rule.frequency == "immediate":
            _send_immediate_notification(rule, event)

        return True

    return False


def _evaluate_docs_update(
    rule, asset, latest_snapshot, previous_snapshot, payload_hash: str
) -> bool:
    """Evaluate document update alert."""
    from .models import AlertEvent

    if not previous_snapshot:
        return False

    # Compare document lists
    old_docs = previous_snapshot.payload.get("documents", [])
    new_docs = latest_snapshot.payload.get("documents", [])

    old_doc_ids = {doc.get("id") for doc in old_docs if doc.get("id")}
    new_doc_ids = {doc.get("id") for doc in new_docs if doc.get("id")}

    # Find new or updated documents
    new_docs_list = [doc for doc in new_docs if doc.get("id") not in old_doc_ids]
    updated_docs_list = []

    for new_doc in new_docs:
        doc_id = new_doc.get("id")
        if doc_id in old_doc_ids:
            old_doc = next((doc for doc in old_docs if doc.get("id") == doc_id), None)
            if old_doc and new_doc.get("updated_at") != old_doc.get("updated_at"):
                updated_docs_list.append(new_doc)

    if new_docs_list or updated_docs_list:
        payload = {
            "new_documents": new_docs_list,
            "updated_documents": updated_docs_list,
            "total_new": len(new_docs_list),
            "total_updated": len(updated_docs_list),
        }

        event = AlertEvent.objects.create(
            alert_rule=rule, asset=asset, payload=payload, payload_hash=payload_hash
        )

        if rule.frequency == "immediate":
            _send_immediate_notification(rule, event)

        return True

    return False


def _evaluate_permit_status(
    rule, asset, latest_snapshot, previous_snapshot, payload_hash: str
) -> bool:
    """Evaluate permit status change alert."""
    from .models import AlertEvent

    if not previous_snapshot:
        return False

    old_status = previous_snapshot.payload.get("permit_status")
    new_status = latest_snapshot.payload.get("permit_status")

    if old_status != new_status and new_status:
        payload = {
            "status_old": old_status,
            "status_new": new_status,
            "permit_name": latest_snapshot.payload.get("permit_name", "היתר בנייה"),
            "permit_url": latest_snapshot.payload.get("permit_url"),
        }

        event = AlertEvent.objects.create(
            alert_rule=rule, asset=asset, payload=payload, payload_hash=payload_hash
        )

        if rule.frequency == "immediate":
            _send_immediate_notification(rule, event)

        return True

    return False


def _evaluate_new_gov_tx(
    rule, asset, latest_snapshot, previous_snapshot, payload_hash: str
) -> bool:
    """Evaluate new government transaction alert."""
    from .models import AlertEvent

    if not previous_snapshot:
        return False

    old_txs = previous_snapshot.payload.get("gov_transactions", [])
    new_txs = latest_snapshot.payload.get("gov_transactions", [])

    old_tx_ids = {tx.get("id") for tx in old_txs if tx.get("id")}
    new_txs_list = [tx for tx in new_txs if tx.get("id") not in old_tx_ids]

    if new_txs_list:
        payload = {
            "new_transactions": new_txs_list,
            "count": len(new_txs_list),
            "radius_m": rule.params.get("radius_m", 500),
        }

        event = AlertEvent.objects.create(
            alert_rule=rule, asset=asset, payload=payload, payload_hash=payload_hash
        )

        if rule.frequency == "immediate":
            _send_immediate_notification(rule, event)

        return True

    return False


def _evaluate_listing_removed(
    rule, asset, latest_snapshot, previous_snapshot, payload_hash: str
) -> bool:
    """Evaluate listing removed alert."""
    from .models import AlertEvent

    if not previous_snapshot:
        return False

    # This would need to be implemented based on your listing tracking logic
    # For now, we'll create a simple implementation
    if previous_snapshot.payload.get("listing_id") and not latest_snapshot.payload.get(
        "listing_id"
    ):
        payload = {
            "listing_id": previous_snapshot.payload.get("listing_id"),
            "address": asset.normalized_address
            or f"{asset.street} {asset.number}, {asset.city}",
            "misses": rule.params.get("misses", 2),
        }

        event = AlertEvent.objects.create(
            alert_rule=rule, asset=asset, payload=payload, payload_hash=payload_hash
        )

        if rule.frequency == "immediate":
            _send_immediate_notification(rule, event)

        return True

    return False


def _send_immediate_notification(rule, event):
    """Send immediate notification for an alert event."""
    from orchestration.alerts import create_notifier_for_alert_rule
    from django.utils import timezone

    notifier = create_notifier_for_alert_rule(rule)

    if not notifier:
        logger.warning("No notifier created for rule %s", rule.id)
        return

    # Create message based on trigger type
    message = _create_alert_message(rule, event)

    try:
        for alert in notifier.alerts:
            alert.send(message)

        # Mark as delivered
        event.delivered_at = timezone.now()
        event.save(update_fields=["delivered_at"])

        logger.info(
            "Sent immediate notification for rule %s, event %s", rule.id, event.id
        )
    except Exception as e:
        logger.error(
            "Failed to send immediate notification for rule %s: %s", rule.id, e
        )


def _create_alert_message(rule, event) -> str:
    """Create alert message based on rule type and event payload."""
    payload = event.payload
    asset = event.asset

    if rule.trigger_type == "PRICE_DROP":
        return f"""נדלנר: ירידת מחיר בנכס שלך
{asset.normalized_address or f"{asset.street} {asset.number}, {asset.city}"}
מחיר: {payload["price_old"]:,} → {payload["price_new"]:,} ({payload["drop_pct"]}%↓)
צפה בנכס: /api/assets/{asset.id}"""

    elif rule.trigger_type == "NEW_LISTING":
        return f"""נדלנר: נכס חדש באזור ששמרת
{payload.get("address", "")} • {payload.get("rooms", "")} חדרים • {payload.get("area", "")} מ"ר • {payload.get("price", ""):,}₪
פתח: /api/assets/{asset.id}"""

    elif rule.trigger_type == "MARKET_TREND":
        return f"""נדלנר: שינוי מגמה באזור {asset.neighborhood or asset.city}
מחיר ממוצע למ"ר: {payload["ppsqm_old"]:,} → {payload["ppsqm_new"]:,} ({payload["delta_pct"]}%)
פרטים: /api/assets/{asset.id}"""

    elif rule.trigger_type == "DOCS_UPDATE":
        return f"""נדלנר: עדכון מסמכים לנכס {asset.normalized_address or f"{asset.street} {asset.number}, {asset.city}"}
{payload.get("total_new", 0)} מסמכים חדשים, {payload.get("total_updated", 0)} עודכנו
פתח מסמך: /assets/{asset.id}"""

    elif rule.trigger_type == "PERMIT_STATUS":
        return f"""נדלנר: סטטוס היתרים עודכן
{payload.get("permit_name", "היתר בנייה")}: {payload.get("status_old", "")} → {payload.get("status_new", "")}
לצפייה: /api/assets/{asset.id}"""

    else:
        return f"""נדלנר: התראה חדשה
{asset.normalized_address or f"{asset.street} {asset.number}, {asset.city}"}
פרטים: /api/assets/{asset.id}"""


@shared_task
def alerts_daily_digest():
    """Send daily digest of undelivered alert events."""
    from django.utils import timezone
    from datetime import timedelta
    from .models import AlertEvent
    from orchestration.alerts import create_notifier_for_alert_rule
    import uuid

    # Get undelivered events from last 24 hours
    since = timezone.now() - timedelta(hours=24)
    events = (
        AlertEvent.objects.filter(
            occurred_at__gte=since,
            delivered_at__isnull=True,
            alert_rule__frequency="daily",
        )
        .select_related("alert_rule", "asset")
        .order_by("alert_rule__user", "occurred_at")
    )

    # Group by user
    user_events = {}
    for event in events:
        user_id = event.alert_rule.user_id
        if user_id not in user_events:
            user_events[user_id] = []
        user_events[user_id].append(event)

    digest_id = str(uuid.uuid4())

    for user_id, user_event_list in user_events.items():
        try:
            # Get user and create notifier
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.get(id=user_id)

            # Get the first alert rule for this user to create notifier
            first_rule = user_event_list[0].alert_rule
            notifier = create_notifier_for_alert_rule(first_rule)
            if not notifier:
                continue

            # Group events by asset
            asset_events = {}
            for event in user_event_list:
                asset_id = event.asset_id
                if asset_id not in asset_events:
                    asset_events[asset_id] = []
                asset_events[asset_id].append(event)

            # Create digest message
            message_lines = ["נדלנר: סיכום יומי של התראות"]
            total_events = len(user_event_list)

            for asset_id, asset_event_list in list(asset_events.items())[
                :10
            ]:  # Max 10 assets
                asset = asset_event_list[0].asset
                message_lines.append(
                    f"\n{asset.normalized_address or f'{asset.street} {asset.number}, {asset.city}'}:"
                )

                for event in asset_event_list[:3]:  # Max 3 events per asset
                    if event.alert_rule.trigger_type == "PRICE_DROP":
                        payload = event.payload
                        message_lines.append(
                            f"  • ירידת מחיר: {payload.get('price_old', 0):,} → {payload.get('price_new', 0):,} ({payload.get('drop_pct', 0)}%)"
                        )
                    elif event.alert_rule.trigger_type == "NEW_LISTING":
                        payload = event.payload
                        message_lines.append(
                            f"  • נכס חדש: {payload.get('rooms', '')} חדרים, {payload.get('price', 0):,}₪"
                        )
                    elif event.alert_rule.trigger_type == "DOCS_UPDATE":
                        payload = event.payload
                        message_lines.append(
                            f"  • עדכון מסמכים: {payload.get('total_new', 0)} חדשים, {payload.get('total_updated', 0)} עודכנו"
                        )
                    else:
                        message_lines.append(
                            f"  • {event.alert_rule.get_trigger_type_display()}"
                        )

                if len(asset_event_list) > 3:
                    message_lines.append(
                        f"  • + עוד {len(asset_event_list) - 3} התראות"
                    )

            if len(asset_events) > 10:
                message_lines.append(f"\n+ עוד {len(asset_events) - 10} נכסים")

            message_lines.append(f'\nסה"כ: {total_events} התראות')
            message_lines.append(f"לצפייה: /alerts")

            message = "\n".join(message_lines)

            # Send digest
            for alert in notifier.alerts:
                alert.send(message)

            # Mark events as delivered
            for event in user_event_list:
                event.delivered_at = timezone.now()
                event.digest_id = digest_id
                event.save(update_fields=["delivered_at", "digest_id"])

            logger.info(
                "Sent daily digest for user %s with %d events", user_id, total_events
            )

        except Exception as e:
            logger.error("Failed to send daily digest for user %s: %s", user_id, e)
