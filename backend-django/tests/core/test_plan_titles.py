import pytest

from django.contrib.auth import get_user_model

from core.models import Asset, Plan
from core.serializers import PlanSerializer
from core.views import _normalize_plan_entry
from orchestration.pipeline.asset_enrichment import _create_documents_and_plans


User = get_user_model()


@pytest.mark.django_db
def test_plan_title_populated_and_exposed_in_api():
    user = User.objects.create_user(
        username='pipeline-user',
        email='pipeline@example.com',
        password='test-password',
    )

    asset = Asset.objects.create(
        scope_type='address',
        city='Tel Aviv',
        street='Herzl',
        number=10,
        created_by=user,
    )

    rami_plan = {
        'planNumber': 'RAMI-123',
        'title': 'Rami Master Plan',
        'status': 'approved',
        'url': 'https://rami.example.com/plan/RAMI-123',
    }

    mavat_plan = {
        'plan_id': 'MAVAT-456',
        'title': 'Mavat Renewal Plan',
        'status': 'approved',
        'url': 'https://mavat.example.com/plan/MAVAT-456',
    }

    _create_documents_and_plans(
        asset,
        gis_data={},
        gov_data={},
        plans=[rami_plan],
        mavat_plans=[mavat_plan],
        handasa_archive=[],
    )

    stored_rami_plan = Plan.objects.get(plan_number='RAMI-123')
    stored_mavat_plan = Plan.objects.get(plan_number='MAVAT-456')

    assert stored_rami_plan.title == 'Rami Master Plan'
    assert stored_rami_plan.description == 'Rami Master Plan'
    assert stored_mavat_plan.title == 'Mavat Renewal Plan'
    assert stored_mavat_plan.description == 'Mavat Renewal Plan'

    serialized = PlanSerializer(stored_rami_plan).data
    assert serialized['title'] == 'Rami Master Plan'

    normalized = _normalize_plan_entry({
        'id': stored_rami_plan.id,
        'plan_number': stored_rami_plan.plan_number,
        'title': stored_rami_plan.title,
        'description': stored_rami_plan.description,
        'status': stored_rami_plan.status,
        'file_url': stored_rami_plan.file_url,
        'raw': stored_rami_plan.raw,
    })

    assert normalized['title'] == 'Rami Master Plan'
    assert normalized['description'] == 'Rami Master Plan'
