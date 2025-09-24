import ast
import json

from rest_framework import serializers

from .models import (
    Contact,
    Lead,
    LeadStatus,
    ContactTask,
    ContactTaskStatus,
    ContactMeeting,
    ContactMeetingStatus,
    ContactInteraction,
    InteractionType,
)


def _extract_list_from_request(serializer, field_name):
    """Extract list values for ``field_name`` from the incoming request if possible."""

    request = serializer.context.get("request") if serializer else None
    if not request:
        return None

    data = getattr(request, "data", None)
    if data is None or not hasattr(data, "getlist"):
        return None

    values = data.getlist(field_name)
    if not values:
        return []

    return values


def _coerce_json_like_value(value):
    """Coerce string representations of JSON/collections into Python objects."""

    if isinstance(value, (list, dict)) or value is None:
        return value

    if isinstance(value, str):
        candidate = value.strip()
        if candidate == "":
            return []

        try:
            return json.loads(candidate)
        except (ValueError, TypeError):
            try:
                return ast.literal_eval(candidate)
            except (ValueError, SyntaxError, NameError):
                return value

    return value


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model."""

    tags = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True, default=list
    )
    equity = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        coerce_to_string=False
    )

    class Meta:
        model = Contact
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "equity",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_internal_value(self, data):
        """Ensure tags are consistently treated as a list when submitted via forms."""

        mutable_data = dict(data.items()) if hasattr(data, "items") else dict(data)
        request_tags = _extract_list_from_request(self, "tags")
        if request_tags:
            mutable_data["tags"] = request_tags
        else:
            raw_tags = mutable_data.get("tags")
            if isinstance(raw_tags, str):
                coerced = _coerce_json_like_value(raw_tags)
                if isinstance(coerced, list):
                    mutable_data["tags"] = coerced
                elif coerced in ("", None):
                    mutable_data["tags"] = []
                else:
                    mutable_data["tags"] = [str(coerced)]

        return super().to_internal_value(mutable_data)


class LeadSerializer(serializers.ModelSerializer):
    """Serializer for Lead model."""
    
    contact = ContactSerializer(read_only=True)
    contact_id = serializers.IntegerField(source="contact.id", read_only=True)
    contact_id_write = serializers.PrimaryKeyRelatedField(
        write_only=True, 
        queryset=Contact.objects.all(), 
        source="contact"
    )
    asset_id = serializers.IntegerField(write_only=True)
    
    asset = serializers.SerializerMethodField(read_only=True)
    asset_address = serializers.CharField(source="asset.address", read_only=True)
    asset_price = serializers.IntegerField(source="asset.price", read_only=True)
    asset_rooms = serializers.IntegerField(source="asset.rooms", read_only=True)
    asset_area = serializers.FloatField(source="asset.area", read_only=True)

    class Meta:
        model = Lead
        fields = [
            "id", "contact", "contact_id", "contact_id_write", "asset", "asset_id", "asset_address",
            "asset_price", "asset_rooms", "asset_area", "status", "notes",
            "last_activity_at", "created_at"
        ]
        read_only_fields = ["id", "last_activity_at", "created_at"]

    def to_internal_value(self, data):
        """Normalise notes submitted through multipart requests."""

        mutable_data = dict(data.items()) if hasattr(data, "items") else dict(data)
        request_notes = _extract_list_from_request(self, "notes")
        if request_notes:
            coerced = [_coerce_json_like_value(item) for item in request_notes]
            if len(coerced) == 1 and isinstance(coerced[0], list):
                mutable_data["notes"] = coerced[0]
            else:
                mutable_data["notes"] = coerced
        else:
            raw_notes = mutable_data.get("notes")
            if isinstance(raw_notes, str):
                coerced = _coerce_json_like_value(raw_notes)
                if isinstance(coerced, list):
                    mutable_data["notes"] = coerced
                elif isinstance(coerced, dict):
                    mutable_data["notes"] = [coerced]
                elif coerced in ("", None):
                    mutable_data["notes"] = []
                else:
                    mutable_data["notes"] = [coerced]

        return super().to_internal_value(mutable_data)

    def get_asset(self, obj):
        """Get asset information for the lead."""
        if obj.asset:
            return {
                'id': obj.asset.id,
                'address': obj.asset.address,
                'price': obj.asset.price,
                'rooms': obj.asset.rooms,
                'area': obj.asset.area,
                'city': obj.asset.city,
                'street': obj.asset.street,
                'number': obj.asset.number
            }
        return None

    def validate_asset_id(self, value):
        """Validate that the asset exists and user has permission."""
        from core.models import Asset
        try:
            asset = Asset.objects.get(id=value)
            # For now, just check if user created the asset or has access
            # This can be enhanced based on existing permission system
            if hasattr(self.context.get('request'), 'user') and asset.created_by_id != self.context['request'].user.id:
                raise serializers.ValidationError("No permission on this asset")
        except Asset.DoesNotExist:
            raise serializers.ValidationError("Asset not found")
        return value

    def validate(self, attrs):
        """Validate lead data."""
        user = self.context["request"].user
        contact = attrs.get("contact")
        
        # Check contact ownership if contact exists
        if contact and contact.owner_id != user.id:
            raise serializers.ValidationError("No permission on this contact")
        
        return attrs


class LeadStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating lead status."""
    
    status = serializers.ChoiceField(choices=LeadStatus.choices)


class LeadNoteSerializer(serializers.Serializer):
    """Serializer for adding notes to leads."""

    text = serializers.CharField(max_length=1000, allow_blank=True)


class ContactTaskSerializer(serializers.ModelSerializer):
    """Serializer for contact tasks."""

    contact_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=Contact.objects.all(),
        source="contact",
    )
    lead_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=Lead.objects.all(),
        source="lead",
        required=False,
        allow_null=True,
    )
    contact = ContactSerializer(read_only=True)
    lead = LeadSerializer(read_only=True)
    status = serializers.ChoiceField(choices=ContactTaskStatus.choices, required=False)

    class Meta:
        model = ContactTask
        fields = [
            "id",
            "title",
            "description",
            "due_at",
            "status",
            "completed_at",
            "created_at",
            "updated_at",
            "contact",
            "contact_id",
            "lead",
            "lead_id",
        ]
        read_only_fields = ["id", "completed_at", "created_at", "updated_at", "contact", "lead"]

    def validate_contact_id(self, value):
        request = self.context.get("request")
        if request and not request.user.is_superuser and value.owner_id != request.user.id:
            raise serializers.ValidationError("No permission on this contact")
        return value

    def validate_lead_id(self, value):
        request = self.context.get("request")
        if value and request and not request.user.is_superuser and value.contact.owner_id != request.user.id:
            raise serializers.ValidationError("No permission on this lead")
        return value


class ContactMeetingSerializer(serializers.ModelSerializer):
    """Serializer for contact meetings."""

    contact_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=Contact.objects.all(),
        source="contact",
    )
    contact = ContactSerializer(read_only=True)
    status = serializers.ChoiceField(choices=ContactMeetingStatus.choices, required=False)

    class Meta:
        model = ContactMeeting
        fields = [
            "id",
            "title",
            "scheduled_for",
            "duration_minutes",
            "location",
            "status",
            "notes",
            "created_at",
            "updated_at",
            "contact",
            "contact_id",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "contact"]

    def validate_contact_id(self, value):
        request = self.context.get("request")
        if request and not request.user.is_superuser and value.owner_id != request.user.id:
            raise serializers.ValidationError("No permission on this contact")
        return value


class ContactInteractionSerializer(serializers.ModelSerializer):
    """Serializer for contact interactions."""

    contact_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=Contact.objects.all(),
        source="contact",
    )
    contact = ContactSerializer(read_only=True)
    interaction_type = serializers.ChoiceField(choices=InteractionType.choices, required=False)

    class Meta:
        model = ContactInteraction
        fields = [
            "id",
            "interaction_type",
            "subject",
            "notes",
            "occurred_at",
            "next_steps",
            "follow_up_at",
            "created_at",
            "updated_at",
            "contact",
            "contact_id",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "contact"]

    def validate_contact_id(self, value):
        request = self.context.get("request")
        if request and not request.user.is_superuser and value.owner_id != request.user.id:
            raise serializers.ValidationError("No permission on this contact")
        return value
