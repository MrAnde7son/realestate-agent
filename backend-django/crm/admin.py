from django.contrib import admin
from .models import (
    Contact,
    Lead,
    ContactTask,
    ContactMeeting,
    ContactInteraction,
)


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


@admin.register(ContactTask)
class ContactTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'contact', 'owner', 'status', 'due_at', 'created_at']
    list_filter = ['status', 'due_at', 'owner']
    search_fields = ['title', 'description', 'contact__name']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']


@admin.register(ContactMeeting)
class ContactMeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'contact', 'owner', 'scheduled_for', 'status']
    list_filter = ['status', 'scheduled_for', 'owner']
    search_fields = ['title', 'contact__name', 'location']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ContactInteraction)
class ContactInteractionAdmin(admin.ModelAdmin):
    list_display = ['interaction_type', 'contact', 'owner', 'occurred_at', 'subject']
    list_filter = ['interaction_type', 'occurred_at', 'owner']
    search_fields = ['subject', 'notes', 'contact__name']
    readonly_fields = ['created_at', 'updated_at']