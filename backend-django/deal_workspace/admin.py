from django.contrib import admin

from . import models


@admin.register(models.Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "asset",
        "stage",
        "deal_lead",
        "confidentiality_level",
        "created_at",
    )
    list_filter = ("stage", "confidentiality_level")
    search_fields = ("asset__id", "deal_lead__email")
    autocomplete_fields = ("asset",)


@admin.register(models.PartyRole)
class PartyRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "deal", "role", "side", "user", "invitation_status")
    list_filter = ("role", "side", "invitation_status")
    search_fields = ("user__email", "external_contact_json__name")
    autocomplete_fields = ("deal",)


@admin.register(models.Negotiation)
class NegotiationAdmin(admin.ModelAdmin):
    list_display = ("id", "deal", "status", "current_offer", "created_at")
    list_filter = ("status",)
    search_fields = ("deal__id",)
    autocomplete_fields = ("deal", "current_offer")


class OfferAttachmentInline(admin.TabularInline):
    model = models.OfferAttachment
    extra = 0


@admin.register(models.Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "negotiation",
        "submitted_by",
        "amount",
        "status",
        "expiration_at",
    )
    list_filter = ("status", "financing_type")
    search_fields = ("negotiation__deal__id", "submitted_by__user__email")
    autocomplete_fields = ("negotiation", "submitted_by")
    inlines = [OfferAttachmentInline]


@admin.register(models.Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "deal",
        "kind",
        "status",
        "visibility_scope",
        "created_at",
    )
    list_filter = ("kind", "status", "visibility_scope")
    search_fields = ("title", "deal__id")
    autocomplete_fields = ("deal", "asset", "uploader_partyrole")


@admin.register(models.LegalCase)
class LegalCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "deal", "responsible_partyrole", "status")
    list_filter = ("status",)
    search_fields = ("deal__id",)
    autocomplete_fields = ("deal", "responsible_partyrole")


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "deal",
        "legalcase",
        "assignee_partyrole",
        "status",
        "due_at",
    )
    list_filter = ("status",)
    search_fields = ("title", "deal__id")
    autocomplete_fields = ("deal", "legalcase", "assignee_partyrole")


@admin.register(models.Appraisal)
class AppraisalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "asset",
        "deal",
        "appraised_value",
        "valuation_date",
        "source",
    )
    list_filter = ("source",)
    search_fields = ("asset__id", "deal__id", "appraiser_name")
    autocomplete_fields = ("asset", "deal")


@admin.register(models.PlanSet)
class PlanSetAdmin(admin.ModelAdmin):
    list_display = ("id", "asset", "architect_partyrole", "status")
    list_filter = ("status",)
    search_fields = ("asset__id",)
    autocomplete_fields = ("asset", "architect_partyrole")


@admin.register(models.MortgageApplication)
class MortgageApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "deal",
        "applicant_partyrole",
        "status",
        "requested_amount",
    )
    list_filter = ("status",)
    search_fields = ("deal__id", "applicant_partyrole__user__email")
    autocomplete_fields = ("deal", "applicant_partyrole")


@admin.register(models.MortgageOffer)
class MortgageOfferAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "mortgageapplication",
        "lender_name",
        "product_type",
        "rate_pct",
        "valid_until",
    )
    list_filter = ("product_type",)
    search_fields = ("mortgageapplication__deal__id", "lender_name")
    autocomplete_fields = ("mortgageapplication",)


@admin.register(models.AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "entity_type",
        "entity_id",
        "action",
        "by_partyrole",
        "created_at",
    )
    list_filter = ("entity_type", "action")
    search_fields = ("entity_id", "action")
    autocomplete_fields = ("by_partyrole",)
