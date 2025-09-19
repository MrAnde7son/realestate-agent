from django.contrib import admin
from .models import Contact, Lead


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'owner', 'created_at']
    list_filter = ['created_at', 'owner']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['contact', 'asset', 'status', 'last_activity_at', 'created_at']
    list_filter = ['status', 'created_at', 'last_activity_at']
    search_fields = ['contact__name', 'contact__email', 'asset__street']
    readonly_fields = ['created_at', 'last_activity_at']