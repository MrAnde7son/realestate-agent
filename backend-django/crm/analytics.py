"""CRM analytics tracking utilities.

DISABLED: Using Vercel Analytics and Google Analytics instead.
This module provides no-op stubs to maintain compatibility with existing code.
"""

from typing import Any, Dict, Optional, Sequence, Union
from datetime import datetime


class AnalyticsClient:
    """No-op analytics client."""

    def track(
        self, event_name: str, user_id: Optional[int], properties: Dict[str, Any]
    ) -> None:
        """No-op - analytics disabled."""
        pass


analytics = AnalyticsClient()


def track_event(
    event_name: str, properties: Dict[str, Any], user_id: Optional[int] = None
) -> None:
    """No-op - analytics disabled."""
    pass


def send_to_analytics_service(event_name: str, properties: Dict[str, Any]) -> None:
    """No-op - analytics disabled."""
    pass


def send_to_google_analytics(event_name: str, properties: Dict[str, Any]) -> None:
    """No-op - analytics disabled."""
    pass


def send_to_mixpanel(event_name: str, properties: Dict[str, Any]) -> None:
    """No-op - analytics disabled."""
    pass


def send_to_amplitude(event_name: str, properties: Dict[str, Any]) -> None:
    """No-op - analytics disabled."""
    pass


def send_to_segment(event_name: str, properties: Dict[str, Any]) -> None:
    """No-op - analytics disabled."""
    pass


def track_contact_created(contact, user_id: int) -> None:
    """No-op - analytics disabled."""
    pass


def track_contact_updated(contact, user_id: int, changed_fields: Sequence[str]) -> None:
    """No-op - analytics disabled."""
    pass


def track_contact_deleted(contact, user_id: int, leads_count: int) -> None:
    """No-op - analytics disabled."""
    pass


def track_lead_created(lead, user_id: int) -> None:
    """No-op - analytics disabled."""
    pass


def track_lead_updated(lead, user_id: int, changed_fields: Sequence[str]) -> None:
    """No-op - analytics disabled."""
    pass


def track_lead_deleted(lead, user_id: int) -> None:
    """No-op - analytics disabled."""
    pass


def track_lead_status_changed(
    lead, user_id: int, from_status: str, to_status: str
) -> None:
    """No-op - analytics disabled."""
    pass


def track_lead_note_added(lead, user_id: int, note_text: str) -> None:
    """No-op - analytics disabled."""
    pass


def track_lead_report_sent(lead, user_id: int, via: str) -> None:
    """No-op - analytics disabled."""
    pass


def track_asset_change_notified(
    asset, user_id: int, leads_count: int, change_summary: str
) -> None:
    """No-op - analytics disabled."""
    pass


def track_crm_search(
    user_id: int, search_type: str, search_query: str, results_count: int
) -> None:
    """No-op - analytics disabled."""
    pass


def track_crm_export(user_id: int, export_type: str, records_count: int) -> None:
    """No-op - analytics disabled."""
    pass


def track_crm_dashboard_view(user_id: int, dashboard_type: str) -> None:
    """No-op - analytics disabled."""
    pass


def track_crm_contact_lead_association(
    user_id: int,
    contact: Union[int, Any],
    asset: Union[int, Any, None],
    lead: Optional[Union[int, Any]] = None,
) -> None:
    """No-op - analytics disabled."""
    pass


def track_crm_bulk_action(
    user_id: int,
    action_type: str,
    records_count: int,
    success_count: Optional[int] = None,
    *,
    item_type: Optional[str] = None,
) -> None:
    """No-op - analytics disabled."""
    pass


def track_crm_permission_denied(
    user_id: int,
    resource_type: str,
    resource_id: Optional[int],
    action: str,
) -> None:
    """No-op - analytics disabled."""
    pass


def track_crm_error(
    user_id: int,
    error_type: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """No-op - analytics disabled."""
    pass


def get_analytics_summary(user_id: int, days: int = 30) -> Dict[str, Any]:
    """No-op - analytics disabled."""
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


def export_analytics_data(
    user_id: int, start_date: datetime, end_date: datetime
) -> str:
    """No-op - analytics disabled."""
    import json

    return json.dumps(
        {
            "user_id": user_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "events": [],
            "summary": get_analytics_summary(user_id, (end_date - start_date).days),
        },
        indent=2,
    )
