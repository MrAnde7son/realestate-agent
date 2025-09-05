from django.contrib import admin
from .models import SupportTicket, ConsultationRequest


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "user", "severity", "status", "created_at", "subject")
    list_filter = ("kind", "severity", "status", "created_at")
    search_fields = ("subject", "message", "user__email")


@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "phone", "channel", "status", "created_at")
    list_filter = ("channel", "status", "created_at")
    search_fields = ("full_name", "email", "phone", "topic")
