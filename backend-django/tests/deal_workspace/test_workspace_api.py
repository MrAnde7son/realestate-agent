from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Asset, User
from deal_workspace import models as workspace_models


class DealWorkspaceAPITests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="password",
        )
        self.seller = User.objects.create_user(
            username="seller",
            email="seller@example.com",
            password="password",
        )
        self.asset = Asset.objects.create(
            scope_type="address",
            city="Tel Aviv",
            status="pending",
            created_by=self.buyer,
        )
        self.buyer_client = APIClient()
        self.buyer_client.force_authenticate(self.buyer)
        self.seller_client = APIClient()
        self.seller_client.force_authenticate(self.seller)
        self.deal_id = self._create_deal()
        self.negotiation_id = self._start_negotiation()
        self._create_additional_deals()

    def _create_deal(self) -> int:
        url = f"/api/deal-workspace/deals/create/{self.asset.id}"
        response = self.buyer_client.post(
            url,
            {
                "stage": "discovery",
                "parties": [
                    {
                        "user_id": self.buyer.id,
                        "role": "buyer",
                        "side": "buyer",
                    },
                    {
                        "user_id": self.seller.id,
                        "role": "seller",
                        "side": "seller",
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response.data["id"]

    def _start_negotiation(self) -> int:
        url = f"/api/deal-workspace/negotiations/{self.deal_id}"
        response = self.buyer_client.post(url, {}, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        return response.data["id"]

    def _create_additional_deals(self):
        self.second_asset = Asset.objects.create(
            scope_type="address",
            city="Jerusalem",
            status="pending",
            normalized_address="King George 12, Jerusalem",
            created_by=self.buyer,
        )
        self.third_user = User.objects.create_user(
            username="observer",
            email="observer@example.com",
            password="password",
        )
        self.second_deal = workspace_models.Deal.objects.create(
            asset=self.second_asset,
            stage=workspace_models.Deal.Stage.LEGAL,
            deal_lead=self.buyer,
        )
        workspace_models.PartyRole.objects.create(
            deal=self.second_deal,
            user=self.buyer,
            role=workspace_models.PartyRole.Role.BUYER,
            side=workspace_models.PartyRole.Side.BUYER,
            invitation_status=workspace_models.PartyRole.InvitationStatus.ACCEPTED,
        )
        workspace_models.PartyRole.objects.create(
            deal=self.second_deal,
            user=self.seller,
            role=workspace_models.PartyRole.Role.SELLER,
            side=workspace_models.PartyRole.Side.SELLER,
            invitation_status=workspace_models.PartyRole.InvitationStatus.ACCEPTED,
        )

        self.unrelated_asset = Asset.objects.create(
            scope_type="address",
            city="Haifa",
            status="pending",
            normalized_address="Allenby 4, Haifa",
            created_by=self.third_user,
        )
        unrelated_deal = workspace_models.Deal.objects.create(
            asset=self.unrelated_asset,
            stage=workspace_models.Deal.Stage.DISCOVERY,
            deal_lead=self.third_user,
        )
        workspace_models.PartyRole.objects.create(
            deal=unrelated_deal,
            user=self.third_user,
            role=workspace_models.PartyRole.Role.AGENT,
            side=workspace_models.PartyRole.Side.NEUTRAL,
            invitation_status=workspace_models.PartyRole.InvitationStatus.ACCEPTED,
        )

    def _buyer_role(self):
        return workspace_models.PartyRole.objects.get(
            deal_id=self.deal_id, user=self.buyer
        )

    def _seller_role(self):
        return workspace_models.PartyRole.objects.get(
            deal_id=self.deal_id, user=self.seller
        )

    def test_negotiation_counter_and_accept_flow(self):
        offer_payload = {
            "negotiation": self.negotiation_id,
            "amount": 4_000_000,
            "currency": "ILS",
            "financing_type": "mixed",
            "down_payment_pct": "30",
            "conditions": {
                "inspection": True,
                "financing_contingency": 21,
            },
            "expiration_at": (timezone.now() + timedelta(days=2)).isoformat(),
            "message": "Initial offer",
        }
        response = self.buyer_client.post(
            "/api/deal-workspace/offers",
            offer_payload,
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        offer_id = response.data["id"]

        counter_payload = {
            "amount": 4_250_000,
            "currency": "ILS",
            "financing_type": "mixed",
            "down_payment_pct": "35",
            "conditions": {"inspection": True},
            "expiration_at": (timezone.now() + timedelta(days=3)).isoformat(),
            "message": "Counter offer",
        }
        counter_url = f"/api/deal-workspace/offers/{offer_id}/counter"
        counter_response = self.seller_client.post(
            counter_url, counter_payload, format="json"
        )
        self.assertEqual(counter_response.status_code, 201, counter_response.content)
        counter_id = counter_response.data["id"]

        # Original offer should be marked as countered
        original_offer = workspace_models.Offer.objects.get(pk=offer_id)
        self.assertEqual(original_offer.status, workspace_models.Offer.Status.COUNTERED)

        accept_url = f"/api/deal-workspace/offers/{counter_id}/accept"
        accept_response = self.buyer_client.post(accept_url, {}, format="json")
        self.assertEqual(accept_response.status_code, 200, accept_response.content)
        self.assertEqual(accept_response.data["status"], "accepted")

        negotiation = workspace_models.Negotiation.objects.get(pk=self.negotiation_id)
        self.assertEqual(negotiation.status, workspace_models.Negotiation.Status.CLOSED)
        deal = workspace_models.Deal.objects.get(pk=self.deal_id)
        self.assertEqual(deal.stage, workspace_models.Deal.Stage.LEGAL)
        self.assertTrue(
            workspace_models.AuditLog.objects.filter(
                entity_type="offer", action="accepted"
            ).exists()
        )

    def test_list_deals_includes_asset_summary_and_filters(self):
        response = self.buyer_client.get("/api/deal-workspace/deals", format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)

        first = data[0]
        self.assertIn("asset_summary", first)
        summary = first["asset_summary"]
        self.assertEqual(summary["id"], first["asset"])
        self.assertIn(summary["city"], {"Tel Aviv", "Jerusalem"})

        stage_response = self.buyer_client.get(
            "/api/deal-workspace/deals?stage=legal", format="json"
        )
        self.assertEqual(stage_response.status_code, 200)
        stage_data = stage_response.json()
        self.assertEqual(len(stage_data), 1)
        self.assertEqual(stage_data[0]["id"], self.second_deal.id)

        search_response = self.buyer_client.get(
            "/api/deal-workspace/deals?q=Jerusalem", format="json"
        )
        self.assertEqual(search_response.status_code, 200)
        search_data = search_response.json()
        self.assertEqual(len(search_data), 1)
        self.assertEqual(search_data[0]["asset_summary"]["city"], "Jerusalem")

        seller_view = self.seller_client.get("/api/deal-workspace/deals", format="json")
        self.assertEqual(seller_view.status_code, 200)
        seller_data = seller_view.json()
        self.assertEqual(len(seller_data), 2)

        third_user_client = APIClient()
        third_user_client.force_authenticate(self.third_user)
        third_view = third_user_client.get("/api/deal-workspace/deals", format="json")
        self.assertEqual(third_view.status_code, 200)
        third_data = third_view.json()
        self.assertEqual(len(third_data), 1)
        self.assertEqual(
            third_data[0]["asset_summary"]["city"], self.unrelated_asset.city
        )

    def test_document_visibility_respects_sides(self):
        buyer_doc_response = self.buyer_client.post(
            "/api/deal-workspace/documents",
            {
                "deal": self.deal_id,
                "kind": "legal",
                "title": "Buyer NDA",
                "storage_url": "https://example.com/buyer.pdf",
                "visibility_scope": "buyer_side",
            },
            format="json",
        )
        self.assertEqual(
            buyer_doc_response.status_code, 201, buyer_doc_response.content
        )

        seller_doc_response = self.seller_client.post(
            "/api/deal-workspace/documents",
            {
                "deal": self.deal_id,
                "kind": "legal",
                "title": "Seller Disclosures",
                "storage_url": "https://example.com/seller.pdf",
                "visibility_scope": "seller_side",
            },
            format="json",
        )
        self.assertEqual(
            seller_doc_response.status_code, 201, seller_doc_response.content
        )

        buyer_list = self.buyer_client.get(
            f"/api/deal-workspace/documents?deal_id={self.deal_id}",
            format="json",
        )
        self.assertEqual(buyer_list.status_code, 200)
        buyer_titles = {doc["title"] for doc in buyer_list.json()}
        self.assertIn("Buyer NDA", buyer_titles)
        self.assertNotIn("Seller Disclosures", buyer_titles)

        seller_list = self.seller_client.get(
            f"/api/deal-workspace/documents?deal_id={self.deal_id}",
            format="json",
        )
        self.assertEqual(seller_list.status_code, 200)
        seller_titles = {doc["title"] for doc in seller_list.json()}
        self.assertIn("Seller Disclosures", seller_titles)
        self.assertNotIn("Buyer NDA", seller_titles)

    def test_mortgage_application_requires_applicant_side(self):
        buyer_role = self._buyer_role()
        mortgage_payload = {
            "deal": self.deal_id,
            "applicant_partyrole": buyer_role.id,
            "status": "submitted",
            "requested_amount": 2_000_000,
            "ltv_pct": "60",
            "income_json": {"salary": 40000},
        }
        create_response = self.buyer_client.post(
            "/api/deal-workspace/mortgages",
            mortgage_payload,
            format="json",
        )
        self.assertEqual(create_response.status_code, 201, create_response.content)
        application_id = create_response.data["id"]

        forbidden_response = self.seller_client.post(
            "/api/deal-workspace/mortgages",
            mortgage_payload,
            format="json",
        )
        self.assertEqual(forbidden_response.status_code, 403)

        offer_payload = {
            "mortgageapplication": application_id,
            "lender_name": "Mizrahi",
            "product_type": "mixed",
            "term_months": 240,
            "rate_pct": "4.10",
            "apr_estimate_pct": "4.35",
            "monthly_payment": "12890",
            "fees_total": "4500",
            "valid_until": (timezone.now() + timedelta(days=30)).isoformat(),
            "score": "92",
            "source": "manual",
        }
        offer_response = self.buyer_client.post(
            "/api/deal-workspace/mortgage-offers",
            offer_payload,
            format="json",
        )
        self.assertEqual(offer_response.status_code, 201, offer_response.content)
        offers_list = self.buyer_client.get(
            "/api/deal-workspace/mortgage-offers?"
            f"mortgageapplication_id={application_id}",
            format="json",
        )
        self.assertEqual(offers_list.status_code, 200)
        self.assertEqual(len(offers_list.json()), 1)
