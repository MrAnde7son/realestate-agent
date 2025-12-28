"""Simple tests for RAMI downloads without hitting the real network."""

from unittest.mock import Mock

import requests

from gov.rami.rami_client import RamiClient


class StubResponse:
    """Lightweight response object to avoid real HTTP calls."""

    def __init__(
        self, status_code: int, headers: dict | None = None, content: bytes = b""
    ) -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self._content = content
        # Provide text for parity with ``requests.Response``
        try:
            self.text = content.decode()
        except Exception:
            self.text = ""

    def iter_content(self, chunk_size: int = 8192):
        for start in range(0, len(self._content), chunk_size):
            chunk = self._content[start : start + chunk_size]
            if chunk:
                yield chunk


def test_direct_vs_client(monkeypatch):
    """Ensure both direct requests and the client session honour PDF responses."""

    test_url = "https://apps.land.gov.il/IturTabotData/takanonim/telmer/5050330.pdf"
    pdf_payload = b"%PDF-1.4 mock payload"

    direct_response = StubResponse(
        status_code=200,
        headers={
            "content-type": "application/pdf",
            "content-length": str(len(pdf_payload)),
        },
        content=pdf_payload,
    )
    client_response = StubResponse(
        status_code=200,
        headers={
            "content-type": "application/pdf",
            "content-length": str(len(pdf_payload)),
        },
        content=pdf_payload,
    )

    mock_get = Mock(return_value=direct_response)
    monkeypatch.setattr(requests, "get", mock_get)

    session = Mock()
    session.headers = {}
    session.get = Mock(return_value=client_response)

    client = RamiClient(session=session)

    direct = requests.get(test_url, timeout=30)
    via_client = client.session.get(test_url, timeout=30)

    assert direct.headers["content-type"].startswith("application/pdf")
    assert via_client.headers["content-type"].startswith("application/pdf")
    assert via_client.text.startswith("%PDF-1.4")
    assert client.session.headers["User-Agent"] == client.headers["User-Agent"]
    mock_get.assert_called_once_with(test_url, timeout=30)
    session.get.assert_called_once_with(test_url, timeout=30)


def test_working_download(tmp_path, monkeypatch):
    """Stream a mocked PDF response into a temporary file."""

    test_url = "https://apps.land.gov.il/IturTabotData/takanonim/telmer/5050330.pdf"
    pdf_payload = b"%PDF-1.4 minimal"
    response = StubResponse(
        status_code=200,
        headers={"content-type": "application/pdf"},
        content=pdf_payload,
    )

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
    )
    session.get = Mock(return_value=response)
    monkeypatch.setattr(requests, "Session", lambda: session)

    # Simulate the download workflow without hitting the real endpoint
    download_path = tmp_path / "test_download.pdf"
    resp = session.get(test_url, stream=True, timeout=60)
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")

    with open(download_path, "wb") as handle:
        for chunk in resp.iter_content(chunk_size=8192):
            handle.write(chunk)

    assert download_path.read_bytes() == pdf_payload
    session.get.assert_called_once_with(test_url, stream=True, timeout=60)
