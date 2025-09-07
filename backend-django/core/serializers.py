from rest_framework import serializers
from .models import Asset, Permit, Plan, SupportTicket, ConsultationRequest


class MetaSerializerMixin(serializers.ModelSerializer):
    """Adds _meta section with field lineage information."""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        meta = getattr(instance, "meta", {}) or {}
        field_meta = {}
        for key, value in meta.items():
            if isinstance(value, dict):
                source = value.get("source")
                fetched = value.get("fetched_at") or value.get("fetchedAt")
                url = value.get("url")
                if source and fetched and url:
                    field_meta[key] = {"source": source, "fetched_at": fetched, "url": url}
                elif source and fetched:
                    field_meta[key] = {"source": source, "fetched_at": fetched}
        if field_meta:
            data["_meta"] = field_meta
        return data


class AssetSerializer(MetaSerializerMixin):
    size = serializers.SerializerMethodField()
    rights = serializers.SerializerMethodField()
    permits = serializers.SerializerMethodField()
    comps = serializers.SerializerMethodField()

    KEY_FIELDS = ["city", "size", "rights", "permits", "comps"]

    def _get_meta_value(self, obj, field):
        meta = getattr(obj, "meta", {}) or {}
        value = meta.get(field)
        if isinstance(value, dict):
            return value.get("value")
        return None

    def get_size(self, obj):
        return self._get_meta_value(obj, "size")

    def get_rights(self, obj):
        return self._get_meta_value(obj, "rights")

    def get_permits(self, obj):
        return self._get_meta_value(obj, "permits")

    def get_comps(self, obj):
        return self._get_meta_value(obj, "comps")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Override key field values from meta if provided
        meta = getattr(instance, "meta", {}) or {}
        for field in self.KEY_FIELDS:
            meta_val = meta.get(field)
            if isinstance(meta_val, dict) and meta_val.get("value") is not None:
                data[field] = meta_val["value"]
        return data

    class Meta:
        model = Asset
        fields = [
            'id', 'scope_type', 'city', 'neighborhood', 'street', 'number',
            'gush', 'helka', 'lat', 'lon', 'normalized_address', 'status',
            'size', 'rights', 'permits', 'comps'
        ]


class PermitSerializer(MetaSerializerMixin):
    class Meta:
        model = Permit
        fields = [
            'id', 'asset', 'permit_number', 'description', 'status',
            'issued_date', 'expiry_date', 'file_url'
        ]


class PlanSerializer(MetaSerializerMixin):
    class Meta:
        model = Plan
        fields = [
            'id', 'asset', 'plan_number', 'description', 'status',
            'effective_date', 'file_url'
        ]


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "status")


class ConsultationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationRequest
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "status")
