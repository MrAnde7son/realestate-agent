from rest_framework import serializers
from .models import Asset, Permit, Plan


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
                if source and fetched:
                    field_meta[key] = {"source": source, "fetched_at": fetched}
        if field_meta:
            data["_meta"] = field_meta
        return data


class AssetSerializer(MetaSerializerMixin):
    class Meta:
        model = Asset
        fields = [
            'id', 'scope_type', 'city', 'neighborhood', 'street', 'number',
            'gush', 'helka', 'lat', 'lon', 'normalized_address', 'status'
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
