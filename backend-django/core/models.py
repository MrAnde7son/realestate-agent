from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model

class User(AbstractUser):
    """Custom user model for the real estate application."""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=50, blank=True, null=True)  # broker, appraiser, investor, etc.
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    normalized_address = models.CharField(max_length=500, blank=True, null=True)
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
            models.Index(fields=['normalized_address']),
            models.Index(fields=['status']),
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
