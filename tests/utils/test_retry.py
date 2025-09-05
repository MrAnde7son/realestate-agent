import requests
from unittest.mock import Mock
from datetime import datetime

from utils.retry import request_with_retry


def test_request_with_retry_succeeds_after_retry():
    attempts = {'count': 0}

    def fake_get(url, **kwargs):
        attempts['count'] += 1
        if attempts['count'] == 1:
            raise requests.RequestException('boom')
        response = Mock()
        response.status_code = 200
        response.raise_for_status = lambda: None
        return response

    response = request_with_retry(fake_get, 'http://example.com', max_retries=3, backoff_factor=0)
    assert response.status_code == 200
    assert attempts['count'] == 2

    fetched_at = datetime.utcnow().isoformat()
    lineage = {'source': 'test', 'fetched_at': fetched_at, 'url': 'http://example.com'}
    assert lineage['url'] == 'http://example.com'
