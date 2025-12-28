from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from . import models


class PartyRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PartyRole
        fields = [
            "id",
            "deal",
            "user",
            "external_contact_json",
            "role",
            "side",
            "invitation_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "deal"]


class DealSerializer(serializers.ModelSerializer):
    party_roles = PartyRoleSerializer(many=True, read_only=True)
    asset_summary = serializers.SerializerMethodField()

    class Meta:
        model = models.Deal
        fields = [
            "id",
            "asset",
            "stage",
            "deal_lead",
            "confidentiality_level",
            "closing_date",
            "created_at",
            "updated_at",
            "party_roles",
            "asset_summary",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "party_roles",
            "asset_summary",
        ]

    def get_asset_summary(self, obj):
        asset = getattr(obj, "asset", None)
        if not asset:
            return None

        return {
            "id": asset.pk,
            "address": getattr(asset, "address", None),
            "city": getattr(asset, "city", None),
            "neighborhood": getattr(asset, "neighborhood", None),
            "price": getattr(asset, "price", None),
            "status": getattr(asset, "status", None),
            "building_type": getattr(asset, "building_type", None),
        }


class NegotiationSerializer(serializers.ModelSerializer):
    current_offer = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.Negotiation
        fields = [
            "id",
            "deal",
            "status",
            "visibility_rules",
            "current_offer",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "deal",
            "current_offer",
        ]


class OfferSerializer(serializers.ModelSerializer):
    submitted_by = serializers.PrimaryKeyRelatedField(read_only=True)
    conditions = serializers.JSONField(source="conditions_json")

    class Meta:
        model = models.Offer
        fields = [
            "id",
            "negotiation",
            "submitted_by",
            "amount",
            "currency",
            "financing_type",
            "down_payment_pct",
            "conditions",
            "expiration_at",
            "status",
            "message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "submitted_by",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate_expiration_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Expiration must be in the future")
        return value


class OfferAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OfferAttachment
        fields = ["id", "offer", "document", "created_at"]
        read_only_fields = ["id", "created_at"]


class DocumentSerializer(serializers.ModelSerializer):
    extracted_json = serializers.JSONField(required=False)

    class Meta:
        model = models.Document
        fields = [
            "id",
            "asset",
            "deal",
            "kind",
            "title",
            "storage_url",
            "hash",
            "uploader_partyrole",
            "visibility_scope",
            "extracted_json",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "hash",
            "uploader_partyrole",
            "status",
            "created_at",
            "updated_at",
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AuditLog
        fields = [
            "id",
            "entity_type",
            "entity_id",
            "action",
            "by_partyrole",
            "diff_json",
            "ip",
            "ua",
            "created_at",
        ]
        read_only_fields = fields


class LegalCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LegalCase
        fields = [
            "id",
            "deal",
            "responsible_partyrole",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Task
        fields = [
            "id",
            "legalcase",
            "deal",
            "title",
            "description",
            "assignee_partyrole",
            "due_at",
            "status",
            "checklist_json",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AppraisalSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Appraisal
        fields = [
            "id",
            "asset",
            "deal",
            "appraised_value",
            "valuation_date",
            "appraiser_name",
            "methodology",
            "confidence_score",
            "source",
            "variance_vs_nadlaner_pct",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PlanSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlanSet
        fields = [
            "id",
            "asset",
            "architect_partyrole",
            "status",
            "metadata_json",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MortgageOfferSerializer(serializers.ModelSerializer):
    raw_json = serializers.JSONField(required=False)

    class Meta:
        model = models.MortgageOffer
        fields = [
            "id",
            "mortgageapplication",
            "lender_name",
            "product_type",
            "term_months",
            "rate_pct",
            "apr_estimate_pct",
            "monthly_payment",
            "fees_total",
            "valid_until",
            "score",
            "source",
            "raw_json",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MortgageApplicationSerializer(serializers.ModelSerializer):
    offers = MortgageOfferSerializer(many=True, read_only=True)

    class Meta:
        model = models.MortgageApplication
        fields = [
            "id",
            "deal",
            "applicant_partyrole",
            "status",
            "requested_amount",
            "ltv_pct",
            "income_json",
            "created_at",
            "updated_at",
            "offers",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "offers"]
