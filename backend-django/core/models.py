import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for the real estate application."""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=50, blank=True, null=True)  # broker, appraiser, investor, etc.
    is_verified = models.BooleanField(default=False)
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
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email

class Alert(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='alerts')
    criteria = models.JSONField()
    notify = models.JSONField(default=list)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self): 
        return f"Alert({self.user.email}, active={self.active})"

# Asset Enrichment Pipeline Models
class Asset(models.Model):
    """Asset model for the enrichment pipeline."""
    SCOPE_TYPE_CHOICES = [
        ('address', 'Address'),
        ('neighborhood', 'Neighborhood'),
        ('street', 'Street'),
        ('city', 'City'),
        ('parcel', 'Parcel'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('enriching', 'Enriching'),
        ('ready', 'Ready'),
        ('error', 'Error'),
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
    building_type = models.CharField(max_length=50, blank=True, null=True)  # דירה, בית פרטי, etc.
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
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    meta = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['scope_type']),
            models.Index(fields=['city']),
            models.Index(fields=['neighborhood']),
            models.Index(fields=['street']),
            models.Index(fields=['gush']),
            models.Index(fields=['helka']),
            models.Index(fields=['subhelka']),
            models.Index(fields=['normalized_address']),
            models.Index(fields=['status']),
            models.Index(fields=['building_type']),
            models.Index(fields=['price']),
            models.Index(fields=['area']),
            models.Index(fields=['rooms']),
            models.Index(fields=['zoning']),
        ]
    
    def __str__(self):
        return f"Asset({self.id}, {self.scope_type}, {self.status})"

class SourceRecord(models.Model):
    """Source record model for storing data from external sources."""
    SOURCE_CHOICES = [
        ('yad2', 'Yad2'),
        ('nadlan', 'Nadlan'),
        ('gis_permit', 'GIS Permit'),
        ('gis_rights', 'GIS Rights'),
        ('rami_plan', 'RAMI Plan'),
        ('tabu', 'Tabu'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='source_records')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    external_id = models.CharField(max_length=100, blank=True, null=True)
    title = models.CharField(max_length=500, blank=True, null=True)
    url = models.URLField(max_length=500, blank=True, null=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    raw = models.JSONField(default=dict)
    fetched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['asset']),
            models.Index(fields=['source']),
            models.Index(fields=['external_id']),
        ]
        unique_together = ['source', 'external_id']
    
    def __str__(self):
        return f"SourceRecord({self.source}, {self.external_id})"

class RealEstateTransaction(models.Model):
    """Real estate transaction model for storing deal data."""
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='transactions')
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
            models.Index(fields=['asset']),
            models.Index(fields=['deal_id']),
        ]
    
    def __str__(self):
        return f"Transaction({self.deal_id}, {self.price})"

class Report(models.Model):
    """Report model for storing generated report metadata."""
    REPORT_TYPE_CHOICES = [
        ('asset', 'Asset Report'),
        ('market', 'Market Report'),
        ('investment', 'Investment Analysis'),
        ('comparison', 'Property Comparison'),
    ]
    
    STATUS_CHOICES = [
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES, default='asset')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    
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
    meta = models.JSONField(default=dict)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['asset']),
            models.Index(fields=['report_type']),
            models.Index(fields=['status']),
            models.Index(fields=['generated_at']),
        ]
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"Report({self.id}, {self.report_type}, {self.status})"
    
    @property
    def file_url(self):
        """Return the URL to access the report file.

        Reports are stored in the front-end ``public/reports`` directory which
        is served directly at ``/reports``.  The previous implementation
        returned a URL under ``/media`` which does not exist in the Next.js
        application, causing generated reports to return 404 when users tried
        to open them.  By pointing to ``/reports`` we align the URL with the
        actual file location.
        """

        return f"/reports/{self.filename}"
    
    def mark_completed(self, file_size=None, pages=None, generation_time=None):
        """Mark the report as completed with metadata."""
        self.status = 'completed'
        if file_size is not None:
            self.file_size = file_size
        if pages is not None:
            self.pages = pages
        if generation_time is not None:
            self.generation_time = generation_time
        self.save()
    
    def mark_failed(self, error_message):
        """Mark the report as failed with error message."""
        self.status = 'failed'
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
            print(f"Error deleting report {self.id}: {e}")
            return False
