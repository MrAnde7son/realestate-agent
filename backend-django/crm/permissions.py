from rest_framework.permissions import BasePermission


class IsOwnerContact(BasePermission):
    """Permission class to ensure user owns the contact or lead."""
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access the object."""
        if hasattr(obj, "owner"):
            # Direct contact access
            return obj.owner_id == request.user.id
        elif hasattr(obj, "contact"):
            # Lead access - check contact ownership
            return obj.contact.owner_id == request.user.id
        return False
    
    def has_permission(self, request, view):
        """Check if user has permission for the view."""
        return request.user.is_authenticated
