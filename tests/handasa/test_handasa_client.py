import base64
import json

import pytest

from handasa.client import (
    FILES_API_URL,
    PROCESS_QUERY_URL,
    SEARCH_RESULTS_URL,
    HandasaClient,
)


class FakeResponse:
    def __init__(self, payload):
        self.status_code = payload.get('status', 200)
        self._text = payload.get('text', '')
        self._content = payload.get('content', self._text.encode('utf-8'))
        self._json = payload.get('json_data')

    @property
    def text(self):
        return self._text

    @property
    def content(self):
        return self._content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        if self._json is not None:
            return self._json
        return json.loads(self._content.decode('utf-8'))


# python
class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.headers = {}

    def _find_index(self, method, url, params=None):
        for i, payload in enumerate(self.responses):
            if payload.get('method') != method:
                continue
            if payload.get('url') != url:
                continue
            expected_params = payload.get('params')
            if expected_params is not None and expected_params != params:
                continue
            return i
        return None

    def _next(self, method=None, url=None, params=None):
        if method is None and url is None:
            if not self.responses:
                raise AssertionError("No more fake responses configured")
            return self.responses.pop(0)

        idx = self._find_index(method, url, params=params)
        if idx is None:
            raise AssertionError(f"No fake response configured for {method} {url} (remaining: {self.responses})")
        return self.responses.pop(idx)

    def get(self, url, **kwargs):
        params = kwargs.get('params')
        payload = self._next('GET', url, params=params)
        assert payload['method'] == 'GET'
        assert payload['url'] == url
        expected_params = payload.get('params')
        if expected_params is not None:
            assert params == expected_params
        return FakeResponse(payload)

    def post(self, url, data=None, json=None, **kwargs):
        payload = self._next('POST', url)
        assert payload['method'] == 'POST'
        assert payload['url'] == url
        if 'content' not in payload:
            if isinstance(data, bytes):
                payload['content'] = data
            elif isinstance(data, str):
                payload['content'] = data.encode('utf-8')
            else:
                payload['content'] = b''
        return FakeResponse(payload)


@pytest.fixture
def process_query_payload():
    return [
        {
            'ResultTableCollection': {
                'ResultTables': [
                    {
                        "TableType": "RelevantResults",
                        "TotalRows": 1,
                        'ResultRows': [
                            {
                                'UniqueID': '{HANDASA-123}',
                                'Title': 'Permit Title',
                                'TlvMPEngDocumentType': 'היתר מילולי חתום',
                                'TlvMPEngPermitNum': 'H-123',
                                'TlvMPEngOnlineReqNum': 'REQ-123',
                                'TlvMPEngIssueDate': '/Date(1704067200000)/',
                                'Path': 'https://handasa.tel-aviv.gov.il/documents/123',
                            }
                        ]
                    }
                ]
            }
        }
    ]


def test_get_archive_normalizes_handasa_rows(process_query_payload):
    session = FakeSession([
        {
            'method': 'GET',
            'url': SEARCH_RESULTS_URL,
            'text': '{ "formDigestValue": "0xF8A85579F71BE2BE68D6CE5419F40509D62AD5143479658A3936237B6678F1D8EE4513BF5FD9D7AF037BB0505839C281C7B0F486E212F6B98C5FA3077FE68D53,14 Oct 2025 10:11:06 -0000", }',
        },
        {
            'method': 'POST',
            'url': PROCESS_QUERY_URL,
            'content': json.dumps(process_query_payload).encode('utf-8'),
        },
    ])

    client = HandasaClient(session=session)
    permits = client.get_archive('6952', '127')

    assert len(permits) == 1
    permit = permits[0]
    assert permit['external_id'] == 'HANDASA-123'
    assert permit['permission_num'] == 'H-123'
    assert permit['request_num'] == 'REQ-123'
    assert permit['document_date'] == '2024-01-01'
    assert permit['external_url'].endswith('HANDASA-123')
    assert permit['source'] == 'Handasa'
    assert permit['document_type'] == 'permit'
    assert permit['document_category'] == 'permit'


def test_get_archive_marks_non_permit_documents():
    payload = [
        {
            'ResultTableCollection': {
                'ResultTables': [
                    {
                        "TableType": "RelevantResults",
                        "TotalRows": 1,
                        'ResultRows': [
                            {
                                'UniqueID': '{HANDASA-456}',
                                'Title': 'Form Document',
                                'TlvMPEngDocumentType': 'טופס 4',
                                'TlvMPEngOnlineReqNum': 'REQ-999',
                                'Path': 'https://handasa.tel-aviv.gov.il/documents/456',
                            }
                        ]
                    }
                ]
            }
        }
    ]
    session = FakeSession([
        {
            'method': 'GET',
            'url': SEARCH_RESULTS_URL,
            'text': '{ "formDigestValue": "0xF8A85579F71BE2BE68D6CE5419F40509D62AD5143479658A3936237B6678F1D8EE4513BF5FD9D7AF037BB0505839C281C7B0F486E212F6B98C5FA3077FE68D53,14 Oct 2025 10:11:06 -0000", }',
        },
        {
            'method': 'POST',
            'url': PROCESS_QUERY_URL,
            'content': json.dumps(payload).encode('utf-8'),
        },
    ])

    client = HandasaClient(session=session)
    archive = client.get_archive('6952', '127')

    assert len(archive) == 1
    doc = archive[0]
    assert doc['external_id'] == 'HANDASA-456'
    assert doc['document_type'] == 'other'


def test_download_document_decodes_buffer():
    encoded = base64.b64encode(b'pdf-bytes').decode('ascii')
    session = FakeSession([
        {
            'method': 'GET',
            'url': FILES_API_URL,
            'params': {'id': 'HANDASA-123'},
            'json_data': {
                'fileName': 'permit.pdf',
                'buffer': encoded,
                'contentType': 'application/pdf',
            },
        }
    ])

    client = HandasaClient(session=session)
    result = client.download_document('HANDASA-123')

    assert result['file_name'] == 'permit.pdf'
    assert result['content'] == b'pdf-bytes'
    assert result['content_type'] == 'application/pdf'


def test_download_document_can_save_file(tmp_path):
    encoded = base64.b64encode(b'some-contents').decode('ascii')
    session = FakeSession([
        {
            'method': 'GET',
            'url': FILES_API_URL,
            'params': {'id': 'HANDASA-456'},
            'json_data': {
                'fileName': 'another.pdf',
                'buffer': encoded,
                'contentType': 'application/pdf',
            },
        }
    ])

    client = HandasaClient(session=session)
    output_dir = tmp_path / 'documents'
    result = client.download_document('HANDASA-456', save_to=output_dir)

    expected_path = output_dir / 'another.pdf'
    assert expected_path.read_bytes() == b'some-contents'
    assert result['file_path'] == expected_path
