from rest_framework import serializers
from .models import Contact, Lead, LeadStatus


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model."""
    
    tags = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = Contact
        fields = ["id", "name", "phone", "email", "tags", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class LeadSerializer(serializers.ModelSerializer):
    """Serializer for Lead model."""
    
    contact = ContactSerializer(read_only=True)
    contact_id = serializers.PrimaryKeyRelatedField(
        write_only=True, 
        queryset=Contact.objects.all(), 
        source="contact"
    )
    asset_id = serializers.IntegerField(write_only=True)
    asset_address = serializers.CharField(source="asset.address", read_only=True)
    asset_price = serializers.IntegerField(source="asset.price", read_only=True)
    asset_rooms = serializers.IntegerField(source="asset.rooms", read_only=True)
    asset_area = serializers.FloatField(source="asset.area", read_only=True)

    class Meta:
        model = Lead
        fields = [
            "id", "contact", "contact_id", "asset_id", "asset_address", 
            "asset_price", "asset_rooms", "asset_area", "status", "notes",
            "last_activity_at", "created_at"
        ]
        read_only_fields = ["id", "last_activity_at", "created_at"]

    def validate(self, attrs):
        """Validate lead data."""
        user = self.context["request"].user
        contact = attrs["contact"]
        
        # Check contact ownership
        if contact.owner_id != user.id:
            raise serializers.ValidationError("No permission on this contact")
        
        # Check asset access (basic check - can be enhanced based on existing ACL)
        from core.models import Asset
        try:
            asset = Asset.objects.get(id=attrs["asset_id"])
            # For now, just check if user created the asset or has access
            # This can be enhanced based on existing permission system
            if asset.created_by_id != user.id:
                raise serializers.ValidationError("No permission on this asset")
        except Asset.DoesNotExist:
            raise serializers.ValidationError("Asset not found")
        
        return attrs


class LeadStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating lead status."""
    
    status = serializers.ChoiceField(choices=LeadStatus.choices)


class LeadNoteSerializer(serializers.Serializer):
    """Serializer for adding notes to leads."""
    
    text = serializers.CharField(max_length=1000, min_length=1)
