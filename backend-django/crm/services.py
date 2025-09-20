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


def send_email(to: str, subject: str, body: str, attachments: list = None):
    """
    Send an email with optional attachments.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email message body
        attachments: List of (filename, content, mimetype) tuples
    """
    from django.core.mail import EmailMessage
    
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    
    if attachments:
        for attachment in attachments:
            if len(attachment) == 3:
                filename, content, mimetype = attachment
                email.attach(filename, content, mimetype)
            else:
                filename, content = attachment
                email.attach(filename, content, 'application/octet-stream')
    
    email.send(fail_silently=False)


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
                    send_email(
                        to=contact.email,
                        subject="עדכון בנכס במעקב",
                        body=f"""
היי {contact.name},

{change_summary}

תוכל לראות את הפרטים המלאים בקישור הבא:
{settings.FRONTEND_URL}/assets/{asset_id}

בברכה,
צוות נדל"נר
                        """
                    )
                    logger.info(f"Asset change notification sent to {contact.email}")
                except Exception as e:
                    logger.error(f"Failed to send notification to {contact.email}: {e}")
        
        logger.info(f"Asset change notifications processed for asset {asset_id}")
        
        # Track asset change notification event
        from core.models import Asset
        try:
            asset = Asset.objects.get(id=asset_id)
            track_asset_change_notified(asset, asset.created_by.id, leads.count(), change_summary)
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
        
        # Generate branded PDF report
        pdf_content = build_branded_pdf(payload=report_payload, owner_id=contact.owner_id)
        
        if not contact.email:
            logger.warning(f"No email for contact {contact.id}, cannot send report")
            return False
        
        # Send email with PDF attachment
        send_email(
            to=contact.email,
            subject="דוח נדל\"נר",
            body="מצורף דוח ממותג.",
            attachments=[('nadlaner-report.pdf', pdf_content.getvalue() if hasattr(pdf_content, 'getvalue') else pdf_content)]
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


def build_branded_pdf(payload: dict, owner_id: int) -> BytesIO:
    """
    Build a branded PDF report for a lead.
    
    Args:
        payload: Report data to include
        owner_id: ID of the owner
        
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
    
    # Contact info
    p.drawString(100, y_position, f"לקוח: {payload.get('contact_name', 'Unknown')}")
    y_position -= 20
    
    
    y_position -= 20
    
    # Asset details
    p.drawString(100, y_position, "פרטי הנכס:")
    y_position -= 20
    
    if payload.get('asset_id'):
        p.drawString(120, y_position, f"מזהה נכס: {payload['asset_id']}")
        y_position -= 20
    
    y_position -= 20
    
    # Report type
    p.drawString(100, y_position, f"סוג דוח: {payload.get('report_type', 'property_analysis')}")
    y_position -= 20
    
    # Footer
    p.setFont("Helvetica", 10)
    p.drawString(100, 50, "דוח זה נוצר על ידי מערכת נדל״נר")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer
