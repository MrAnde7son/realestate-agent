from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import uuid

from core.serializers import AdminUserSerializer, AdminUserCreateSerializer, AdminUserUpdateSerializer
from core.admin_views import AdminUserViewSet, IsAdminUser

User = get_user_model()


class AdminUserSerializerTest(TestCase):
    """Test cases for AdminUserSerializer."""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '050-1234567',
            'company': 'Test Company',
            'role': 'broker',
            'is_active': True,
            'is_verified': False,
            'is_demo': False,
            'is_staff': False,
        }
    
    def tearDown(self):
        """Clean up after each test."""
        User.objects.all().delete()
    
    def test_create_user_serializer(self):
        """Test creating a user with AdminUserCreateSerializer."""
        serializer = AdminUserCreateSerializer(data={
            **self.user_data,
            'password': 'testpassword123',
            'confirm_password': 'testpassword123'
        })
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'broker')
        self.assertTrue(user.check_password('testpassword123'))
    
    def test_password_confirmation_validation(self):
        """Test password confirmation validation."""
        serializer = AdminUserCreateSerializer(data={
            **self.user_data,
            'password': 'testpassword123',
            'confirm_password': 'differentpassword'
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirm_password', serializer.errors)
    
    def test_email_uniqueness_validation(self):
        """Test email uniqueness validation."""
        # Create first user
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='password123'
        )
        
        # Try to create second user with same email
        serializer = AdminUserCreateSerializer(data={
            **self.user_data,
            'password': 'testpassword123',
            'confirm_password': 'testpassword123'
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
    
    def test_update_user_serializer(self):
        """Test updating a user with AdminUserUpdateSerializer."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        serializer = AdminUserUpdateSerializer(user, data={
            'first_name': 'Updated',
            'last_name': 'Name',
            'role': 'admin',
            'is_active': False
        })
        self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")
        updated_user = serializer.save()
        
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
        self.assertEqual(updated_user.role, 'admin')
        self.assertFalse(updated_user.is_active)
    
    def test_serializer_method_fields(self):
        """Test serializer method fields."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )
        
        serializer = AdminUserSerializer(user)
        data = serializer.data
        
        self.assertEqual(data['full_name'], 'Test User')
        self.assertEqual(data['is_active_display'], 'פעיל')
        self.assertIsNotNone(data['created_at_display'])


class AdminUserViewSetTest(APITestCase):
    """Test cases for AdminUserViewSet."""
    
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='test_admin',
            email='test_admin@example.com',
            password='adminpassword123',
            role='admin',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='test_regular',
            email='test_regular@example.com',
            password='regularpassword123',
            role='broker'
        )
        
        # Get admin token
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(refresh.access_token)
    
    def tearDown(self):
        """Clean up after each test."""
        User.objects.all().delete()
    
    def test_admin_permission_required(self):
        """Test that only admin users can access the viewset."""
        # Test without authentication
        response = self.client.get('/api/admin/users')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with regular user token
        refresh = RefreshToken.for_user(self.regular_user)
        regular_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {regular_token}')
        response = self.client.get('/api/admin/users')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_users_as_admin(self):
        """Test listing users as admin."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.get('/api/admin/users')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 4)  # admin + regular user + migration users
    
    def test_create_user_as_admin(self):
        """Test creating a user as admin."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'appraiser',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'is_active': True
        }
        
        response = self.client.post('/api/admin/users', user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.role, 'appraiser')
        self.assertTrue(user.check_password('newpassword123'))
    
    def test_update_user_as_admin(self):
        """Test updating a user as admin."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'role': 'investor',
            'is_active': False
        }
        
        response = self.client.patch(f'/api/admin/users/{self.regular_user.id}', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user was updated
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, 'Updated')
        self.assertEqual(self.regular_user.last_name, 'Name')
        self.assertEqual(self.regular_user.role, 'investor')
        self.assertFalse(self.regular_user.is_active)
    
    def test_deactivate_user(self):
        """Test deactivating a user."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.post(f'/api/admin/users/{self.regular_user.id}/deactivate')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)
    
    def test_activate_user(self):
        """Test activating a user."""
        # First deactivate the user
        self.regular_user.is_active = False
        self.regular_user.save()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.post(f'/api/admin/users/{self.regular_user.id}/activate')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_active)
    
    def test_reset_password(self):
        """Test resetting user password."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.post(f'/api/admin/users/{self.regular_user.id}/reset_password')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertIn('new_password', response.data)
        self.assertEqual(response.data['new_password'], 'defaultpassword123')
        
        # Verify password was reset
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.check_password('defaultpassword123'))
    
    def test_user_statistics(self):
        """Test user statistics endpoint."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.get('/api/admin/users/statistics')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('total_users', data)
        self.assertIn('active_users', data)
        self.assertIn('inactive_users', data)
        self.assertIn('role_counts', data)
        self.assertEqual(data['total_users'], 4)  # Including migration users
        self.assertEqual(data['active_users'], 4)  # All users are active
    
    def test_search_users(self):
        """Test searching users."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        # Search by username
        response = self.client.get('/api/admin/users?search=test_admin')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], 'test_admin')
        
        # Search by email
        response = self.client.get('/api/admin/users?search=test_regular@example.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['email'], 'test_regular@example.com')
    
    def test_filter_by_role(self):
        """Test filtering users by role."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.get('/api/admin/users?role=broker')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['role'], 'broker')
    
    def test_filter_by_status(self):
        """Test filtering users by status."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.get('/api/admin/users?status=active')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 4)  # All users are active
        
        # Deactivate one user
        self.regular_user.is_active = False
        self.regular_user.save()
        
        response = self.client.get('/api/admin/users?status=active')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)  # One user deactivated
        
        response = self.client.get('/api/admin/users?status=inactive')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_prevent_admin_self_deletion(self):
        """Test that admin cannot delete themselves."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.delete(f'/api/admin/users/{self.admin_user.id}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You cannot delete your own account', str(response.data))


class IsAdminUserPermissionTest(TestCase):
    """Test cases for IsAdminUser permission."""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='test_admin_permission',
            email='test_admin_permission@example.com',
            password='adminpassword123',
            role='admin'
        )
        
        self.regular_user = User.objects.create_user(
            username='test_regular_permission',
            email='test_regular_permission@example.com',
            password='regularpassword123',
            role='broker'
        )
    
    def tearDown(self):
        """Clean up after each test."""
        User.objects.all().delete()
    
    def test_admin_user_has_permission(self):
        """Test that admin user has permission."""
        permission = IsAdminUser()
        
        # Mock request with admin user
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.admin_user)
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_regular_user_no_permission(self):
        """Test that regular user has no permission."""
        permission = IsAdminUser()
        
        # Mock request with regular user
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.regular_user)
        
        self.assertFalse(permission.has_permission(request, None))
    
    def test_anonymous_user_no_permission(self):
        """Test that anonymous user has no permission."""
        permission = IsAdminUser()
        
        # Mock request with no user
        class MockRequest:
            def __init__(self):
                self.user = None
        
        request = MockRequest()
        
        self.assertFalse(permission.has_permission(request, None))
