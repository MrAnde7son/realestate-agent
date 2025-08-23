import pytest
from django.core.management import call_command

from core.models import Asset, SourceRecord
from core import tasks


class DummyYad2Helper:
    @staticmethod
    def get_location_codes(city, neighborhood=None):
        return {'city_id': 5000}

    @staticmethod
    def search_real_estate_smart(property_type, city, neighborhood=None, **kwargs):
        return {
            'success': True,
            'assets_preview': [
                {'id': '1', 'title': 'Listing', 'url': 'http://example.com'}
            ]
        }


class DummyRamiClient:
    def get_plans_by_gush_helka(self, gush, helka):
        assert gush == '1234' and helka == '56'
        return [{'id': 'p1', 'title': 'Plan', 'url': 'http://rami'}]


def test_pull_yad2_saves_records(monkeypatch):
    call_command('migrate', run_syncdb=True, verbosity=0)
    monkeypatch.setattr('yad2.search_helper.Yad2SearchHelper', DummyYad2Helper)
    asset = Asset.objects.create(scope_type='address', city='תל אביב', status='enriching', meta={})
    context = {'asset_id': asset.id, 'lat': 32.1, 'lon': 34.8, 'radius': 150}
    result = tasks.pull_yad2(context)
    assert result['count'] == 1
    assert SourceRecord.objects.filter(asset_id=asset.id, source='yad2').count() == 1


def test_pull_rami_saves_records(monkeypatch):
    call_command('migrate', run_syncdb=True, verbosity=0)
    monkeypatch.setattr('rami.rami_client.RamiClient', lambda: DummyRamiClient())
    asset = Asset.objects.create(scope_type='parcel', gush='1234', helka='56', status='enriching', meta={})
    context = {'asset_id': asset.id, 'gush': '1234', 'helka': '56'}
    result = tasks.pull_rami(context)
    assert result['count'] == 1
    assert SourceRecord.objects.filter(asset_id=asset.id, source='rami_plan').count() == 1


def test_pull_decisive_saves_records(monkeypatch):
    call_command('migrate', run_syncdb=True, verbosity=0)
    monkeypatch.setattr(
        'gov.decisive.fetch_decisive_appraisals',
        lambda block, plot, max_pages=2: [
            {'title': 'Decision', 'pdf_url': 'http://gov'}
        ]
    )
    asset = Asset.objects.create(scope_type='parcel', gush='1234', helka='56', status='enriching', meta={})
    context = {'asset_id': asset.id, 'gush': '1234', 'helka': '56'}
    result = tasks.pull_decisive(context)
    assert result['count'] == 1
    assert SourceRecord.objects.filter(asset_id=asset.id, source='gov_decisive').count() == 1
