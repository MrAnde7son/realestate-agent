"""Comprehensive analytics tracking utilities for the CRM app."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Sequence, Union

from django.conf import settings

logger = logging.getLogger(__name__)


class AnalyticsClient:
    """Placeholder analytics client that logs events."""

    def track(self, event_name: str, user_id: Optional[int], properties: Dict[str, Any]) -> None:
        """Log analytics events.

        Args:
            event_name: Name of the analytics event.
            user_id: Optional ID of the user that triggered the event.
            properties: Event metadata.
        """
        logger.info(
            "Analytics Event",
            extra={
                "event_name": event_name,
                "user_id": user_id,
                "properties": properties,
            },
        )


analytics = AnalyticsClient()


def track_event(event_name: str, properties: Dict[str, Any], user_id: Optional[int] = None) -> None:
    """Track an analytics event with optional external forwarding.

    This helper enriches events with timestamps, logs them and optionally forwards
    the payload to a configured external analytics provider.
    """
    try:
        payload = dict(properties)
        payload.setdefault("timestamp", datetime.utcnow().isoformat())
        if user_id is not None:
            payload.setdefault("user_id", user_id)

        analytics.track(event_name, user_id, payload)

        if getattr(settings, "ANALYTICS_SERVICE", None):
            send_to_analytics_service(event_name, payload)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to track analytics event %s: %s", event_name, exc)


def send_to_analytics_service(event_name: str, properties: Dict[str, Any]) -> None:
    """Send the event to an external analytics service if configured."""
    try:
        analytics_service = getattr(settings, "ANALYTICS_SERVICE", None)

        if analytics_service == "google_analytics":
            send_to_google_analytics(event_name, properties)
        elif analytics_service == "mixpanel":
            send_to_mixpanel(event_name, properties)
        elif analytics_service == "amplitude":
            send_to_amplitude(event_name, properties)
        elif analytics_service == "segment":
            send_to_segment(event_name, properties)
        else:
            logger.info("Analytics Event: %s", event_name, extra=properties)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to forward analytics event %s: %s", event_name, exc)


def send_to_google_analytics(event_name: str, properties: Dict[str, Any]) -> None:
    """Placeholder Google Analytics integration."""
    logger.info("Google Analytics Event: %s", event_name, extra=properties)


def send_to_mixpanel(event_name: str, properties: Dict[str, Any]) -> None:
    """Placeholder Mixpanel integration."""
    logger.info("Mixpanel Event: %s", event_name, extra=properties)


def send_to_amplitude(event_name: str, properties: Dict[str, Any]) -> None:
    """Placeholder Amplitude integration."""
    logger.info("Amplitude Event: %s", event_name, extra=properties)


def send_to_segment(event_name: str, properties: Dict[str, Any]) -> None:
    """Placeholder Segment integration."""
    logger.info("Segment Event: %s", event_name, extra=properties)


def _safe_len(items: Optional[Sequence[Any]]) -> int:
    return len(items) if items else 0


def _truncate(text: Optional[str], length: int) -> str:
    if not text:
        return ""
    return text[:length]


def _asset_address(asset: Any) -> str:
    if not asset:
        return ""
    for attr in ("normalized_address", "address"):
        value = getattr(asset, attr, None)
        if value:
            return value
    street = getattr(asset, "street", None)
    number = getattr(asset, "number", None)
    city = getattr(asset, "city", None)
    parts = [
        part
        for part in (
            street,
            str(number) if number is not None else None,
            city,
        )
        if part
    ]
    return ", ".join(parts)


def track_contact_created(contact, user_id: int) -> None:
    properties = {
        "contact_id": contact.id,
        "has_email": bool(contact.email),
        "has_phone": bool(contact.phone),
        "tags_count": _safe_len(contact.tags),
        "contact_name": contact.name,
        "contact_email": contact.email or "",
        "contact_phone": contact.phone or "",
    }
    track_event("contact_created", properties, user_id)


def track_contact_updated(contact, user_id: int, changed_fields: Sequence[str]) -> None:
    properties = {
        "contact_id": contact.id,
        "fields_changed": list(changed_fields),
        "has_email": bool(contact.email),
        "has_phone": bool(contact.phone),
        "tags_count": _safe_len(contact.tags),
        "contact_name": contact.name,
        "contact_email": contact.email or "",
        "contact_phone": contact.phone or "",
    }
    track_event("contact_updated", properties, user_id)


def track_contact_deleted(contact, user_id: int, leads_count: int) -> None:
    properties = {
        "contact_id": contact.id,
        "leads_count": leads_count,
        "contact_name": contact.name,
        "contact_email": contact.email or "",
        "contact_phone": contact.phone or "",
    }
    track_event("contact_deleted", properties, user_id)


def track_lead_created(lead, user_id: int) -> None:
    asset = getattr(lead, "asset", None)
    contact = getattr(lead, "contact", None)
    properties = {
        "lead_id": lead.id,
        "status": getattr(lead, "status", ""),
        "asset_id": getattr(asset, "id", None),
        "contact_id": getattr(contact, "id", None),
        "contact_name": getattr(contact, "name", ""),
        "asset_address": _asset_address(asset),
        "notes_count": _safe_len(getattr(lead, "notes", None)),
    }
    track_event("lead_created", properties, user_id)


def track_lead_updated(lead, user_id: int, changed_fields: Sequence[str]) -> None:
    asset = getattr(lead, "asset", None)
    contact = getattr(lead, "contact", None)
    properties = {
        "lead_id": lead.id,
        "fields_changed": list(changed_fields),
        "status": getattr(lead, "status", ""),
        "asset_id": getattr(asset, "id", None),
        "contact_id": getattr(contact, "id", None),
        "contact_name": getattr(contact, "name", ""),
        "asset_address": _asset_address(asset),
        "notes_count": _safe_len(getattr(lead, "notes", None)),
    }
    track_event("lead_updated", properties, user_id)


def track_lead_deleted(lead, user_id: int) -> None:
    asset = getattr(lead, "asset", None)
    contact = getattr(lead, "contact", None)
    properties = {
        "lead_id": lead.id,
        "status": getattr(lead, "status", ""),
        "asset_id": getattr(asset, "id", None),
        "contact_id": getattr(contact, "id", None),
        "contact_name": getattr(contact, "name", ""),
        "asset_address": _asset_address(asset),
        "notes_count": _safe_len(getattr(lead, "notes", None)),
    }
    track_event("lead_deleted", properties, user_id)


def track_lead_status_changed(lead, user_id: int, from_status: str, to_status: str) -> None:
    asset = getattr(lead, "asset", None)
    contact = getattr(lead, "contact", None)
    properties = {
        "lead_id": lead.id,
        "from_status": from_status,
        "to_status": to_status,
        "asset_id": getattr(asset, "id", None),
        "contact_id": getattr(contact, "id", None),
        "contact_name": getattr(contact, "name", ""),
        "asset_address": _asset_address(asset),
    }
    track_event("lead_status_changed", properties, user_id)


def track_lead_note_added(lead, user_id: int, note_text: str) -> None:
    asset = getattr(lead, "asset", None)
    contact = getattr(lead, "contact", None)
    properties = {
        "lead_id": lead.id,
        "note_length": len(note_text or ""),
        "note_text": _truncate(note_text, 100),
        "status": getattr(lead, "status", ""),
        "asset_id": getattr(asset, "id", None),
        "contact_id": getattr(contact, "id", None),
        "contact_name": getattr(contact, "name", ""),
    }
    track_event("lead_note_added", properties, user_id)


def track_lead_report_sent(lead, user_id: int, via: str) -> None:
    asset = getattr(lead, "asset", None)
    contact = getattr(lead, "contact", None)
    properties = {
        "lead_id": lead.id,
        "via": via,
        "status": getattr(lead, "status", ""),
        "asset_id": getattr(asset, "id", None),
        "contact_id": getattr(contact, "id", None),
        "contact_name": getattr(contact, "name", ""),
        "contact_email": getattr(contact, "email", ""),
        "asset_address": _asset_address(asset),
    }
    track_event("lead_report_sent", properties, user_id)


def track_asset_change_notified(asset, user_id: int, leads_count: int, change_summary: str) -> None:
    properties = {
        "asset_id": getattr(asset, "id", None),
        "leads_count": leads_count,
        "change_summary": _truncate(change_summary, 200),
        "asset_address": _asset_address(asset),
        "asset_price": getattr(asset, "price", None),
        "asset_area": getattr(asset, "area", None),
        "asset_rooms": getattr(asset, "rooms", None),
    }
    track_event("asset_change_notified", properties, user_id)


def track_crm_search(user_id: int, search_type: str, search_query: str, results_count: int) -> None:
    properties = {
        "search_type": search_type,
        "search_query": _truncate(search_query, 100),
        "results_count": results_count,
        "query_length": len(search_query or ""),
    }
    track_event("crm_search", properties, user_id)


def track_crm_export(user_id: int, export_type: str, records_count: int) -> None:
    properties = {
        "export_type": export_type,
        "records_count": records_count,
    }
    track_event("crm_export", properties, user_id)


def track_crm_dashboard_view(user_id: int, dashboard_type: str) -> None:
    properties = {
        "dashboard_type": dashboard_type,
        "view_timestamp": datetime.utcnow().isoformat(),
    }
    track_event("crm_dashboard_view", properties, user_id)


def track_crm_contact_lead_association(
    user_id: int,
    contact: Union[int, Any],
    asset: Union[int, Any, None],
    lead: Optional[Union[int, Any]] = None,
) -> None:
    contact_id = getattr(contact, "id", contact)
    contact_name = getattr(contact, "name", "")

    lead_obj = lead if hasattr(lead, "id") else None
    lead_id = getattr(lead_obj, "id", lead if isinstance(lead, int) else None)
    lead_status = getattr(lead_obj, "status", None)

    asset_obj = asset if hasattr(asset, "id") else getattr(lead_obj, "asset", None)
    asset_id = getattr(asset_obj, "id", asset if isinstance(asset, int) else None)

    properties = {
        "contact_id": contact_id,
        "lead_id": lead_id,
        "contact_name": contact_name,
        "asset_id": asset_id,
        "asset_address": _asset_address(asset_obj),
        "lead_status": lead_status,
    }
    track_event("crm_contact_lead_association", properties, user_id)


def track_crm_bulk_action(
    user_id: int,
    action_type: str,
    records_count: int,
    success_count: Optional[int] = None,
    *,
    item_type: Optional[str] = None,
) -> None:
    success = records_count if success_count is None else success_count
    properties = {
        "action_type": action_type,
        "item_type": item_type,
        "records_count": records_count,
        "success_count": success,
        "failure_count": max(records_count - success, 0),
    }
    track_event("crm_bulk_action", properties, user_id)


def track_crm_permission_denied(
    user_id: int,
    resource_type: str,
    resource_id: Optional[int],
    action: str,
) -> None:
    properties = {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "action": action,
        "denied_timestamp": datetime.utcnow().isoformat(),
    }
    track_event("crm_permission_denied", properties, user_id)


def track_crm_error(
    user_id: int,
    error_type: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    properties = {
        "error_type": error_type,
        "error_message": _truncate(error_message, 200),
        "context": context or {},
        "error_timestamp": datetime.utcnow().isoformat(),
    }
    track_event("crm_error", properties, user_id)


def get_analytics_summary(user_id: int, days: int = 30) -> Dict[str, Any]:
    """Return a placeholder analytics summary for the given user."""
    return {
        "total_contacts": 0,
        "total_leads": 0,
        "contacts_created_today": 0,
        "leads_created_today": 0,
        "leads_by_status": {},
        "top_contacts": [],
        "recent_activity": [],
        "conversion_rate": 0.0,
        "average_lead_lifetime": 0,
        "most_active_assets": [],
        "days": days,
    }


def export_analytics_data(user_id: int, start_date: datetime, end_date: datetime) -> str:
    """Return a JSON payload describing analytics activity for the user."""
    data = {
        "user_id": user_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "events": [],
        "summary": get_analytics_summary(user_id, (end_date - start_date).days),
    }
    return json.dumps(data, indent=2)
