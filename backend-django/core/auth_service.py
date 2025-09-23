import json
from decimal import Decimal, InvalidOperation
import urllib.parse
import requests
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()

ALLOWED_REGISTRATION_ROLES = {
    User.Role.BROKER,
    User.Role.APPRAISER,
    User.Role.PRIVATE,
}

DEFAULT_REGISTRATION_ROLE = User.Role.PRIVATE


class AuthenticationService:
    """Service class for handling authentication operations."""
    
    def __init__(self, settings_module):
        self.settings = settings_module
    
    def authenticate_user(self, email: str, password: str) -> dict:
        """Authenticate a user with email and password."""
        try:
            # Authenticate user
            user = authenticate(username=email, password=password)
            
            if user is None:
                return {
                    'success': False,
                    'error': 'Invalid credentials',
                    'status': status.HTTP_401_UNAUTHORIZED
                }
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return {
                'success': True,
                'data': {
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'user': self._get_user_data(user)
                },
                'status': status.HTTP_200_OK
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    def register_user(self, user_data: dict) -> dict:
        """Register a new user."""
        try:
            email = user_data.get('email')
            password = user_data.get('password')
            username = user_data.get('username')
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            company = user_data.get('company', '')
            requested_role = user_data.get('role')
            raw_equity = user_data.get('equity')
            role = (
                requested_role
                if requested_role in ALLOWED_REGISTRATION_ROLES
                else str(DEFAULT_REGISTRATION_ROLE)
            )

            equity = None
            if role == str(User.Role.PRIVATE) and raw_equity not in (None, ""):
                try:
                    equity = Decimal(str(raw_equity))
                except (InvalidOperation, TypeError):
                    return {
                        'success': False,
                        'error': 'Equity must be a valid number',
                        'status': status.HTTP_400_BAD_REQUEST
                    }
                if equity < 0:
                    return {
                        'success': False,
                        'error': 'Equity must be a non-negative amount',
                        'status': status.HTTP_400_BAD_REQUEST
                    }
            
            if not email or not password or not username:
                return {
                    'success': False,
                    'error': 'Email, password, and username are required',
                    'status': status.HTTP_400_BAD_REQUEST
                }
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                return {
                    'success': False,
                    'error': 'User with this email already exists',
                    'status': status.HTTP_400_BAD_REQUEST
                }
            
            if User.objects.filter(username=username).exists():
                return {
                    'success': False,
                    'error': 'Username already taken',
                    'status': status.HTTP_400_BAD_REQUEST
                }
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                company=company,
                role=role,
                equity=equity,
            )
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return {
                'success': True,
                'data': {
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'user': self._get_user_data(user)
                },
                'status': status.HTTP_201_CREATED
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    def refresh_token(self, refresh_token: str) -> dict:
        """Refresh JWT token."""
        try:
            if not refresh_token:
                return {
                    'success': False,
                    'error': 'Refresh token is required',
                    'status': status.HTTP_400_BAD_REQUEST
                }
            
            # Verify and refresh token
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
            return {
                'success': True,
                'data': {
                    'access_token': access_token,
                    'refresh_token': str(refresh),
                },
                'status': status.HTTP_200_OK
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': status.HTTP_401_UNAUTHORIZED
            }
    
    def get_user_profile(self, user) -> dict:
        """Get user profile data."""
        try:
            return {
                'success': True,
                'data': {
                    'user': self._get_user_data(user)
                },
                'status': status.HTTP_200_OK
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    def update_user_profile(self, user, profile_data: dict) -> dict:
        """Update user profile."""
        try:
            # Update allowed fields
            if 'first_name' in profile_data:
                user.first_name = profile_data['first_name']
            if 'last_name' in profile_data:
                user.last_name = profile_data['last_name']
            if 'company' in profile_data:
                user.company = profile_data['company']
            if 'role' in profile_data:
                user.role = profile_data['role']
            if 'equity' in profile_data:
                raw_equity = profile_data['equity']
                if raw_equity in (None, ""):
                    user.equity = None
                else:
                    try:
                        equity_value = Decimal(str(raw_equity))
                    except (InvalidOperation, TypeError):
                        raise ValueError('Equity must be a valid number')
                    if equity_value < 0:
                        raise ValueError('Equity must be a non-negative amount')
                    user.equity = equity_value

            user.save()

            return {
                'success': True,
                'data': {
                    'user': self._get_user_data(user)
                },
                'status': status.HTTP_200_OK
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    def change_password(self, user, current_password: str, new_password: str) -> dict:
        """Change user password."""
        try:
            if not current_password or not new_password:
                return {
                    'success': False,
                    'error': 'Current password and new password are required',
                    'status': status.HTTP_400_BAD_REQUEST
                }
            
            if len(new_password) < 8:
                return {
                    'success': False,
                    'error': 'New password must be at least 8 characters long',
                    'status': status.HTTP_400_BAD_REQUEST
                }
            
            # Verify current password
            if not user.check_password(current_password):
                return {
                    'success': False,
                    'error': 'Current password is incorrect',
                    'status': status.HTTP_400_BAD_REQUEST
                }
            
            # Check if new password is different from current
            if user.check_password(new_password):
                return {
                    'success': False,
                    'error': 'New password must be different from current password',
                    'status': status.HTTP_400_BAD_REQUEST
                }
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            return {
                'success': True,
                'data': {
                    'message': 'Password changed successfully'
                },
                'status': status.HTTP_200_OK
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    def get_google_auth_url(self, request) -> dict:
        """Get Google OAuth URL."""
        try:
            redirect_uri = self._build_callback_url(request)
            params = {
                'client_id': self.settings.GOOGLE_CLIENT_ID,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'scope': 'openid email profile',
                'access_type': 'offline',
                'prompt': 'consent',
            }
            
            auth_url = f"{self.settings.GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
            
            return {
                'success': True,
                'data': {
                    'auth_url': auth_url
                },
                'status': status.HTTP_200_OK
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    def handle_google_callback(self, request, frontend_url: str) -> dict:
        """Handle Google OAuth callback."""
        try:
            # Get authorization code from query parameters
            code = request.GET.get('code')
            if not code:
                return {
                    'success': False,
                    'error': 'Authorization code not provided',
                    'status': status.HTTP_400_BAD_REQUEST
                }
            
            redirect_uri = self._build_callback_url(request)
            token_data = {
                'client_id': self.settings.GOOGLE_CLIENT_ID,
                'client_secret': self.settings.GOOGLE_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri,
            }
            
            token_response = requests.post(self.settings.GOOGLE_TOKEN_URL, data=token_data, timeout=10)
            token_info = token_response.json()
            
            if token_response.status_code != 200:
                return {
                    'success': False,
                    'error': 'Failed to get access token from Google',
                    'data': token_info,
                    'status': status.HTTP_400_BAD_REQUEST
                }
            
            access_token = token_info.get('access_token')
            
            # Get user info from Google
            user_info_response = requests.get(
                self.settings.GOOGLE_USER_INFO_URL,
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if not user_info_response.ok:
                return {
                    'success': False,
                    'error': 'Failed to get user info from Google',
                    'status': status.HTTP_400_BAD_REQUEST
                }
            
            user_info = user_info_response.json()
            google_id = user_info.get('id')
            email = user_info.get('email')
            first_name = user_info.get('given_name', '')
            last_name = user_info.get('family_name', '')
            
            if not email:
                return {
                    'success': False,
                    'error': 'Email not provided by Google',
                    'status': status.HTTP_400_BAD_REQUEST
                }
            
            # Check if user exists, create if not
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Create new user
                username = email.split('@')[0]  # Use email prefix as username
                # Ensure username is unique
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=make_password(None),  # No password for OAuth users
                    first_name=first_name,
                    last_name=last_name,
                    is_verified=True  # Google users are verified
                )
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            tokens = {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': self._get_user_data(user)
            }
            
            # Encode tokens in URL parameters
            encoded_tokens = urllib.parse.urlencode(tokens)
            redirect_url = f"{frontend_url}/auth/google-callback?{encoded_tokens}"
            
            return {
                'success': True,
                'data': {
                    'redirect_url': redirect_url,
                    'tokens': tokens
                },
                'status': status.HTTP_200_OK
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    def _get_user_data(self, user) -> dict:
        """Extract user data for API responses."""
        return {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'company': getattr(user, 'company', ''),
            'role': getattr(user, 'role', ''),
            'equity': float(user.equity) if getattr(user, 'equity', None) is not None else None,
            'is_verified': getattr(user, 'is_verified', False),
            'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None,
            'language': getattr(user, 'language', ''),
            'timezone': getattr(user, 'timezone', ''),
            'currency': getattr(user, 'currency', ''),
            'date_format': getattr(user, 'date_format', ''),
            'notify_email': getattr(user, 'notify_email', False),
            'notify_whatsapp': getattr(user, 'notify_whatsapp', False),
            'notify_urgent': getattr(user, 'notify_urgent', False),
            'notification_time': getattr(user, 'notification_time', ''),
        }
    
    def _build_callback_url(self, request) -> str:
        """Build absolute callback URL for Google OAuth."""
        from django.urls import reverse
        return request.build_absolute_uri(reverse('auth_google_callback'))
