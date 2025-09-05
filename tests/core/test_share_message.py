import json
import os
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from core.models import Asset, ShareToken


@pytest.mark.django_db
def test_asset_share_message_fallback_no_openai():
    os.environ.pop('OPENAI_API_KEY', None)
    asset = Asset.objects.create(
        scope_type='address',
        city='תל אביב',
        neighborhood='לב העיר',
        street='אלנבי',
        number=1,
        rooms=3,
        area=70,
        price=2000000,
        meta={'transit': 'רכבת השלום'},
    )
    client = Client()
    resp = client.post(
        f'/api/assets/{asset.id}/share-message/',
        data=json.dumps({'language': 'he'}),
        content_type='application/json',
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['text']
    assert data['share_url'].startswith('/r/')


@pytest.mark.django_db
def test_share_token_invalid_or_expired_returns_404():
    client = Client()
    resp = client.get('/r/nonexistent')
    assert resp.status_code == 404

    asset = Asset.objects.create(scope_type='address')
    ShareToken.objects.create(
        asset=asset,
        token='expiredtoken',
        expires_at=timezone.now() - timedelta(days=1),
    )
    resp2 = client.get('/r/expiredtoken')
    assert resp2.status_code == 404
