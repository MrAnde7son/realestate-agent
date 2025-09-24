import logging
from django.conf import settings
from django.db import models
from .analytics import (
    track_contact_created, track_contact_updated, track_contact_deleted,
    track_lead_created, track_lead_updated, track_lead_deleted,
    track_lead_status_changed, track_lead_note_added, track_lead_report_sent,
    track_asset_change_notified, track_crm_search, track_crm_export
)

logger = logging.getLogger(__name__)


def track_event(event_name: str, user_id: int, properties: dict):
    """
    Generic event tracking function for CRM events.
    This is a convenience function that delegates to the analytics module.
    """
    from .analytics import analytics
    analytics.track(event_name, user_id, properties)


class Contact(models.Model):
    """Contact model for CRM - represents a client/contact."""
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="contacts"
    )
    name = models.CharField(max_length=200, help_text="Contact full name")
    phone = models.CharField(max_length=30, blank=True, help_text="Phone number")
    email = models.EmailField(blank=True, help_text="Email address")
    tags = models.JSONField(default=list, blank=True, help_text="Tags like ['משקיע', 'VIP']")
    equity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Optional equity amount to support mortgage insights",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "name"]),
            models.Index(fields=["name"]),
            models.Index(fields=["email"]),
        ]
        # Soft unique constraint - only enforce if email exists
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'email'],
                condition=models.Q(email__isnull=False) & ~models.Q(email=''),
                name='unique_owner_email'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.email or 'no-email'})"
    
    def save(self, *args, **kwargs):
        """Override save to track analytics events."""
        is_new = self.pk is None
        if not is_new:
            # Track changes for existing contact
            old_contact = Contact.objects.get(pk=self.pk)
            changed_fields = []
            for field in ['name', 'email', 'phone', 'tags']:
                if getattr(old_contact, field) != getattr(self, field):
                    changed_fields.append(field)
            
            if changed_fields:
                try:
                    track_contact_updated(self, self.owner_id, changed_fields)
                except Exception as e:
                    # Log analytics error but don't break the main functionality
                    logger.warning(f"Analytics error in contact_updated: {e}")
        
        super().save(*args, **kwargs)
        
        if is_new:
            try:
                track_contact_created(self, self.owner_id)
            except Exception as e:
                # Log analytics error but don't break the main functionality
                logger.warning(f"Analytics error in contact_created: {e}")
    
    def delete(self, *args, **kwargs):
        """Override delete to track analytics events."""
        leads_count = self.leads.count()
        try:
            track_contact_deleted(self, self.owner_id, leads_count)
        except Exception as e:
            # Log analytics error but don't break the main functionality
            logger.warning(f"Analytics error in contact_deleted: {e}")
        super().delete(*args, **kwargs)


class LeadStatus(models.TextChoices):
    """Lead status choices."""
    NEW = "new", "New"
    CONTACTED = "contacted", "Contacted"
    INTERESTED = "interested", "Interested"
    NEGOTIATING = "negotiating", "Negotiating"
    CLOSED_WON = "closed-won", "Closed Won"
    CLOSED_LOST = "closed-lost", "Closed Lost"


class Lead(models.Model):
    """Lead model - represents a potential deal between a contact and an asset."""
    
    contact = models.ForeignKey(
        Contact, 
        on_delete=models.CASCADE, 
        related_name="leads"
    )
    asset = models.ForeignKey(
        "core.Asset", 
        on_delete=models.CASCADE, 
        related_name="leads"
    )
    status = models.CharField(
        max_length=32, 
        choices=LeadStatus.choices, 
        default=LeadStatus.NEW
    )
    notes = models.JSONField(
        default=list, 
        blank=True, 
        help_text="List of notes: [{'ts': ISO, 'text': '...'}]"
    )
    last_activity_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "last_activity_at"]),
            models.Index(fields=["contact", "asset"]),
            models.Index(fields=["status"]),
            models.Index(fields=["last_activity_at"]),
        ]
        # Prevent duplicate leads for same contact-asset pair
        unique_together = [("contact", "asset")]

    def __str__(self):
        return f"Lead({self.contact_id} -> {self.asset_id})"
    
    def save(self, *args, **kwargs):
        """Override save to track analytics events."""
        is_new = self.pk is None
        if not is_new:
            # Track changes for existing lead
            old_lead = Lead.objects.get(pk=self.pk)
            changed_fields = []
            for field in ['status', 'notes']:
                if getattr(old_lead, field) != getattr(self, field):
                    changed_fields.append(field)
            
            if changed_fields:
                track_lead_updated(self, self.contact.owner_id, changed_fields)
                
                # Track status change specifically
                if 'status' in changed_fields:
                    track_lead_status_changed(self, self.contact.owner_id, old_lead.status, self.status)
        
        super().save(*args, **kwargs)
        
        if is_new:
            track_lead_created(self, self.contact.owner_id)
    
    def delete(self, *args, **kwargs):
        """Override delete to track analytics events."""
        track_lead_deleted(self, self.contact.owner_id)
        super().delete(*args, **kwargs)
    
    def add_note(self, note_text: str, user_id: int = None):
        """Add a note to the lead and track the event."""
        if not note_text.strip():
            return False
        
        notes = self.notes or []
        notes.append({
            'ts': self.last_activity_at.isoformat(),
            'text': note_text
        })
        self.notes = notes
        self.save(update_fields=['notes', 'last_activity_at'])
        
        # Track note addition
        track_lead_note_added(self, user_id or self.contact.owner_id, note_text)
        return True
    
    def send_report(self, user_id: int = None):
        """Send report to contact and track the event."""
        from .services import send_report_to_contact
        
        report_payload = {
            'asset_id': self.asset.id,
            'contact_name': self.contact.name,
            'report_type': 'property_analysis'
        }
        
        send_report_to_contact(self.id, report_payload)
        
        # Track report sending
        via = 'email' if self.contact.email else 'link'
        track_lead_report_sent(self, user_id or self.contact.owner_id, via)
        return True


class ContactTaskStatus(models.TextChoices):
    """Status options for contact tasks."""

    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class ContactTask(models.Model):
    """Actionable task associated with a CRM contact."""

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    lead = models.ForeignKey(
        "Lead",
        on_delete=models.CASCADE,
        related_name="tasks",
        blank=True,
        null=True,
        help_text="Optional lead this task is associated with"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="crm_tasks",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=32,
        choices=ContactTaskStatus.choices,
        default=ContactTaskStatus.PENDING,
    )
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "status", "due_at"]),
            models.Index(fields=["contact", "status"]),
            models.Index(fields=["lead", "status"]),
        ]
        ordering = ["due_at", "-created_at"]

    def __str__(self):
        if self.lead:
            return f"Task({self.title}) for Lead {self.lead_id}"
        return f"Task({self.title}) for Contact {self.contact_id}"

    def mark_completed(self):
        """Mark the task as completed."""
        from django.utils import timezone

        self.status = ContactTaskStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])


class ContactMeetingStatus(models.TextChoices):
    """Status options for meetings scheduled with a contact."""

    SCHEDULED = "scheduled", "Scheduled"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class ContactMeeting(models.Model):
    """Scheduled meeting for a CRM contact."""

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="meetings",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="crm_meetings",
    )
    title = models.CharField(max_length=255)
    scheduled_for = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=32,
        choices=ContactMeetingStatus.choices,
        default=ContactMeetingStatus.SCHEDULED,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "scheduled_for"]),
            models.Index(fields=["contact", "scheduled_for"]),
        ]
        ordering = ["scheduled_for"]

    def __str__(self):
        return f"Meeting({self.title}) for {self.contact_id}"


class InteractionType(models.TextChoices):
    """Type of interaction recorded with a contact."""

    CALL = "call", "Call"
    EMAIL = "email", "Email"
    MEETING = "meeting", "Meeting"
    MESSAGE = "message", "Message"
    NOTE = "note", "Note"
    OTHER = "other", "Other"


class ContactInteraction(models.Model):
    """Historic record of interactions with a contact."""

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="interactions",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="crm_interactions",
    )
    interaction_type = models.CharField(
        max_length=32,
        choices=InteractionType.choices,
        default=InteractionType.OTHER,
    )
    subject = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    occurred_at = models.DateTimeField()
    next_steps = models.TextField(blank=True)
    follow_up_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "occurred_at"]),
            models.Index(fields=["contact", "occurred_at"]),
        ]
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"Interaction({self.interaction_type}) for {self.contact_id}"
