import os
import logging
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


class User(AbstractUser):
    """Custom user model for the real estate application."""

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        db_index=True,
    )
    is_verified = models.BooleanField(default=False)
    is_demo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # User preference fields for settings page
    language = models.CharField(max_length=10, default="en")
    timezone = models.CharField(max_length=100, default="UTC")
    currency = models.CharField(max_length=10, default="usd")
    date_format = models.CharField(max_length=20, default="yyyy-mm-dd")
    notify_email = models.BooleanField(default=True)
    notify_whatsapp = models.BooleanField(default=False)
    notify_urgent = models.BooleanField(default=True)
    notification_time = models.CharField(max_length=5, default="09:00")
    report_sections = models.JSONField(default=list)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email


class OnboardingProgress(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="onboarding_progress",
    )
    connect_payment = models.BooleanField(default=False)
    add_first_asset = models.BooleanField(default=False)
    generate_first_report = models.BooleanField(default=False)
    set_one_alert = models.BooleanField(default=False)

    def is_complete(self):
        return all(
            [
                self.connect_payment,
                self.add_first_asset,
                self.generate_first_report,
                self.set_one_alert,
            ]
        )

    def __str__(self):
        return f"OnboardingProgress({self.user_id})"


class Alert(models.Model):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="alerts"
    )
    criteria = models.JSONField()
    notify = models.JSONField(default=list)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert({self.user.email}, active={self.active})"


class AlertRule(models.Model):
    """Alert rule model for user-defined notification triggers."""
    
    TRIGGER_TYPE_CHOICES = [
        ('PRICE_DROP', 'ירידת מחיר'),
        ('NEW_LISTING', 'נכס חדש'),
        ('MARKET_TREND', 'שינוי בשוק'),
        ('DOCS_UPDATE', 'עדכון מסמכים'),
        ('PERMIT_STATUS', 'סטטוס היתרים'),
        ('NEW_GOV_TX', 'עסקה חדשה בסביבה'),
        ('LISTING_REMOVED', 'מודעה הוסרה'),
    ]
    
    FREQUENCY_CHOICES = [
        ('immediate', 'מיידי'),
        ('daily', 'יומי'),
    ]
    
    SCOPE_CHOICES = [
        ('global', 'כללי'),
        ('asset', 'נכס ספציפי'),
    ]
    
    user = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE, 
        related_name="alert_rules"
    )
    scope = models.CharField(
        max_length=20, 
        choices=SCOPE_CHOICES, 
        default='global'
    )
    asset = models.ForeignKey(
        'Asset', 
        on_delete=models.CASCADE, 
        related_name="alert_rules",
        null=True, 
        blank=True
    )
    trigger_type = models.CharField(
        max_length=20, 
        choices=TRIGGER_TYPE_CHOICES
    )
    params = models.JSONField(default=dict)
    channels = models.JSONField(default=list)  # ['email', 'whatsapp']
    frequency = models.CharField(
        max_length=20, 
        choices=FREQUENCY_CHOICES, 
        default='immediate'
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'active']),
            models.Index(fields=['scope', 'asset']),
            models.Index(fields=['trigger_type']),
        ]
    
    def __str__(self):
        return f"AlertRule({self.user.email}, {self.trigger_type}, {self.scope})"


class AlertEvent(models.Model):
    """Alert event model for tracking triggered notifications."""
    
    alert_rule = models.ForeignKey(
        AlertRule, 
        on_delete=models.CASCADE, 
        related_name="events"
    )
    asset = models.ForeignKey(
        'Asset', 
        on_delete=models.CASCADE, 
        related_name="alert_events",
        null=True, 
        blank=True
    )
    occurred_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict)
    payload_hash = models.CharField(max_length=64, unique=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    digest_id = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['alert_rule', 'occurred_at']),
            models.Index(fields=['asset', 'occurred_at']),
            models.Index(fields=['payload_hash']),
            models.Index(fields=['delivered_at']),
        ]
        ordering = ['-occurred_at']
    
    def __str__(self):
        return f"AlertEvent({self.alert_rule.trigger_type}, {self.occurred_at})"


class Snapshot(models.Model):
    """Asset snapshot model for tracking changes over time."""
    
    asset = models.ForeignKey(
        'Asset', 
        on_delete=models.CASCADE, 
        related_name="snapshots"
    )
    payload = models.JSONField(default=dict)
    ppsqm = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['asset', 'created_at']),
            models.Index(fields=['ppsqm']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Snapshot({self.asset_id}, {self.created_at})"


# Asset Enrichment Pipeline Models
class Asset(models.Model):
    """Asset model for the enrichment pipeline."""

    SCOPE_TYPE_CHOICES = [
        ("address", "Address"),
        ("neighborhood", "Neighborhood"),
        ("street", "Street"),
        ("city", "City"),
        ("parcel", "Parcel"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("enriching", "Enriching"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]

    scope_type = models.CharField(max_length=50, choices=SCOPE_TYPE_CHOICES)
    city = models.CharField(max_length=100, blank=True, null=True)
    neighborhood = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=200, blank=True, null=True)
    number = models.IntegerField(blank=True, null=True)
    gush = models.CharField(max_length=20, blank=True, null=True)
    helka = models.CharField(max_length=20, blank=True, null=True)
    subhelka = models.CharField(max_length=20, blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    normalized_address = models.CharField(max_length=500, blank=True, null=True)

    # Additional real estate fields
    building_type = models.CharField(
        max_length=50, blank=True, null=True
    )  # דירה, בית פרטי, etc.
    floor = models.IntegerField(blank=True, null=True)
    total_floors = models.IntegerField(blank=True, null=True)
    rooms = models.IntegerField(blank=True, null=True)
    bedrooms = models.IntegerField(blank=True, null=True)
    bathrooms = models.IntegerField(blank=True, null=True)
    area = models.FloatField(blank=True, null=True)  # שטח נטו
    total_area = models.FloatField(blank=True, null=True)  # שטח כולל
    balcony_area = models.FloatField(blank=True, null=True)
    parking_spaces = models.IntegerField(blank=True, null=True)
    storage_room = models.BooleanField(default=False)
    elevator = models.BooleanField(default=False)
    air_conditioning = models.BooleanField(default=False)
    furnished = models.BooleanField(default=False)
    renovated = models.BooleanField(default=False)
    year_built = models.IntegerField(blank=True, null=True)
    last_renovation = models.IntegerField(blank=True, null=True)

    # Financial fields
    price = models.IntegerField(blank=True, null=True)
    price_per_sqm = models.IntegerField(blank=True, null=True)
    rent_estimate = models.IntegerField(blank=True, null=True)

    # Legal/Planning fields
    zoning = models.CharField(max_length=100, blank=True, null=True)
    building_rights = models.CharField(max_length=200, blank=True, null=True)
    permit_status = models.CharField(max_length=50, blank=True, null=True)
    permit_date = models.DateField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    is_demo = models.BooleanField(default=False)
    meta = models.JSONField(default=dict)
    last_enriched_at = models.DateTimeField(blank=True, null=True)
    last_enrich_error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["scope_type"]),
            models.Index(fields=["city"]),
            models.Index(fields=["neighborhood"]),
            models.Index(fields=["street"]),
            models.Index(fields=["gush"]),
            models.Index(fields=["helka"]),
            models.Index(fields=["subhelka"]),
            models.Index(fields=["normalized_address"]),
            models.Index(fields=["status"]),
            models.Index(fields=["building_type"]),
            models.Index(fields=["price"]),
            models.Index(fields=["area"]),
            models.Index(fields=["rooms"]),
            models.Index(fields=["zoning"]),
        ]

    def __str__(self):
        return f"Asset({self.id}, {self.scope_type}, {self.status})"

    def delete_asset(self):
        """Delete the asset and its related records."""
        try:
            self.delete()
            return True
        except Exception as e:
            # Log the error but don't fail the deletion
            logger.error("Error deleting asset %s: %s", self.id, e)
            return False


class SourceRecord(models.Model):
    """Source record model for storing data from external sources."""

    SOURCE_CHOICES = [
        ("yad2", "Yad2"),
        ("nadlan", "Nadlan"),
        ("gis_permit", "GIS Permit"),
        ("gis_rights", "GIS Rights"),
        ("rami_plan", "RAMI Plan"),
        ("tabu", "Tabu"),
    ]

    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="source_records"
    )
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    external_id = models.CharField(max_length=100, blank=True, null=True)
    title = models.CharField(max_length=500, blank=True, null=True)
    url = models.URLField(max_length=500, blank=True, null=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    raw = models.JSONField(default=dict)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["asset"]),
            models.Index(fields=["source"]),
            models.Index(fields=["external_id"]),
        ]
        unique_together = ["source", "external_id"]

    def __str__(self):
        return f"SourceRecord({self.source}, {self.external_id})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            promote_raw_to_asset(self.asset, self.raw or {})


def promote_raw_to_asset(asset: Asset, raw: dict):
    def set_if_empty(obj, field, value):
        if value in (None, "", [], {}):
            return
        if getattr(obj, field, None) in (None, "", [], {}):
            setattr(obj, field, value)

    set_if_empty(asset, "city", raw.get("city"))
    set_if_empty(asset, "street", raw.get("street"))
    set_if_empty(asset, "number", raw.get("number"))
    set_if_empty(asset, "area", raw.get("size") or raw.get("area"))
    set_if_empty(asset, "rooms", raw.get("rooms"))
    set_if_empty(asset, "bedrooms", raw.get("bedrooms"))
    set_if_empty(asset, "building_type", raw.get("property_type"))
    asset.save()


class RealEstateTransaction(models.Model):
    """Real estate transaction model for storing deal data."""

    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="transactions"
    )
    deal_id = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)
    rooms = models.IntegerField(blank=True, null=True)
    area = models.FloatField(blank=True, null=True)
    floor = models.IntegerField(blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    raw = models.JSONField(default=dict)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["asset"]),
            models.Index(fields=["deal_id"]),
        ]

    def __str__(self):
        return f"Transaction({self.deal_id}, {self.price})"


class Report(models.Model):
    """Report model for storing generated report metadata."""

    REPORT_TYPE_CHOICES = [
        ("asset", "Asset Report"),
        ("market", "Market Report"),
        ("investment", "Investment Analysis"),
        ("comparison", "Property Comparison"),
    ]

    STATUS_CHOICES = [
        ("generating", "Generating"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True,
    )
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="reports", null=True, blank=True
    )
    report_type = models.CharField(
        max_length=50, choices=REPORT_TYPE_CHOICES, default="asset"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="generating"
    )

    # File information
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField(blank=True, null=True)  # in bytes

    # Report content metadata
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    pages = models.IntegerField(default=1)

    # Generation details
    generated_at = models.DateTimeField(auto_now_add=True)
    generation_time = models.FloatField(blank=True, null=True)  # in seconds

    # Error handling
    error_message = models.TextField(blank=True, null=True)

    # Additional metadata
    sections = models.JSONField(default=list)
    meta = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["asset"]),
            models.Index(fields=["report_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["generated_at"]),
        ]
        ordering = ["-generated_at"]

    def __str__(self):
        return f"Report({self.id}, {self.report_type}, {self.status})"

    @property
    def file_url(self):
        """Return the API URL to download the report's PDF.

        Reports are stored on the backend and served through a dedicated
        endpoint so the front-end does not need direct filesystem access.
        """

        return f"/api/reports/file/{self.filename}"

    def mark_completed(self, file_size=None, pages=None, generation_time=None):
        """Mark the report as completed with metadata."""
        self.status = "completed"
        if file_size is not None:
            self.file_size = file_size
        if pages is not None:
            self.pages = pages
        if generation_time is not None:
            self.generation_time = generation_time
        self.save()

    def mark_failed(self, error_message):
        """Mark the report as failed with error message."""
        self.status = "failed"
        self.error_message = error_message
        self.save()

    def delete_report(self):
        """Delete the report file and database record."""
        try:
            # Delete the physical file if it exists
            if os.path.exists(self.file_path):
                os.remove(self.file_path)

            # Delete the database record
            self.delete()
            return True
        except Exception as e:
            # Log the error but don't fail the deletion
            logger.error("Error deleting report %s: %s", self.id, e)
            return False


class Permit(models.Model):
    """Building permit associated with an asset."""

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="permits")
    permit_number = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, blank=True)
    issued_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    file_url = models.CharField(max_length=500, blank=True)
    raw = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=["asset"]),
            models.Index(fields=["permit_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Permit({self.permit_number})"


class Plan(models.Model):
    """Planning document associated with an asset."""

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="plans")
    plan_number = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, blank=True)
    effective_date = models.DateField(blank=True, null=True)
    file_url = models.CharField(max_length=500, blank=True)
    raw = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=["asset"]),
            models.Index(fields=["plan_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Plan({self.plan_number})"


class ShareToken(models.Model):
    """Token allowing read-only access to an asset."""

    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="share_tokens"
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["asset"]),
        ]

    def __str__(self):
        return f"ShareToken({self.asset_id}, {self.token})"


class AnalyticsEvent(models.Model):
    """Raw analytics events for tracking system activity."""

    created_at = models.DateTimeField(auto_now_add=True)
    event = models.CharField(max_length=100)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analytics_events",
    )
    asset_id = models.IntegerField(null=True, blank=True)
    source = models.CharField(max_length=100, null=True, blank=True)
    error_code = models.CharField(max_length=100, null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["event"]),
            models.Index(fields=["source"]),
            models.Index(fields=["error_code"]),
        ]


class AnalyticsDaily(models.Model):
    """Daily rollups for analytics events."""

    date = models.DateField(unique=True)
    users = models.IntegerField(default=0)
    assets = models.IntegerField(default=0)
    reports = models.IntegerField(default=0)
    alerts = models.IntegerField(default=0)
    errors = models.IntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["date"])]

    def __str__(self):
        return f"AnalyticsDaily({self.date})"


class SupportTicket(models.Model):
    class Kind(models.TextChoices):
        CONTACT = "contact"
        BUG = "bug"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    severity = models.CharField(max_length=16, blank=True)
    url = models.URLField(blank=True)
    user_agent = models.TextField(blank=True)
    app_version = models.CharField(max_length=64, blank=True)
    attachment = models.FileField(upload_to="support/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, default="open", db_index=True)

    def __str__(self):
        return f"SupportTicket({self.id}, {self.kind})"


class ConsultationRequest(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40)
    preferred_time = models.CharField(max_length=200)
    channel = models.CharField(max_length=16)
    topic = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, default="new", db_index=True)

    def __str__(self):
        return f"ConsultationRequest({self.id}, {self.email})"
