from rest_framework import serializers
from .models import Asset, Permit, Plan, SupportTicket, ConsultationRequest, AlertRule, AlertEvent, Snapshot, AssetContribution, UserProfile, PlanType, UserPlan


class MetaSerializerMixin(serializers.ModelSerializer):
    """Adds _meta section with field lineage information."""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        meta = getattr(instance, "meta", {}) or {}
        field_meta = {}
        
        # Extract values and attribution information from meta field
        for key, value in meta.items():
            if isinstance(value, dict):
                # Extract the actual value if it exists
                actual_value = value.get("value")
                if actual_value is not None:
                    data[key] = actual_value
                
                # Extract attribution information
                source = value.get("source")
                fetched = value.get("fetched_at") or value.get("fetchedAt")
                url = value.get("url")
                if source and fetched and url:
                    field_meta[key] = {"source": source, "fetched_at": fetched, "url": url}
                elif source and fetched:
                    field_meta[key] = {"source": source, "fetched_at": fetched}
        
        # Add _meta section if we have attribution data
        if field_meta:
            data["_meta"] = field_meta
            
        return data


class AssetSerializer(MetaSerializerMixin):
    address = serializers.SerializerMethodField()
    
    def get_address(self, obj):
        """Get formatted address for frontend compatibility."""
        if obj.normalized_address:
            return obj.normalized_address
        else:
            # Build address from components
            parts = []
            if obj.street:
                parts.append(obj.street)
            if obj.number:
                parts.append(str(obj.number))
            if obj.building_type and obj.floor:
                parts.append(f"{obj.building_type} {obj.floor}")
            if obj.apartment:
                parts.append(f"דירה {obj.apartment}")
            if obj.city:
                parts.append(obj.city)
            return " ".join(parts) if parts else None
    
    class Meta:
        model = Asset
        fields = [
            'id', 'scope_type', 'city', 'neighborhood', 'street', 'number',
            'gush', 'helka', 'subhelka', 'lat', 'lon', 'normalized_address', 'address', 'status',
                   'building_type', 'floor', 'apartment', 'total_floors', 'rooms', 'bedrooms', 'bathrooms',
            'area', 'total_area', 'balcony_area', 'parking_spaces', 'storage_room',
            'elevator', 'air_conditioning', 'furnished', 'renovated', 'year_built',
            'last_renovation', 'price', 'price_per_sqm', 'rent_estimate', 'zoning',
            'building_rights', 'permit_status', 'permit_date', 'is_demo',
            'last_enriched_at', 'created_at', 'created_by', 'last_updated_by'
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


class AssetContributionSerializer(serializers.ModelSerializer):
    """Serializer for AssetContribution model."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    contribution_type_display = serializers.SerializerMethodField()
    
    def get_contribution_type_display(self, obj):
        """Return Hebrew translation for contribution type."""
        translations = {
            'creation': 'יצירת נכס',
            'enrichment': 'העשרת נתונים',
            'verification': 'אימות נתונים',
            'update': 'עדכון שדה',
            'source_add': 'הוספת מקור',
            'comment': 'הערה/תגובה'
        }
        return translations.get(obj.contribution_type, obj.get_contribution_type_display())
    
    class Meta:
        model = AssetContribution
        fields = [
            'id', 'asset', 'user', 'user_email', 'user_first_name', 'user_last_name',
            'contribution_type', 'contribution_type_display', 'field_name',
            'old_value', 'new_value', 'source', 'description', 'created_at'
        ]
        read_only_fields = ('id', 'created_at')


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_email', 'user_first_name', 'user_last_name',
            'assets_created', 'assets_updated', 'contributions_made',
            'data_points_added', 'sources_contributed', 'reputation_score',
            'verification_count', 'helpful_votes', 'show_attribution',
            'public_profile', 'contribution_notifications', 'created_at',
            'updated_at', 'last_contribution_at'
        ]
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class AssetWithAttributionSerializer(AssetSerializer):
    """Enhanced Asset serializer with attribution information."""
    
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    last_updated_by_email = serializers.CharField(source='last_updated_by.email', read_only=True)
    last_updated_by_name = serializers.SerializerMethodField()
    contributions = AssetContributionSerializer(many=True, read_only=True)
    contribution_count = serializers.SerializerMethodField()
    
    class Meta(AssetSerializer.Meta):
        fields = AssetSerializer.Meta.fields + [
            'created_by', 'created_by_email', 'created_by_name',
            'last_updated_by', 'last_updated_by_email', 'last_updated_by_name',
            'contributions', 'contribution_count'
        ]
    
    def get_created_by_name(self, obj):
        """Get full name of the user who created the asset."""
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.email
        return None
    
    def get_last_updated_by_name(self, obj):
        """Get full name of the user who last updated the asset."""
        if obj.last_updated_by:
            return f"{obj.last_updated_by.first_name} {obj.last_updated_by.last_name}".strip() or obj.last_updated_by.email
        return None
    
    def get_contribution_count(self, obj):
        """Get total number of contributions for this asset."""
        return obj.contributions.count()


class PlanTypeSerializer(serializers.ModelSerializer):
    """Serializer for plan types."""
    
    class Meta:
        model = PlanType
        fields = [
            'id', 'name', 'display_name', 'description', 'price', 'currency', 'billing_period',
            'asset_limit', 'report_limit', 'alert_limit', 'advanced_analytics', 'data_export',
            'api_access', 'priority_support', 'custom_reports', 'is_active'
        ]


class UserPlanSerializer(serializers.ModelSerializer):
    """Serializer for user plans."""
    plan_type = PlanTypeSerializer(read_only=True)
    is_expired = serializers.SerializerMethodField()
    remaining_assets = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPlan
        fields = [
            'id', 'plan_type', 'is_active', 'started_at', 'expires_at', 'auto_renew',
            'last_payment_at', 'next_payment_at', 'assets_used', 'reports_used', 'alerts_used',
            'is_expired', 'remaining_assets'
        ]
    
    def get_is_expired(self, obj):
        """Check if the plan has expired."""
        return obj.is_expired()
    
    def get_remaining_assets(self, obj):
        """Get remaining asset slots."""
        return obj.get_remaining_assets()


class UserPlanInfoSerializer(serializers.Serializer):
    """Serializer for comprehensive user plan information."""
    plan_name = serializers.CharField()
    display_name = serializers.CharField()
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    billing_period = serializers.CharField()
    is_active = serializers.BooleanField()
    is_expired = serializers.BooleanField()
    expires_at = serializers.DateTimeField(allow_null=True)
    limits = serializers.DictField()
    features = serializers.DictField()
