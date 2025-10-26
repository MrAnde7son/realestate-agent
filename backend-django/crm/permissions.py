from rest_framework.permissions import BasePermission


def has_global_crm_access(user) -> bool:
    """Return True when the user should have unrestricted CRM access."""
    role = getattr(user, "role", "")
    if isinstance(role, str):
        role = role.strip().lower()
    return user.is_superuser or user.is_staff or role == "admin"


class HasCrmAccess(BasePermission):
    """Ensure only brokers and appraisers can access CRM features."""

    message = "גישה מותרת למתווכים ושמאים בלבד."

    allowed_roles = {"broker", "appraiser", "admin"}

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if has_global_crm_access(request.user):
            return True

        role = getattr(request.user, "role", None)
        if isinstance(role, str):
            role = role.strip().lower()
        return role in self.allowed_roles

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsOwnerContact(BasePermission):
    """Permission class to ensure user owns the contact or lead."""
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access the object."""
        # Allow superusers to access any object
        user = request.user
        if has_global_crm_access(user):
            return True
            
        if hasattr(obj, "owner"):
            # Direct contact access
            return obj.owner_id == user.id
        elif hasattr(obj, "contact"):
            # Lead access - check contact ownership
            return obj.contact.owner_id == user.id
        return False
    
    def has_permission(self, request, view):
        """Check if user has permission for the view."""
        return request.user.is_authenticated
