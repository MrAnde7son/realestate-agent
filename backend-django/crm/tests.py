from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Contact


class ContactEquityAPITests(TestCase):
    """Ensure contacts support optional equity field through the API."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="agent",
            password="password123",
            email="agent@example.com",
        )
        self.user.role = "broker"
        self.user.save(update_fields=["role"])
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_create_contact_with_equity(self):
        """Creating a contact should persist the provided equity value."""

        payload = {
            "name": "יוסי הון",
            "email": "yossi@example.com",
            "phone": "050-1111111",
            "equity": 350000.50,
        }

        response = self.client.post("/api/crm/contacts/", payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertIn("equity", response.data)
        self.assertEqual(response.data["equity"], 350000.5)

        contact = Contact.objects.get(id=response.data["id"])
        self.assertEqual(contact.equity, Decimal("350000.50"))

    def test_update_contact_can_clear_equity(self):
        """Updating a contact with null equity should remove the stored value."""

        contact = Contact.objects.create(
            owner=self.user,
            name="רות משכנתא",
            email="rut@example.com",
            equity=Decimal("125000.00"),
        )

        response = self.client.patch(
            f"/api/crm/contacts/{contact.id}/",
            {"equity": None},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["equity"])

        contact.refresh_from_db()
        self.assertIsNone(contact.equity)

    def test_create_contact_with_preference_fields(self):
        """Creating a contact should persist optional preference fields."""

        payload = {
            "name": "דנה חיפוש",
            "email": "dana@example.com",
            "city": "תל אביב",
            "streets": "נחלת בנימין, רוטשילד",
            "asset_type": "דירה",
            "area_min": 70,
            "area_max": 120,
            "floor": "3-5",
            "notes": "מחפשת דירה מוארת עם מעלית וחניה",
        }

        response = self.client.post("/api/crm/contacts/", payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["city"], payload["city"])
        self.assertEqual(response.data["streets"], payload["streets"])
        self.assertEqual(response.data["asset_type"], payload["asset_type"])
        self.assertEqual(response.data["area_min"], payload["area_min"])
        self.assertEqual(response.data["area_max"], payload["area_max"])
        self.assertEqual(response.data["floor"], payload["floor"])
        self.assertEqual(response.data["notes"], payload["notes"])

        contact = Contact.objects.get(id=response.data["id"])
        self.assertEqual(contact.city, payload["city"])
        self.assertEqual(contact.streets, payload["streets"])
        self.assertEqual(contact.asset_type, payload["asset_type"])
        self.assertEqual(contact.area_min, payload["area_min"])
        self.assertEqual(contact.area_max, payload["area_max"])
        self.assertEqual(contact.floor, payload["floor"])
        self.assertEqual(contact.notes, payload["notes"])
