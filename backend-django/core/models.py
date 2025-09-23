import os
import logging
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)


class User(AbstractUser):
    """Custom user model for the real estate application."""

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    equity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Equity amount saved for default mortgage calculations",
    )

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        BROKER = "broker", "Broker"
        APPRAISER = "appraiser", "Appraiser"
        PRIVATE = "private", "Private"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PRIVATE,
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

    @property
    def current_plan(self):
        """Get the user's current active plan."""
        try:
            return self.user_plans.filter(is_active=True).first()
        except UserPlan.DoesNotExist:
            return None

    def get_asset_limit(self):
        """Get the asset limit for the user's current plan."""
        plan = self.current_plan
        if not plan:
            return 1  # Default to free plan limit
        return plan.plan_type.asset_limit

    def can_create_asset(self):
        """Check if user can create a new asset based on their plan limit."""
        if not self.current_plan:
            # Default to free plan
            return self.created_assets.count() < 1
        
        plan = self.current_plan.plan_type
        if plan.asset_limit == -1:  # Unlimited
            return True
        
        return self.created_assets.count() < plan.asset_limit


class PlanType(models.Model):
    """Plan type model defining different subscription tiers."""
    
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('pro', 'Professional'),
    ]
    
    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='ILS')
    billing_period = models.CharField(max_length=20, default='monthly')  # monthly, yearly
    
    # Feature limits
    asset_limit = models.IntegerField(default=5)  # -1 for unlimited
    report_limit = models.IntegerField(default=10)  # -1 for unlimited
    alert_limit = models.IntegerField(default=5)  # -1 for unlimited
    
    # Feature flags
    advanced_analytics = models.BooleanField(default=False)
    data_export = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    custom_reports = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.display_name} ({self.name})"


class UserPlan(models.Model):
    """User subscription plan tracking."""
    
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="user_plans"
    )
    plan_type = models.ForeignKey(
        PlanType,
        on_delete=models.CASCADE,
        related_name="user_plans"
    )
    
    # Subscription details
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    
    # Payment tracking
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    last_payment_at = models.DateTimeField(null=True, blank=True)
    next_payment_at = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking
    assets_used = models.IntegerField(default=0)
    reports_used = models.IntegerField(default=0)
    alerts_used = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['stripe_subscription_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_active=True),
                name='unique_active_user_plan'
            )
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.plan_type.display_name}"
    
    def is_expired(self):
        """Check if the plan has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def can_use_feature(self, feature_name, amount=1):
        """Check if user can use a specific feature based on their plan."""
        if not self.is_active or self.is_expired():
            return False
        
        # Handle asset limits
        if feature_name == 'assets':
            if self.plan_type.asset_limit == -1:  # Unlimited
                return True
            return (self.assets_used + amount) <= self.plan_type.asset_limit
        
        # Handle report limits
        if feature_name == 'reports':
            if self.plan_type.report_limit == -1:  # Unlimited
                return True
            return (self.reports_used + amount) <= self.plan_type.report_limit
        
        # Handle alert limits
        if feature_name == 'alerts':
            if self.plan_type.alert_limit == -1:  # Unlimited
                return True
            return (self.alerts_used + amount) <= self.plan_type.alert_limit
        
        # Handle boolean features
        feature_map = {
            'advanced_analytics': self.plan_type.advanced_analytics,
            'data_export': self.plan_type.data_export,
            'api_access': self.plan_type.api_access,
            'priority_support': self.plan_type.priority_support,
            'custom_reports': self.plan_type.custom_reports,
        }
        
        return feature_map.get(feature_name, False)
    
    def get_remaining_assets(self):
        """Get remaining asset slots for the user."""
        if self.plan_type.asset_limit == -1:  # Unlimited
            return -1
        return max(0, self.plan_type.asset_limit - self.assets_used)


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
        ("syncing", "Syncing"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]

    scope_type = models.CharField(max_length=50, choices=SCOPE_TYPE_CHOICES)
    city = models.CharField(max_length=100, blank=True, null=True)
    neighborhood = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=200, blank=True, null=True)
    number = models.IntegerField(blank=True, null=True)
    block = models.CharField(max_length=20, blank=True, null=True)
    parcel = models.CharField(max_length=20, blank=True, null=True)
    subparcel = models.CharField(max_length=20, blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    normalized_address = models.CharField(max_length=500, blank=True, null=True)

    # Additional real estate fields
    building_type = models.CharField(
        max_length=50, blank=True, null=True
    )  # דירה, בית פרטי, etc.
    floor = models.IntegerField(blank=True, null=True)
    apartment = models.CharField(max_length=20, blank=True, null=True)
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
    last_sync_started_at = models.DateTimeField(blank=True, null=True)
    last_enrich_error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["scope_type"]),
            models.Index(fields=["city"]),
            models.Index(fields=["neighborhood"]),
            models.Index(fields=["street"]),
            models.Index(fields=["block"]),
            models.Index(fields=["parcel"]),
            models.Index(fields=["subparcel"]),
            models.Index(fields=["normalized_address"]),
            models.Index(fields=["status"]),
            models.Index(fields=["building_type"]),
            models.Index(fields=["price"]),
            models.Index(fields=["area"]),
            models.Index(fields=["rooms"]),
            models.Index(fields=["zoning"]),
        ]

    # Attribution fields
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_assets",
        help_text="User who originally created this asset"
    )
    last_updated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_assets",
        help_text="User who last updated this asset"
    )

    def __str__(self):
        return f"Asset({self.id}, {self.scope_type}, {self.status})"
    
    @property
    def address(self):
        """Return the normalized address or construct from components."""
        if self.normalized_address:
            return self.normalized_address
        
        # Construct address from components
        parts = []
        if self.street:
            parts.append(self.street)
        if self.number:
            parts.append(str(self.number))
        if self.apartment:
            parts.append(f"דירה {self.apartment}")
        if self.city:
            parts.append(self.city)
        
        return " ".join(parts) if parts else None

    def delete_asset(self):
        """Delete the asset and its related records."""
        try:
            self.delete()
            return True
        except Exception as e:
            # Log the error but don't fail the deletion
            logger.error("Error deleting asset %s: %s", self.id, e)
            return False

    def set_property(self, key, value, source=None, url=None, meta_prefix=""):
        """Unified setter that updates both direct fields and metadata."""
        if value is None:
            return
        
        # Initialize meta field if it doesn't exist
        if not self.meta:
            self.meta = {}
        
        # Store the value directly on the asset if the field exists
        if hasattr(self, key):
            try:
                setattr(self, key, value)
            except Exception as e:
                logger.debug(f"Could not set asset.{key}: {e}")
        
        # Store metadata for this property
        meta_key = f"{meta_prefix}_{key}" if meta_prefix else key
        self.meta[meta_key] = {
            "value": value,
            "source": source or "unknown",
            "fetched_at": timezone.now().isoformat(),
            "url": url
        }
        
        # Also store the original key in meta for backward compatibility
        self.meta[key] = value

    def set_properties(self, data_dict, source=None, url=None, meta_prefix=""):
        """Bulk setter for multiple properties with unified metadata."""
        for key, value in data_dict.items():
            self.set_property(key, value, source, url, meta_prefix)
    
    def get_property_meta(self, key):
        """Get metadata for a specific property."""
        if not self.meta:
            return None
        return self.meta.get(key)
    
    def get_property_value(self, key, default=None):
        """
        Get the value of a property (from direct field or meta).
        Supports nested access using dot notation.
        
        Examples:
            asset.get_property_value('price')  # Simple field
            asset.get_property_value('government_data.decisive_appraisals', [])  # Nested
            asset.get_property_value('gis_data.land_use_rights', [])  # Nested
        """
        # Handle nested access with dot notation
        if '.' in key:
            return self._get_nested_value(key, default)
        
        # First try direct field
        if hasattr(self, key):
            value = getattr(self, key)
            if value is not None:
                return value
        
        # Fall back to meta
        if self.meta and key in self.meta:
            meta = self.meta[key]
            if isinstance(meta, dict):
                return meta.get("value")
            return meta
        
        return default
    
    def _get_nested_value(self, key_path, default=None):
        """Helper method to get nested values from meta."""
        if not self.meta:
            return default
            
        keys = key_path.split('.')
        current = self.meta
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
                
        return current


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


class AssetContribution(models.Model):
    """Track detailed contributions to assets by users."""
    
    CONTRIBUTION_TYPE_CHOICES = [
        ('creation', 'Asset Creation'),
        ('enrichment', 'Data Enrichment'),
        ('verification', 'Data Verification'),
        ('update', 'Field Update'),
        ('source_add', 'Source Addition'),
        ('comment', 'Comment/Note'),
    ]
    
    asset = models.ForeignKey(
        Asset, 
        on_delete=models.CASCADE, 
        related_name="contributions"
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="asset_contributions"
    )
    contribution_type = models.CharField(
        max_length=20,
        choices=CONTRIBUTION_TYPE_CHOICES
    )
    field_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Specific field that was updated (if applicable)"
    )
    old_value = models.TextField(
        blank=True,
        null=True,
        help_text="Previous value (if updating existing data)"
    )
    new_value = models.TextField(
        blank=True,
        null=True,
        help_text="New value added or updated"
    )
    source = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Source of the contribution (yad2, manual, etc.)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description of the contribution"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["asset", "user"]),
            models.Index(fields=["contribution_type"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Contribution({self.user.email}, {self.contribution_type}, Asset {self.asset.id})"


class UserProfile(models.Model):
    """Extended user profile with contribution statistics and preferences."""
    
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="profile"
    )
    
    # Contribution statistics
    assets_created = models.IntegerField(default=0)
    assets_updated = models.IntegerField(default=0)
    contributions_made = models.IntegerField(default=0)
    data_points_added = models.IntegerField(default=0)
    sources_contributed = models.IntegerField(default=0)
    
    # Community reputation
    reputation_score = models.IntegerField(default=0)
    verification_count = models.IntegerField(default=0)
    helpful_votes = models.IntegerField(default=0)
    
    # Preferences
    show_attribution = models.BooleanField(
        default=True,
        help_text="Show attribution for this user's contributions"
    )
    public_profile = models.BooleanField(
        default=False,
        help_text="Allow other users to see this user's contribution history"
    )
    contribution_notifications = models.BooleanField(
        default=True,
        help_text="Receive notifications when others contribute to assets you created"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_contribution_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["reputation_score"]),
            models.Index(fields=["assets_created"]),
            models.Index(fields=["last_contribution_at"]),
        ]
    
    def __str__(self):
        return f"Profile({self.user.email})"
    
    def update_contribution_stats(self, contribution_type: str):
        """Update contribution statistics when user makes a contribution."""
        if contribution_type == 'creation':
            self.assets_created += 1
        elif contribution_type in ['enrichment', 'update', 'verification']:
            self.assets_updated += 1
        
        self.contributions_made += 1
        self.last_contribution_at = timezone.now()
        self.save(update_fields=[
            'assets_created', 'assets_updated', 'contributions_made', 
            'last_contribution_at'
        ])


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


class Document(models.Model):
    """Document model for storing file metadata and managing document uploads."""
    
    DOCUMENT_TYPE_CHOICES = [
        ("tabu", "Tabu"),
        ("condo_plan", "Condominium Plan"),
        ("permit", "Building Permit"),
        ("appraisal", "Appraisal"),
        ("appraisal_decisive", "Decisive Appraisal"),
        ("appraisal_rmi", "RAMI Appraisal"),
        ("rights", "Rights Document"),
        ("plan", "Planning Document"),
        ("contract", "Contract"),
        ("deed", "Deed"),
        ("other", "Other"),
    ]
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
    ]
    
    # Core fields
    asset = models.ForeignKey(
        Asset, 
        on_delete=models.CASCADE, 
        related_name="documents",
        help_text="Asset this document belongs to"
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="uploaded_documents",
        help_text="User who uploaded this document"
    )
    
    # Document metadata
    title = models.CharField(max_length=200, help_text="Document title")
    description = models.TextField(blank=True, null=True, help_text="Document description")
    document_type = models.CharField(
        max_length=50, 
        choices=DOCUMENT_TYPE_CHOICES, 
        default="other",
        help_text="Type of document"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="pending",
        help_text="Document status"
    )
    
    # File information
    filename = models.CharField(max_length=255, help_text="Original filename")
    file_path = models.CharField(max_length=500, help_text="Path to stored file")
    file_size = models.IntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100, help_text="MIME type of the file")
    
    # External references
    external_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="External system ID (e.g., permit number)"
    )
    external_url = models.URLField(
        blank=True, 
        null=True,
        help_text="URL to external document"
    )
    source = models.CharField(
        max_length=100, 
        default="user_upload",
        help_text="Source of the document"
    )
    
    # Dates
    document_date = models.DateField(
        blank=True, 
        null=True,
        help_text="Date the document was issued/created"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional metadata
    meta = models.JSONField(default=dict, help_text="Additional metadata")
    
    class Meta:
        indexes = [
            models.Index(fields=["asset"]),
            models.Index(fields=["user"]),
            models.Index(fields=["document_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["uploaded_at"]),
            models.Index(fields=["external_id"]),
        ]
        ordering = ["-uploaded_at"]
    
    def __str__(self):
        return f"Document({self.id}, {self.title}, {self.document_type})"
    
    @property
    def file_url(self):
        """Return the API URL to download the document."""
        return f"/api/assets/{self.asset_id}/documents/{self.id}/download/"
    
    @property
    def is_downloadable(self):
        """Check if document can be downloaded."""
        return bool(self.file_path and os.path.exists(self.file_path))
    
    def delete_file(self):
        """Delete the physical file from storage."""
        if self.file_path and os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
                return True
            except OSError as e:
                logger.error(f"Error deleting file {self.file_path}: {e}")
                return False
        return True

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


class UserSession(models.Model):
    """Track user sessions for engagement analytics."""
    
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.FloatField(default=0.0)  # in seconds
    page_view_count = models.IntegerField(default=0)
    is_bounce = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=["session_id"]),
            models.Index(fields=["user"]),
            models.Index(fields=["started_at"]),
        ]


class PageView(models.Model):
    """Track individual page views for detailed analytics."""
    
    session = models.ForeignKey(
        UserSession,
        on_delete=models.CASCADE,
        related_name="page_views"
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="page_views",
    )
    page_path = models.CharField(max_length=500)
    page_title = models.CharField(max_length=200, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField(default=0.0)  # time spent on page in seconds
    load_time = models.FloatField(default=0.0)  # page load time in seconds
    meta = models.JSONField(default=dict, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["session"]),
            models.Index(fields=["user"]),
            models.Index(fields=["viewed_at"]),
            models.Index(fields=["page_path"]),
        ]


class PlanningMetrics(models.Model):
    """Planning metrics for assets including coverage, setbacks, and height analysis."""
    
    asset = models.OneToOneField('Asset', on_delete=models.CASCADE, related_name='planning_metrics')
    
    # Area calculations
    parcel_area_m2 = models.FloatField(null=True, blank=True, help_text="Total parcel area in square meters")
    footprint_area_m2 = models.FloatField(null=True, blank=True, help_text="Building footprint area in square meters")
    coverage_pct = models.FloatField(null=True, blank=True, help_text="Coverage percentage (footprint/parcel)")
    
    # Planning envelope and violations
    allowed_envelope_polygon = models.JSONField(null=True, blank=True, help_text="GeoJSON polygon of allowed building envelope")
    setback_violations = models.JSONField(default=list, help_text="List of setback violations with details")
    
    # Height analysis
    height_current = models.JSONField(default=dict, help_text="Current building height data")
    height_allowed = models.JSONField(default=dict, help_text="Allowed building height data")
    height_delta = models.JSONField(default=dict, help_text="Height difference calculations")
    
    # Calculation metadata
    calc_confidence = models.CharField(
        max_length=20, 
        default="LOW",
        choices=[
            ("LOW", "Low confidence"),
            ("MEDIUM", "Medium confidence"),
            ("HIGH", "High confidence")
        ],
        help_text="Confidence level of calculations"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Planning Metrics"
        verbose_name_plural = "Planning Metrics"
        indexes = [
            models.Index(fields=["asset"]),
            models.Index(fields=["calc_confidence"]),
            models.Index(fields=["updated_at"]),
        ]
    
    def __str__(self):
        return f"Planning Metrics for {self.asset}"


class AnalyticsDaily(models.Model):
    """Daily rollups for analytics events."""

    date = models.DateField(unique=True)
    
    # Core metrics
    users = models.IntegerField(default=0)
    assets = models.IntegerField(default=0)
    reports = models.IntegerField(default=0)
    alerts = models.IntegerField(default=0)
    errors = models.IntegerField(default=0)
    
    # User engagement metrics
    page_views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    session_duration_avg = models.FloatField(default=0.0)  # in seconds
    bounce_rate = models.FloatField(default=0.0)  # percentage
    
    # Feature usage metrics
    marketing_messages_created = models.IntegerField(default=0)
    searches_performed = models.IntegerField(default=0)
    filters_applied = models.IntegerField(default=0)
    exports_downloaded = models.IntegerField(default=0)
    
    # Conversion metrics
    signup_conversions = models.IntegerField(default=0)
    asset_creation_conversions = models.IntegerField(default=0)
    report_generation_conversions = models.IntegerField(default=0)
    alert_setup_conversions = models.IntegerField(default=0)
    
    # Performance metrics
    avg_page_load_time = models.FloatField(default=0.0)  # in seconds
    api_response_time_avg = models.FloatField(default=0.0)  # in seconds
    error_rate = models.FloatField(default=0.0)  # percentage

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
