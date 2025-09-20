"""
CRM services for notifications and report sending.
"""
import logging
from typing import Optional
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from io import BytesIO

from .models import Lead
from .analytics import track_asset_change_notified

logger = logging.getLogger(__name__)


def notify_asset_change(asset_id: int, change_summary: str):
    """
    Notify all leads associated with an asset about changes.
    
    Args:
        asset_id: ID of the asset that changed
        change_summary: Description of the change
    """
    try:
        leads = Lead.objects.filter(asset_id=asset_id).select_related("contact")
        
        for lead in leads:
            contact = lead.contact
            if contact.email:
                try:
                    send_mail(
                        subject="עדכון בנכס במעקב - נדל״נר",
                        message=f"""
היי {contact.name},

{change_summary}

תוכל לראות את הפרטים המלאים בקישור הבא:
{settings.FRONTEND_URL}/assets/{asset_id}

בברכה,
צוות נדל״נר
                        """,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[contact.email],
                        fail_silently=False,
                    )
                    logger.info(f"Asset change notification sent to {contact.email}")
                except Exception as e:
                    logger.error(f"Failed to send notification to {contact.email}: {e}")
        
        logger.info(f"Asset change notifications processed for asset {asset_id}")
        
        # Track asset change notification event
        from core.models import Asset
        try:
            asset = Asset.objects.get(id=asset_id)
            track_asset_change_notified(asset, asset.created_by_id, leads.count(), change_summary)
        except Asset.DoesNotExist:
            logger.warning(f"Asset {asset_id} not found for analytics tracking")
        
    except Exception as e:
        logger.error(f"Error in notify_asset_change for asset {asset_id}: {e}")


def send_report_to_contact(lead_id: int, report_payload: dict):
    """
    Send a branded report to a lead's contact.
    
    Args:
        lead_id: ID of the lead
        report_payload: Report data to include in the email
    """
    try:
        lead = Lead.objects.select_related("contact").get(id=lead_id)
        contact = lead.contact
        
        if not contact.email:
            logger.warning(f"No email for contact {contact.id}, cannot send report")
            return False
        
        # Generate report content (this would integrate with existing report service)
        report_content = generate_report_content(lead, report_payload)
        
        send_mail(
            subject="דוח נדל״נר - נכס במעקב",
            message=f"""
היי {contact.name},

מצורף דוח ממותג עבור הנכס במעקב שלך.

{report_content}

תוכל לראות את הפרטים המלאים בקישור הבא:
{settings.FRONTEND_URL}/assets/{lead.asset_id}

בברכה,
צוות נדל״נר
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[contact.email],
            fail_silently=False,
        )
        
        logger.info(f"Report sent to {contact.email} for lead {lead_id}")
        
        # Track report sending event
        from .analytics import track_lead_report_sent
        via = 'email' if contact.email else 'link'
        track_lead_report_sent(lead, contact.owner_id, via)
        
        return True
        
    except Lead.DoesNotExist:
        logger.error(f"Lead {lead_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending report to lead {lead_id}: {e}")
        return False


def generate_report_content(lead: Lead, report_payload: dict) -> str:
    """
    Generate report content for email.
    
    Args:
        lead: The lead object
        report_payload: Report data
        
    Returns:
        Formatted report content
    """
    asset = lead.asset
    
    content = f"""
פרטי הנכס:
- כתובת: {asset.address or 'לא זמין'}
- מחיר: {asset.price or 'לא זמין'} ₪
- חדרים: {asset.rooms or 'לא זמין'}
- שטח: {asset.area or 'לא זמין'} מ״ר
- סטטוס ליד: {lead.get_status_display()}
"""
    
    if lead.notes:
        content += "\nהערות:\n"
        for note in lead.notes[-3:]:  # Show last 3 notes
            content += f"- {note.get('text', '')}\n"
    
    return content


def get_asset_leads_summary(asset_id: int) -> dict:
    """
    Get summary of leads for an asset.
    
    Args:
        asset_id: ID of the asset
        
    Returns:
        Dictionary with lead statistics
    """
    leads = Lead.objects.filter(asset_id=asset_id).select_related("contact")
    
    summary = {
        "total_leads": leads.count(),
        "by_status": {},
        "contacts": []
    }
    
    # Count by status
    for status, _ in LeadStatus.choices:
        count = leads.filter(status=status).count()
        if count > 0:
            summary["by_status"][status] = count
    
    # Get contact info
    for lead in leads:
        summary["contacts"].append({
            "id": lead.contact.id,
            "name": lead.contact.name,
            "email": lead.contact.email,
            "status": lead.status,
            "last_activity": lead.last_activity_at.isoformat()
        })
    
    return summary


def send_email(subject: str, message: str, recipient_list: list, from_email: str = None):
    """
    Send email using Django's send_mail function.
    
    Args:
        subject: Email subject
        message: Email message body
        recipient_list: List of recipient email addresses
        from_email: Sender email address (defaults to settings.DEFAULT_FROM_EMAIL)
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        logger.info(f"Email sent to {recipient_list}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def build_branded_pdf(lead: Lead, report_payload: dict) -> BytesIO:
    """
    Build a branded PDF report for a lead.
    
    Args:
        lead: The lead object
        report_payload: Report data to include
        
    Returns:
        BytesIO object containing the PDF
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 100, "דוח נדל״נר - נכס במעקב")
    
    # Asset details
    p.setFont("Helvetica", 12)
    y_position = height - 150
    
    asset = lead.asset
    contact = lead.contact
    
    # Contact info
    p.drawString(100, y_position, f"לקוח: {contact.name}")
    y_position -= 20
    
    if contact.email:
        p.drawString(100, y_position, f"אימייל: {contact.email}")
        y_position -= 20
    
    if contact.phone:
        p.drawString(100, y_position, f"טלפון: {contact.phone}")
        y_position -= 20
    
    y_position -= 20
    
    # Asset details
    p.drawString(100, y_position, "פרטי הנכס:")
    y_position -= 20
    
    if asset.address:
        p.drawString(120, y_position, f"כתובת: {asset.address}")
        y_position -= 20
    
    if asset.price:
        p.drawString(120, y_position, f"מחיר: {asset.price:,} ₪")
        y_position -= 20
    
    if asset.rooms:
        p.drawString(120, y_position, f"חדרים: {asset.rooms}")
        y_position -= 20
    
    if asset.area:
        p.drawString(120, y_position, f"שטח: {asset.area} מ״ר")
        y_position -= 20
    
    y_position -= 20
    
    # Lead status
    p.drawString(100, y_position, f"סטטוס ליד: {lead.get_status_display()}")
    y_position -= 30
    
    # Notes
    if lead.notes:
        p.drawString(100, y_position, "הערות:")
        y_position -= 20
        
        for note in lead.notes[-5:]:  # Show last 5 notes
            note_text = note.get('text', '')[:100]  # Limit length
            p.drawString(120, y_position, f"• {note_text}")
            y_position -= 20
    
    # Footer
    p.setFont("Helvetica", 10)
    p.drawString(100, 100, f"נוצר ב: {lead.created_at.strftime('%d/%m/%Y %H:%M')}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer
