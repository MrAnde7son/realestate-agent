from rest_framework import serializers
from .models import Asset, Permit, Plan, SupportTicket, ConsultationRequest, AlertRule, AlertEvent, Snapshot


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


class AlertRuleSerializer(serializers.ModelSerializer):
    """Serializer for AlertRule model."""
    
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    
    class Meta:
        model = AlertRule
        fields = [
            'id', 'user', 'scope', 'asset', 'trigger_type', 'trigger_type_display',
            'params', 'channels', 'frequency', 'frequency_display', 'scope_display',
            'active', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def validate_channels(self, value):
        """Validate that channels are valid options."""
        valid_channels = ['email', 'whatsapp']
        for channel in value:
            if channel not in valid_channels:
                raise serializers.ValidationError(f"Invalid channel: {channel}. Must be one of {valid_channels}")
        return value
    
    def validate_params(self, value):
        """Validate parameters based on trigger type."""
        trigger_type = self.initial_data.get('trigger_type')
        
        if trigger_type == 'PRICE_DROP':
            pct = value.get('pct', 3)
            if not isinstance(pct, (int, float)) or pct < 0 or pct > 100:
                raise serializers.ValidationError("Price drop percentage must be between 0 and 100")
        
        elif trigger_type == 'MARKET_TREND':
            delta_pct = value.get('delta_pct', 5)
            window_days = value.get('window_days', 30)
            radius_km = value.get('radius_km', 1.0)
            
            if not isinstance(delta_pct, (int, float)) or delta_pct < 0 or delta_pct > 100:
                raise serializers.ValidationError("Market trend delta percentage must be between 0 and 100")
            if not isinstance(window_days, int) or window_days < 7 or window_days > 180:
                raise serializers.ValidationError("Window days must be between 7 and 180")
            if not isinstance(radius_km, (int, float)) or radius_km < 0.1 or radius_km > 5:
                raise serializers.ValidationError("Radius must be between 0.1 and 5 km")
        
        elif trigger_type == 'NEW_GOV_TX':
            radius_m = value.get('radius_m', 500)
            if not isinstance(radius_m, (int, float)) or radius_m < 50 or radius_m > 2000:
                raise serializers.ValidationError("Radius must be between 50 and 2000 meters")
        
        elif trigger_type == 'LISTING_REMOVED':
            misses = value.get('misses', 2)
            if not isinstance(misses, int) or misses < 1 or misses > 10:
                raise serializers.ValidationError("Misses must be between 1 and 10")
        
        return value
    
    def validate(self, data):
        """Validate that asset is provided when scope is 'asset'."""
        if data.get('scope') == 'asset' and not data.get('asset'):
            raise serializers.ValidationError("Asset must be provided when scope is 'asset'")
        return data


class AlertEventSerializer(serializers.ModelSerializer):
    """Serializer for AlertEvent model."""
    
    alert_rule = AlertRuleSerializer(read_only=True)
    asset_address = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertEvent
        fields = [
            'id', 'alert_rule', 'asset', 'asset_address', 'occurred_at',
            'payload', 'delivered_at', 'digest_id'
        ]
        read_only_fields = ('id', 'occurred_at', 'delivered_at', 'digest_id')
    
    def get_asset_address(self, obj):
        """Get formatted asset address."""
        if obj.asset:
            return obj.asset.normalized_address or f"{obj.asset.street} {obj.asset.number}, {obj.asset.city}"
        return None


class SnapshotSerializer(serializers.ModelSerializer):
    """Serializer for Snapshot model."""
    
    class Meta:
        model = Snapshot
        fields = ['id', 'asset', 'payload', 'ppsqm', 'created_at']
        read_only_fields = ('id', 'created_at')
