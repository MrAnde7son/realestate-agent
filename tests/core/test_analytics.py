import pytest
from django.utils import timezone
from core.analytics import track
from core.models import AnalyticsDaily
from core import tasks
from datetime import timedelta
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_rollup_idempotent():
    track('user_signup')
    track('asset_create')
    tasks.rollup_analytics.run()
    tasks.rollup_analytics.run()
    daily = AnalyticsDaily.objects.get(date=timezone.now().date())
    assert daily.users == 1
    assert daily.assets == 1


@pytest.mark.django_db
def test_top_failures_query(django_user_model):
    track('collector_fail', source='yad2', error_code='500')
    track('collector_fail', source='yad2', error_code='500')
    track('collector_fail', source='gis', error_code='timeout')
    tasks.rollup_analytics.run()
    user = django_user_model.objects.create_user(
        username='admin2', email='adm@example.com', password='pw', role='admin'
    )
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    resp = api_client.get('/api/analytics/')
    assert resp.status_code == 200
    top = resp.json()['top_failures'][0]
    assert top['source'] == 'yad2'
    assert top['count'] == 2


@pytest.mark.django_db
def test_spike_detection():
    today = timezone.now().date()
    for i in range(1, 8):
        AnalyticsDaily.objects.create(date=today - timedelta(days=i), errors=1)
    AnalyticsDaily.objects.create(date=today, errors=10)
    assert tasks.alert_on_spikes.run() is True


@pytest.mark.django_db
def test_e2e_metrics():
    track('asset_create')
    track('report_success')
    track('alert_send')
    tasks.rollup_analytics.run()
    daily = AnalyticsDaily.objects.get(date=timezone.now().date())
    assert daily.assets == 1
    assert daily.reports == 1
    assert daily.alerts == 1
