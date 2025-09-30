"""
Analytics tracking for CRM events.
This module provides functions to track various CRM-related events.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Placeholder for an analytics client
class AnalyticsClient:
    def track(self, event_name: str, user_id: int, properties: dict):
        # In a real application, this would send data to Segment/GA/Amplitude
        logger.info(f"Analytics Tracked: User {user_id}, Event: {event_name}, Props: {properties}")

analytics = AnalyticsClient()

# --- Contact Events ---
def track_contact_created(contact_obj, user_id: int):
    """Track when a contact is created."""
    properties = {
        "contact_id": contact_obj.id,
        "has_email": bool(contact_obj.email),
        "has_phone": bool(contact_obj.phone),
        "tags_count": len(contact_obj.tags),
        "contact_name": contact_obj.name,
    }
    analytics.track("contact_created", user_id, properties)

def track_contact_updated(contact_obj, user_id: int, changed_fields: List[str]):
    """Track when a contact is updated."""
    properties = {
        "contact_id": contact_obj.id,
        "changed_fields": changed_fields,
        "contact_name": contact_obj.name,
    }
    analytics.track("contact_updated", user_id, properties)

def track_contact_deleted(contact_obj, user_id: int, leads_count: int):
    """Track when a contact is deleted."""
    properties = {
        "contact_id": contact_obj.id,
        "leads_count_at_deletion": leads_count,
        "contact_name": contact_obj.name,
    }
    analytics.track("contact_deleted", user_id, properties)

# --- Lead Events ---
def track_lead_created(lead_obj, user_id: int):
    """Track when a lead is created."""
    properties = {
        "lead_id": lead_obj.id,
        "status": lead_obj.status,
        "asset_id": lead_obj.asset_id,
        "contact_id": lead_obj.contact_id,
        "contact_name": lead_obj.contact.name,
    }
    analytics.track("lead_created", user_id, properties)

def track_lead_updated(lead_obj, user_id: int, changed_fields: List[str]):
    """Track when a lead is updated."""
    properties = {
        "lead_id": lead_obj.id,
        "changed_fields": changed_fields,
        "status": lead_obj.status,
        "asset_id": lead_obj.asset_id,
        "contact_id": lead_obj.contact_id,
    }
    analytics.track("lead_updated", user_id, properties)

def track_lead_deleted(lead_obj, user_id: int):
    """Track when a lead is deleted."""
    properties = {
        "lead_id": lead_obj.id,
        "status": lead_obj.status,
        "asset_id": lead_obj.asset_id,
        "contact_id": lead_obj.contact_id,
    }
    analytics.track("lead_deleted", user_id, properties)

def track_lead_status_changed(lead_obj, user_id: int, from_status: str, to_status: str):
    """Track when a lead status is changed."""
    properties = {
        "lead_id": lead_obj.id,
        "from_status": from_status,
        "to_status": to_status,
        "asset_id": lead_obj.asset_id,
        "contact_id": lead_obj.contact_id,
    }
    analytics.track("lead_status_changed", user_id, properties)

def track_lead_note_added(lead_obj, user_id: int, note_text: str):
    """Track when a note is added to a lead."""
    properties = {
        "lead_id": lead_obj.id,
        "note_length": len(note_text),
        "status": lead_obj.status,
        "asset_id": lead_obj.asset_id,
        "contact_id": lead_obj.contact_id,
    }
    analytics.track("lead_note_added", user_id, properties)

def track_lead_report_sent(lead_obj, user_id: int, via: str):
    """Track when a report is sent to a lead."""
    properties = {
        "lead_id": lead_obj.id,
        "via": via,  # 'email' or 'link'
        "asset_id": lead_obj.asset_id,
        "contact_id": lead_obj.contact_id,
    }
    analytics.track("lead_report_sent", user_id, properties)

# --- Asset/CRM Integration Events ---
def track_asset_change_notified(asset_obj, user_id: int, leads_count: int, change_summary: str):
    """Track when asset changes are notified to leads."""
    properties = {
        "asset_id": asset_obj.id,
        "leads_notified_count": leads_count,
        "change_summary": change_summary,
    }
    analytics.track("asset_change_notified", user_id, properties)

# --- General CRM Events ---
def track_crm_search(user_id: int, search_type: str, query: str, results_count: int):
    """Track CRM search events."""
    properties = {
        "search_type": search_type,  # 'contacts' or 'leads'
        "search_query": query,
        "results_count": results_count,
    }
    analytics.track("crm_search", user_id, properties)

def track_crm_export(user_id: int, export_type: str, count: int):
    """Track CRM export events."""
    properties = {
        "export_type": export_type,  # 'contacts' or 'leads'
        "exported_count": count,
    }
    analytics.track("crm_export", user_id, properties)

def track_crm_dashboard_view(user_id: int, dashboard_name: str):
    """Track CRM dashboard view events."""
    properties = {
        "dashboard_name": dashboard_name,
    }
    analytics.track("crm_dashboard_view", user_id, properties)

def track_crm_contact_lead_association(user_id: int, contact_id: int, asset_id: int, lead_id: Optional[int] = None):
    """Track when a contact is associated with a lead."""
    properties = {
        "contact_id": contact_id,
        "asset_id": asset_id,
        "lead_id": lead_id,
    }
    analytics.track("crm_contact_lead_association", user_id, properties)

def track_crm_bulk_action(user_id: int, action_type: str, item_type: str, count: int):
    """Track bulk actions in CRM."""
    properties = {
        "action_type": action_type,  # e.g., 'delete', 'change_status'
        "item_type": item_type,  # 'contacts' or 'leads'
        "items_count": count,
    }
    analytics.track("crm_bulk_action", user_id, properties)

def track_crm_permission_denied(user_id: int, resource_type: str, resource_id: Optional[int] = None, action: str = "access"):
    """Track permission denied events."""
    properties = {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "action": action,
    }
    analytics.track("crm_permission_denied", user_id, properties)

def track_crm_error(user_id: int, error_message: str, context: Optional[dict] = None):
    """Track CRM error events."""
    properties = {
        "error_message": error_message,
        "context": context,
    }
    analytics.track("crm_error", user_id, properties)
