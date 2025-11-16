import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from email.header import decode_header

from core.models import Asset


User = get_user_model()


@pytest.mark.django_db
def test_asset_landing_page_requires_broker_role():
    asset = Asset.objects.create(scope_type='address', city='חיפה')
    user = User.objects.create_user(
        username='viewer',
        email='viewer@example.com',
        password='pass12345',
        role='viewer',
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(reverse('asset_landing_page', args=[asset.id]))

    assert response.status_code == 403
    assert 'Landing page generation' in response.json()['error']


@pytest.mark.django_db
def test_asset_landing_page_generates_html_for_broker():
    user = User.objects.create_user(
        username='broker',
        email='broker@example.com',
        password='pass12345',
        role='broker',
        company='Acme Realty',
        phone='050-1234567',
    )
    asset = Asset.objects.create(
        scope_type='address',
        city='תל אביב',
        neighborhood='לב העיר',
        street='אלנבי',
        number=10,
        rooms=4,
        area=120,
        price=2_500_000,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(reverse('asset_landing_page', args=[asset.id]))

    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/html')
    disposition = response['Content-Disposition']
    decoded_parts = []
    for part, encoding in decode_header(disposition):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
        else:
            decoded_parts.append(part)
    decoded_disposition = ''.join(decoded_parts)
    assert 'landing-page' in decoded_disposition

    html = response.content.decode('utf-8')
    assert 'אלנבי' in html
    assert 'תל אביב' in html
    assert 'Acme Realty' in html
