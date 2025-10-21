import datetime

import pytest

from core.models import Asset, Document, Plan
from orchestration.pipeline.asset_enrichment import _create_documents_and_plans


@pytest.mark.django_db
class TestGISPlanDocumentCreation:
    def test_creates_plan_and_document_records_for_gis_sources(self):
        asset = Asset.objects.create(scope_type="address")

        documents_url = (
            "https://gisn.tel-aviv.gov.il/tabaot/docs.aspx?id_taba=641"
            "&st_taba=ג&mode=internet"
        )

        plan_payload = {
            "oid_taba": 7,
            "id_taba": 641,
            "plan_number": "641",
            "taba": "ג                   ",
            "shem_taba": "תכנית \"ג\" - גגות - בניה על גגות בתים",
            "k_status": 11,
            "t_status": "בתוקף",
            "k_status_klali": 1,
            "t_status_klali": "בתוקף",
            "tr_matan_tokef": 766886400000,
            "tr_hafkada": 692150400000,
            "tr_shinuy_status": 766886400000,
            "ms_yalkut_acharon": 4208,
            "k_heykef": 3,
            "t_hekef": "כלל עירונית",
            "k_sivug": 1,
            "t_sivug": "מתאר",
            "shem_mismach": "97t.doc",
            "ms_mismach": 97,
            "ms_shetach": -1,
            "ms_shetach_graphi": 54025468.92,
            "k_ramat_pirut": 1,
            "t_ramat_pirut": "כללית",
            "url_documents": documents_url,
            "url_iplan": None,
            "date_import": "17/10/2025 00:46:54",
            "Shape_Length": 52300.34363123528,
            "Shape_Area": 54025468.92405008,
        }

        city_plan_payload = dict(
            plan_payload,
            id_taba=777,
            plan_number="777",
            tr_matan_tokef=None,
            t_status="מופקד",
        )

        gis_data = {
            "local_plans": [plan_payload],
            "city_plans": [city_plan_payload],
        }

        _create_documents_and_plans(
            asset,
            gis_data,
            gov_data={},
            plans=[],
            mavat_plans=[],
            handasa_archive=[],
        )

        plan_title = plan_payload["shem_taba"]
        plan_number = plan_payload["taba"].strip()

        plan = Plan.objects.get(plan_number=plan_number)
        assert plan.title == plan_title
        assert plan.file_url == documents_url
        assert plan.raw["id_taba"] == 777
        assert plan.effective_date == datetime.date(1994, 4, 21)

        local_document = Document.objects.get(
            document_type="plan_local", external_id=plan_title
        )
        assert local_document.document_type == "plan_local"
        assert local_document.source == "GIS"
        assert local_document.external_url == documents_url
        assert local_document.status == "approved"
        assert local_document.document_date == datetime.date(1994, 4, 21)
        assert local_document.filename == "97t.doc"
        assert local_document.mime_type == "application/msword"

        city_document = Document.objects.get(
            document_type="plan_citywide", external_id=plan_title
        )
        assert city_document.document_type == "plan_citywide"
        assert city_document.status == "pending"
        assert city_document.external_url == documents_url

        system_user = local_document.user
        assert system_user.email == "system@nadlaner.com"
