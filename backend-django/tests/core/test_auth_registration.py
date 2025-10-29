from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AuthRegistrationTests(APITestCase):
    """Tests for user registration using email as the identifier."""

    def setUp(self):
        self.url = reverse('auth_register')

    def tearDown(self):
        User.objects.all().delete()

    def test_register_uses_email_as_username(self):
        payload = {
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'first_name': 'New',
            'last_name': 'User',
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        user = User.objects.get(email=payload['email'])
        self.assertEqual(user.username, payload['email'])
        self.assertEqual(user.first_name, payload['first_name'])
        self.assertEqual(user.last_name, payload['last_name'])
        self.assertEqual(user.role, User.Role.PRIVATE)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='securepass123',
        )

        payload = {
            'email': 'existing@example.com',
            'password': 'anotherpass123',
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
        self.assertIn('User with this email already exists', response.data.get('error', ''))

    def test_register_forces_private_role(self):
        payload = {
            'email': 'rolecheck@example.com',
            'password': 'securepass123',
            'role': 'broker',
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        user = User.objects.get(email=payload['email'])
        self.assertEqual(user.role, User.Role.PRIVATE)
