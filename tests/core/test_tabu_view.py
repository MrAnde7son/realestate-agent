import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_backend.settings')
sys.path.insert(0, os.path.abspath('backend-django'))
import django
django.setup()
from django.test import Client


def test_tabu_view():
    client = Client()
    with open('tests/data/tabu_sample.pdf', 'rb') as f:
        resp = client.post('/api/tabu/', {'file': f})
    assert resp.status_code == 200
    data = resp.json()
    assert any(r['field'] == 'Owner' for r in data['rows'])

    with open('tests/data/tabu_sample.pdf', 'rb') as f:
        resp = client.post('/api/tabu/?q=Parcel', {'file': f})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data['rows']) == 1 and data['rows'][0]['value'] == '12345'
