from django.contrib import admin

from .models import (
    SupportTicket,
    ConsultationRequest,
    Asset,
    Document,
    RealEstateTransaction,
    Permit,
    Plan,
    Listing,
    AssetDocument,
    AssetTransaction,
    AssetListing,
    AssetPermit,
    AssetPlan,
)


class AssetDocumentInline(admin.TabularInline):
    model = AssetDocument
    extra = 0
    autocomplete_fields = ['asset', 'document']


class AssetTransactionInline(admin.TabularInline):
    model = AssetTransaction
    extra = 0
    autocomplete_fields = ['asset', 'transaction']


class AssetListingInline(admin.TabularInline):
    model = AssetListing
    extra = 0
    autocomplete_fields = ['asset', 'listing']


class AssetPermitInline(admin.TabularInline):
    model = AssetPermit
    extra = 0
    autocomplete_fields = ['asset', 'permit']


class AssetPlanInline(admin.TabularInline):
    model = AssetPlan
    extra = 0
    autocomplete_fields = ['asset', 'plan']


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


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    inlines = [
        AssetDocumentInline,
        AssetTransactionInline,
        AssetPermitInline,
        AssetPlanInline,
        AssetListingInline,
    ]
    search_fields = ('id', 'address', 'city', 'street', 'parcel')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    inlines = [AssetDocumentInline]
    search_fields = ('id', 'title', 'external_id')


@admin.register(RealEstateTransaction)
class RealEstateTransactionAdmin(admin.ModelAdmin):
    inlines = [AssetTransactionInline]
    search_fields = ('id', 'deal_id')


@admin.register(Permit)
class PermitAdmin(admin.ModelAdmin):
    inlines = [AssetPermitInline]
    search_fields = ('id', 'permit_number')


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    inlines = [AssetPlanInline]
    search_fields = ('id', 'plan_number', 'title')


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    inlines = [AssetListingInline]
    list_display = (
        "source",
        "external_id",
        "status",
        "listing_type",
        "ad_type",
        "price",
        "rooms",
        "area",
        "contact_name",
        "contact_phone",
        "recent_deal",
        "photos_count",
        "has_video",
        "fetched_at",
    )
    search_fields = ("external_id", "title", "address")
    list_filter = ("source", "status", "listing_type", "ad_type")

    @admin.display(description="Photos")
    def photos_count(self, obj):
        photos = obj.photos or []
        return len(photos)

    @admin.display(boolean=True, description="Video")
    def has_video(self, obj):
        return bool(obj.video_url)
