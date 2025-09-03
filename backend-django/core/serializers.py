from rest_framework import serializers
from .models import Asset, Permit, Plan


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            'id', 'scope_type', 'city', 'neighborhood', 'street', 'number',
            'gush', 'helka', 'lat', 'lon', 'normalized_address', 'status'
        ]


class PermitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permit
        fields = [
            'id', 'asset', 'permit_number', 'description', 'status',
            'issued_date', 'expiry_date', 'file_url'
        ]


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id', 'asset', 'plan_number', 'description', 'status',
            'effective_date', 'file_url'
        ]
