"""Custom authentication backend for API tokens."""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone

from .models import APIToken


class APITokenAuthentication(BaseAuthentication):
    """Authentication backend that accepts API tokens."""
    
    def authenticate(self, request):
        """Authenticate using API token from Authorization header."""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1] if len(auth_header.split(' ')) > 1 else None
        
        if not token:
            return None
        
        # Skip JWT tokens (they have 3 parts separated by dots)
        # API tokens are URL-safe base64 strings without dots
        if token.count('.') == 2:
            # This looks like a JWT token, let JWT authentication handle it
            return None
        
        try:
            api_token = APIToken.objects.select_related('user').get(token=token)
            
            # Check if token is valid
            if not api_token.is_valid():
                raise AuthenticationFailed('Token is expired or inactive')
            
            # Update last_used_at
            api_token.last_used_at = timezone.now()
            api_token.save(update_fields=['last_used_at'])
            
            return (api_token.user, None)
        except APIToken.DoesNotExist:
            # Let JWT authentication handle it if API token doesn't exist
            return None
        except Exception as e:
            raise AuthenticationFailed(f'Invalid token: {str(e)}')

