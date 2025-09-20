"""
Analytics and event tracking for CRM
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


def track_event(event_name: str, properties: Dict[str, Any], user_id: Optional[int] = None) -> None:
    """
    Track an analytics event
    
    Args:
        event_name: Name of the event (e.g., 'contact_created', 'lead_status_changed')
        properties: Event properties dictionary
        user_id: ID of the user who triggered the event
    """
    try:
        # Add timestamp
        properties['timestamp'] = datetime.utcnow().isoformat()
        
        # Add user_id if provided
        if user_id:
            properties['user_id'] = user_id
        
        # Log the event
        logger.info(f"Analytics Event: {event_name}", extra={
            'event_name': event_name,
            'properties': properties,
            'user_id': user_id
        })
        
        # Send to external analytics service if configured
        if hasattr(settings, 'ANALYTICS_SERVICE') and settings.ANALYTICS_SERVICE:
            send_to_analytics_service(event_name, properties)
            
    except Exception as e:
        logger.error(f"Failed to track event {event_name}: {e}")


def send_to_analytics_service(event_name: str, properties: Dict[str, Any]) -> None:
    """
    Send event to external analytics service
    
    Args:
        event_name: Name of the event
        properties: Event properties dictionary
    """
    try:
        # This is a placeholder for external analytics service integration
        # You can integrate with services like:
        # - Google Analytics
        # - Mixpanel
        # - Amplitude
        # - Segment
        # - Custom analytics service
        
        analytics_service = getattr(settings, 'ANALYTICS_SERVICE', None)
        
        if analytics_service == 'google_analytics':
            send_to_google_analytics(event_name, properties)
        elif analytics_service == 'mixpanel':
            send_to_mixpanel(event_name, properties)
        elif analytics_service == 'amplitude':
            send_to_amplitude(event_name, properties)
        elif analytics_service == 'segment':
            send_to_segment(event_name, properties)
        else:
            # Default: just log
            logger.info(f"Analytics Event: {event_name}", extra=properties)
            
    except Exception as e:
        logger.error(f"Failed to send event to analytics service: {e}")


def send_to_google_analytics(event_name: str, properties: Dict[str, Any]) -> None:
    """Send event to Google Analytics"""
    # Placeholder for Google Analytics integration
    # You would use the Google Analytics Measurement Protocol or gtag
    logger.info(f"Google Analytics Event: {event_name}", extra=properties)


def send_to_mixpanel(event_name: str, properties: Dict[str, Any]) -> None:
    """Send event to Mixpanel"""
    # Placeholder for Mixpanel integration
    # You would use the Mixpanel Python library
    logger.info(f"Mixpanel Event: {event_name}", extra=properties)


def send_to_amplitude(event_name: str, properties: Dict[str, Any]) -> None:
    """Send event to Amplitude"""
    # Placeholder for Amplitude integration
    # You would use the Amplitude Python library
    logger.info(f"Amplitude Event: {event_name}", extra=properties)


def send_to_segment(event_name: str, properties: Dict[str, Any]) -> None:
    """Send event to Segment"""
    # Placeholder for Segment integration
    # You would use the Segment Python library
    logger.info(f"Segment Event: {event_name}", extra=properties)


def track_contact_created(contact, user_id: int) -> None:
    """Track contact creation event"""
    properties = {
        'contact_id': contact.id,
        'has_email': bool(contact.email),
        'has_phone': bool(contact.phone),
        'tags_count': len(contact.tags) if contact.tags else 0,
        'contact_name': contact.name,
        'contact_email': contact.email or '',
        'contact_phone': contact.phone or ''
    }
    
    track_event('contact_created', properties, user_id)


def track_contact_updated(contact, user_id: int, changed_fields: list) -> None:
    """Track contact update event"""
    properties = {
        'contact_id': contact.id,
        'fields_changed': changed_fields,
        'has_email': bool(contact.email),
        'has_phone': bool(contact.phone),
        'tags_count': len(contact.tags) if contact.tags else 0,
        'contact_name': contact.name,
        'contact_email': contact.email or '',
        'contact_phone': contact.phone or ''
    }
    
    track_event('contact_updated', properties, user_id)


def track_contact_deleted(contact, user_id: int, leads_count: int) -> None:
    """Track contact deletion event"""
    properties = {
        'contact_id': contact.id,
        'leads_count': leads_count,
        'contact_name': contact.name,
        'contact_email': contact.email or '',
        'contact_phone': contact.phone or ''
    }
    
    track_event('contact_deleted', properties, user_id)


def track_lead_created(lead, user_id: int) -> None:
    """Track lead creation event"""
    properties = {
        'lead_id': lead.id,
        'status': lead.status,
        'asset_id': lead.asset.id,
        'contact_id': lead.contact.id,
        'contact_name': lead.contact.name,
        'asset_address': f"{lead.asset.street} {lead.asset.number}, {lead.asset.city}",
        'notes_count': len(lead.notes) if lead.notes else 0
    }
    
    track_event('lead_created', properties, user_id)


def track_lead_updated(lead, user_id: int, changed_fields: list) -> None:
    """Track lead update event"""
    properties = {
        'lead_id': lead.id,
        'fields_changed': changed_fields,
        'status': lead.status,
        'asset_id': lead.asset.id,
        'contact_id': lead.contact.id,
        'contact_name': lead.contact.name,
        'asset_address': f"{lead.asset.street} {lead.asset.number}, {lead.asset.city}",
        'notes_count': len(lead.notes) if lead.notes else 0
    }
    
    track_event('lead_updated', properties, user_id)


def track_lead_deleted(lead, user_id: int) -> None:
    """Track lead deletion event"""
    properties = {
        'lead_id': lead.id,
        'status': lead.status,
        'asset_id': lead.asset.id,
        'contact_id': lead.contact.id,
        'contact_name': lead.contact.name,
        'asset_address': f"{lead.asset.street} {lead.asset.number}, {lead.asset.city}",
        'notes_count': len(lead.notes) if lead.notes else 0
    }
    
    track_event('lead_deleted', properties, user_id)


def track_lead_status_changed(lead, user_id: int, from_status: str, to_status: str) -> None:
    """Track lead status change event"""
    properties = {
        'lead_id': lead.id,
        'from_status': from_status,
        'to_status': to_status,
        'asset_id': lead.asset.id,
        'contact_id': lead.contact.id,
        'contact_name': lead.contact.name,
        'asset_address': f"{lead.asset.street} {lead.asset.number}, {lead.asset.city}"
    }
    
    track_event('lead_status_changed', properties, user_id)


def track_lead_note_added(lead, user_id: int, note_text: str) -> None:
    """Track lead note addition event"""
    properties = {
        'lead_id': lead.id,
        'note_length': len(note_text),
        'note_text': note_text[:100],  # Truncate for privacy
        'status': lead.status,
        'asset_id': lead.asset.id,
        'contact_id': lead.contact.id,
        'contact_name': lead.contact.name
    }
    
    track_event('lead_note_added', properties, user_id)


def track_lead_report_sent(lead, user_id: int, via: str) -> None:
    """Track lead report sending event"""
    properties = {
        'lead_id': lead.id,
        'via': via,  # 'email' or 'link'
        'status': lead.status,
        'asset_id': lead.asset.id,
        'contact_id': lead.contact.id,
        'contact_name': lead.contact.name,
        'contact_email': lead.contact.email or '',
        'asset_address': f"{lead.asset.street} {lead.asset.number}, {lead.asset.city}"
    }
    
    track_event('lead_report_sent', properties, user_id)


def track_asset_change_notified(asset, user_id: int, leads_count: int, change_summary: str) -> None:
    """Track asset change notification event"""
    properties = {
        'asset_id': asset.id,
        'leads_count': leads_count,
        'change_summary': change_summary[:200],  # Truncate for privacy
        'asset_address': f"{asset.street} {asset.number}, {asset.city}",
        'asset_price': asset.price,
        'asset_area': asset.area,
        'asset_rooms': asset.rooms
    }
    
    track_event('asset_change_notified', properties, user_id)


def track_crm_search(user_id: int, search_type: str, search_query: str, results_count: int) -> None:
    """Track CRM search event"""
    properties = {
        'search_type': search_type,  # 'contacts' or 'leads'
        'search_query': search_query[:100],  # Truncate for privacy
        'results_count': results_count,
        'query_length': len(search_query)
    }
    
    track_event('crm_search', properties, user_id)


def track_crm_export(user_id: int, export_type: str, records_count: int) -> None:
    """Track CRM export event"""
    properties = {
        'export_type': export_type,  # 'contacts' or 'leads'
        'records_count': records_count
    }
    
    track_event('crm_export', properties, user_id)


def track_crm_dashboard_view(user_id: int, dashboard_type: str) -> None:
    """Track CRM dashboard view event"""
    properties = {
        'dashboard_type': dashboard_type,  # 'contacts', 'leads', 'overview'
        'view_timestamp': datetime.utcnow().isoformat()
    }
    
    track_event('crm_dashboard_view', properties, user_id)


def track_crm_contact_lead_association(contact, lead, user_id: int) -> None:
    """Track contact-lead association event"""
    properties = {
        'contact_id': contact.id,
        'lead_id': lead.id,
        'contact_name': contact.name,
        'asset_id': lead.asset.id,
        'asset_address': f"{lead.asset.street} {lead.asset.number}, {lead.asset.city}",
        'lead_status': lead.status
    }
    
    track_event('crm_contact_lead_association', properties, user_id)


def track_crm_bulk_action(user_id: int, action_type: str, records_count: int, success_count: int) -> None:
    """Track CRM bulk action event"""
    properties = {
        'action_type': action_type,  # 'bulk_delete', 'bulk_update', 'bulk_export'
        'records_count': records_count,
        'success_count': success_count,
        'failure_count': records_count - success_count
    }
    
    track_event('crm_bulk_action', properties, user_id)


def track_crm_permission_denied(user_id: int, resource_type: str, resource_id: int, action: str) -> None:
    """Track CRM permission denied event"""
    properties = {
        'resource_type': resource_type,  # 'contact' or 'lead'
        'resource_id': resource_id,
        'action': action,  # 'view', 'edit', 'delete'
        'denied_timestamp': datetime.utcnow().isoformat()
    }
    
    track_event('crm_permission_denied', properties, user_id)


def track_crm_error(user_id: int, error_type: str, error_message: str, context: Dict[str, Any]) -> None:
    """Track CRM error event"""
    properties = {
        'error_type': error_type,
        'error_message': error_message[:200],  # Truncate for privacy
        'context': context,
        'error_timestamp': datetime.utcnow().isoformat()
    }
    
    track_event('crm_error', properties, user_id)


def get_analytics_summary(user_id: int, days: int = 30) -> Dict[str, Any]:
    """
    Get analytics summary for a user
    
    Args:
        user_id: ID of the user
        days: Number of days to look back
        
    Returns:
        Dictionary with analytics summary
    """
    # This is a placeholder for analytics summary
    # In a real implementation, you would query your analytics database
    # or external analytics service for the summary data
    
    return {
        'total_contacts': 0,
        'total_leads': 0,
        'contacts_created_today': 0,
        'leads_created_today': 0,
        'leads_by_status': {},
        'top_contacts': [],
        'recent_activity': [],
        'conversion_rate': 0.0,
        'average_lead_lifetime': 0,
        'most_active_assets': []
    }


def export_analytics_data(user_id: int, start_date: datetime, end_date: datetime) -> str:
    """
    Export analytics data for a user
    
    Args:
        user_id: ID of the user
        start_date: Start date for export
        end_date: End date for export
        
    Returns:
        JSON string with analytics data
    """
    # This is a placeholder for analytics data export
    # In a real implementation, you would query your analytics database
    # and return the data in the requested format
    
    data = {
        'user_id': user_id,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'events': [],
        'summary': get_analytics_summary(user_id)
    }
    
    return json.dumps(data, indent=2)
