from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import re

logger = logging.getLogger(__name__)


try:  # pragma: no cover - best effort import
    backend_path = os.path.join(os.path.dirname(__file__), "..", "backend-django")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    import django  # type: ignore
    from django.conf import settings  # type: ignore

    if not settings.configured:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "broker_backend.settings")
        django.setup()

    from core.models import (  # type: ignore
        AlertRule,
        AssetDocument,
        AssetListing,
        AssetPermit,
        AssetPlan,
        AssetTransaction,
        Document,
        Listing as DjangoListing,
        Plan,
        Permit,
    )
except Exception as import_exc:  # pragma: no cover - best effort fallback
    logging.getLogger(__name__).warning("Failed to import Django models: %s", import_exc)

    class AlertRule:  # type: ignore
        objects = []

    AssetDocument = AssetListing = AssetPermit = AssetPlan = AssetTransaction = None  # type: ignore
    Document = DjangoListing = Plan = Permit = None  # type: ignore


def _convert_unix_timestamp_to_date(timestamp_ms: int) -> Optional[date]:
    """Convert Unix timestamp in milliseconds to a date object."""

    if not timestamp_ms or timestamp_ms <= 0:
        return None

    try:
        timestamp_seconds = timestamp_ms / 1000
        dt = datetime.fromtimestamp(timestamp_seconds)
        return dt.date()
    except (ValueError, OSError) as error:
        logger.warning("Failed to convert timestamp %s to date: %s", timestamp_ms, error)
        return None


def _collect_field_updates(instance: Any, updates: Dict[str, Any]) -> List[str]:
    """Apply field updates to a Django model instance without saving."""

    changed: List[str] = []
    for field, value in updates.items():
        if not hasattr(instance, field):
            continue
        current = getattr(instance, field)
        if current != value:
            setattr(instance, field, value)
            changed.append(field)
    return changed


def _ensure_document_link(document: Any, asset: Any) -> None:
    """Ensure the AssetDocument through link exists."""
    if not document or not asset or AssetDocument is None:
        return
    AssetDocument.objects.get_or_create(document=document, asset=asset)


def _ensure_plan_link(plan: Any, asset: Any) -> None:
    """Ensure the AssetPlan through link exists."""
    if not plan or not asset or AssetPlan is None:
        return
    AssetPlan.objects.get_or_create(plan=plan, asset=asset)


def _ensure_transaction_link(transaction: Any, asset: Any) -> None:
    """Ensure the AssetTransaction through link exists."""
    if not transaction or not asset or AssetTransaction is None:
        return
    AssetTransaction.objects.get_or_create(transaction=transaction, asset=asset)


def _ensure_listing_link(listing: Any, asset: Any) -> None:
    """Ensure the AssetListing through link exists."""
    if not listing or not asset or AssetListing is None:
        return
    AssetListing.objects.get_or_create(listing=listing, asset=asset)


def _ensure_permit_link(permit: Any, asset: Any) -> None:
    """Ensure the AssetPermit through link exists."""
    if not permit or not asset or AssetPermit is None:
        return
    AssetPermit.objects.get_or_create(permit=permit, asset=asset)


def _upsert_document(
    document_type: str,
    external_id: str,
    payload: Dict[str, Any],
    asset: Any = None,
    user: Any = None,
) -> Tuple[Optional[Any], bool]:
    """Fetch or create a Document by (document_type, external_id) and update fields."""
    if Document is None or not external_id:
        return None, False

    normalized_id = str(external_id)
    document = (
        Document.objects.filter(document_type=document_type, external_id=normalized_id)
        .order_by("id")
        .first()
    )
    created = False

    update_payload = dict(payload)

    if document is None:
        create_kwargs = dict(update_payload)
        if asset is not None:
            create_kwargs.setdefault("asset", asset)
        if user is not None:
            create_kwargs.setdefault("user", user)
        document = Document.objects.create(
            document_type=document_type,
            external_id=normalized_id,
            **create_kwargs,
        )
        created = True
    else:
        updates = _collect_field_updates(document, update_payload)
        extra_updates: List[str] = []
        if asset is not None and getattr(document, "asset_id", None) is None:
            document.asset = asset
            extra_updates.append("asset")
        if user is not None and getattr(document, "user_id", None) is None:
            document.user = user
            extra_updates.append("user")
        total_updates = list(dict.fromkeys(updates + extra_updates))
        if total_updates:
            document.save(update_fields=total_updates)

    if asset is not None and document is not None:
        _ensure_document_link(document, asset)

    return document, created


def _upsert_plan(
    plan_number: str,
    payload: Dict[str, Any],
    asset: Any = None,
) -> Tuple[Optional[Any], bool]:
    """Fetch or create a Plan by plan_number and update its fields."""
    if Plan is None or not plan_number:
        return None, False

    normalized_number = str(plan_number)
    plan_obj = (
        Plan.objects.filter(plan_number=normalized_number)
        .order_by("id")
        .first()
    )
    created = False
    update_payload = dict(payload)

    if plan_obj is None:
        create_kwargs = dict(update_payload)
        if asset is not None:
            create_kwargs.setdefault("asset", asset)
        plan_obj = Plan.objects.create(
            plan_number=normalized_number,
            **create_kwargs,
        )
        created = True
    else:
        updates = _collect_field_updates(plan_obj, update_payload)
        if asset is not None and getattr(plan_obj, "asset_id", None) is None:
            plan_obj.asset = asset
            updates.append("asset")
        if updates:
            plan_obj.save(update_fields=list(dict.fromkeys(updates)))

    if asset is not None and plan_obj is not None:
        _ensure_plan_link(plan_obj, asset)

    return plan_obj, created


def _parse_document_date(date_str):
    """Parse date strings for documents."""
    if not date_str:
        return None
    try:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y%m%d"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        if "T" in date_str:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
    except Exception:
        return None
    return None


def _extract_permit_date(value: Any) -> Optional[date]:
    """Best-effort extraction of a permit date field."""
    if value in (None, "", 0):
        return None
    if isinstance(value, (int, float)):
        return _convert_unix_timestamp_to_date(int(value))
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        parsed = _parse_document_date(value)
        if parsed:
            return parsed
        if value.startswith(("/Date", "Date")):
            try:
                millis = int("".join(ch for ch in value if ch.isdigit()))
                return _convert_unix_timestamp_to_date(millis)
            except Exception:
                pass
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except Exception:
            return None
    return None


def _upsert_permit(
    permit_number: str,
    payload: Dict[str, Any],
    asset: Any = None,
    raw: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[Any], bool]:
    """Fetch or create a Permit by permit_number and update its fields."""
    if Permit is None or not permit_number:
        return None, False

    normalized_number = str(permit_number)
    permit_obj = (
        Permit.objects.filter(permit_number=normalized_number)
        .order_by("id")
        .first()
    )
    created = False
    update_payload = dict(payload)

    if permit_obj is None:
        create_kwargs = dict(update_payload)
        if asset is not None:
            create_kwargs.setdefault("asset", asset)
        permit_obj = Permit.objects.create(
            permit_number=normalized_number,
            **create_kwargs,
        )
        created = True
    else:
        updates = _collect_field_updates(permit_obj, update_payload)
        if asset is not None and getattr(permit_obj, "asset_id", None) is None:
            permit_obj.asset = asset
            updates.append("asset")
        if updates:
            permit_obj.save(update_fields=list(dict.fromkeys(updates)))

    if raw and permit_obj:
        permit_date = raw.get("permission_date")
        extracted = _extract_permit_date(permit_date)
        if extracted:
            try:
                permit_obj.permission_date = extracted
                permit_obj.save(update_fields=["permission_date"])
            except Exception:
                logger.debug("Failed to persist permit permission_date for %s", permit_number)

    if asset is not None and permit_obj is not None:
        _ensure_permit_link(permit_obj, asset)

    return permit_obj, created


def _normalize_identifier(value: Any) -> str:
    """Normalize identifiers by stripping non-alphanumeric characters."""
    return re.sub(r"[^0-9A-Za-z]+", "_", str(value)).strip("_")


__all__ = [
    "AssetDocument",
    "AssetListing",
    "AssetPermit",
    "AssetPlan",
    "AssetTransaction",
    "Document",
    "DjangoListing",
    "Plan",
    "Permit",
    "AlertRule",
    "_convert_unix_timestamp_to_date",
    "_collect_field_updates",
    "_ensure_document_link",
    "_ensure_plan_link",
    "_ensure_transaction_link",
    "_ensure_listing_link",
    "_ensure_permit_link",
    "_upsert_document",
    "_upsert_plan",
    "_extract_permit_date",
    "_upsert_permit",
    "_parse_document_date",
    "_normalize_identifier",
]
