import json
import pytest
from django.urls import reverse
from django.test import Client
from core.models import Asset, Document, User

pytestmark = pytest.mark.django_db


def _create_user():
    return User.objects.create_user(username='u1', email='u1@example.com', password='pass')


def test_permits_endpoint_with_building_permits():
    client = Client()
    asset = Asset.objects.create(
        scope_type='address',
        street='Test',
        number=1,
        city='Tel Aviv',
        meta={
            'gis_data': {
                'building_permits': [
                    {
                        'permission_num': '12345',
                        'request_num': 'REQ-1',
                        'building_stage': 'Issued',
                        'addresses': 'Test 1 Tel Aviv',
                        'url_hadmaya': 'http://example.com/permit/12345',
                        'permission_date': '2024-01-02'
                    }
                ]
            },
            'last_enrichment': '2024-01-03T10:00:00Z'
        }
    )

    url = reverse('asset_permits', kwargs={'asset_id': asset.id})
    resp = client.get(url)
    assert resp.status_code == 200
    data = json.loads(resp.content.decode())
    assert 'permits' in data
    assert len(data['permits']) == 1
    p = data['permits'][0]
    assert p['permit_number'] == '12345'
    assert p['request_number'] == 'REQ-1'
    assert p['status'] == 'Issued'
    assert p['url'] == 'http://example.com/permit/12345'
    assert p['source'] == 'gis'


def test_permits_endpoint_with_legacy_permits_key():
    client = Client()
    asset = Asset.objects.create(
        scope_type='address',
        street='Legacy',
        number=2,
        city='Tel Aviv',
        meta={
            'gis_data': {
                'permits': [  # legacy key
                    {
                        'permission_num': '999',
                        'request_num': 'REQ-999',
                        'building_stage': 'Approved',
                        'addresses': 'Legacy 2 Tel Aviv',
                        'url_hadmaya': 'http://example.com/permit/999',
                        'permission_date': '2024-02-10'
                    }
                ]
            },
            'last_enrichment': '2024-02-11T09:00:00Z'
        }
    )

    url = reverse('asset_permits', kwargs={'asset_id': asset.id})
    resp = client.get(url)
    assert resp.status_code == 200
    data = json.loads(resp.content.decode())
    assert len(data['permits']) == 1
    p = data['permits'][0]
    assert p['permit_number'] == '999'
    assert p['status'] == 'Approved'


def test_permits_endpoint_deduplicates_same_permission_num():
    client = Client()
    asset = Asset.objects.create(
        scope_type='address',
        street='Dup',
        number=3,
        city='Tel Aviv',
        meta={
            'gis_data': {
                'building_permits': [
                    {'permission_num': 'ABC', 'request_num': 'R1', 'building_stage': 'Stage1'},
                    {'permission_num': 'ABC', 'request_num': 'R2', 'building_stage': 'Stage2'},
                ]
            },
            'last_enrichment': '2024-03-01T12:00:00Z'
        }
    )

    url = reverse('asset_permits', kwargs={'asset_id': asset.id})
    resp = client.get(url)
    assert resp.status_code == 200
    data = json.loads(resp.content.decode())
    # Should only keep the first one with permission_num ABC
    assert len(data['permits']) == 1
    assert data['permits'][0]['permit_number'] == 'ABC'


def test_permits_endpoint_document_and_meta_merge():
    client = Client()
    user = _create_user()
    asset = Asset.objects.create(scope_type='address', street='Doc', number=4, city='Tel Aviv', meta={'gis_data': {'building_permits': []}})
    # Create a permit document
    Document.objects.create(
        asset=asset,
        user=user,
        title='Permit PDF',
        description='A permit file',
        document_type='permit',
        status='approved',
        filename='permit.pdf',
        file_path='documents/permit.pdf',
        file_size=100,
        mime_type='application/pdf',
        external_id='DOC-777',
        external_url='http://example.com/doc777.pdf',
        meta={'request_number': 'REQ-777'}
    )

    # Add a different permit in meta
    asset.meta['gis_data']['building_permits'].append({'permission_num': '777', 'request_num': 'REQ-777', 'building_stage': 'Issued'})
    asset.save(update_fields=['meta'])

    url = reverse('asset_permits', kwargs={'asset_id': asset.id})
    resp = client.get(url)
    assert resp.status_code == 200
    data = json.loads(resp.content.decode())
    # Document + meta (dedup by permit_number: document external_id counts as permit_number, meta has permission_num '777') => two entries because external_id != permission_num
    assert len(data['permits']) == 2
    ids = {p['id'] for p in data['permits']}
    assert 'DOC-777' in ids or any(p['permit_number'] == 'DOC-777' for p in data['permits'])
    assert any(p.get('permit_number') == '777' for p in data['permits'])

