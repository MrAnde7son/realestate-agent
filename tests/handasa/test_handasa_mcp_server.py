import base64
from pathlib import Path

import pytest

from handasa.mcp import server


class DummyContext:
    def __init__(self) -> None:
        self.messages = []

    async def info(self, message: str) -> None:  # pragma: no cover - trivial logging
        self.messages.append(("info", message))

    async def error(self, message: str) -> None:  # pragma: no cover - trivial logging
        self.messages.append(("error", message))


@pytest.mark.asyncio
async def test_handasa_archive_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.calls = 0

        def get_archive(self, block: str, parcel: str | None = None, page_size: int = 50):
            self.calls += 1
            return [{"external_id": "123"}]

    fake_client = FakeClient()
    monkeypatch.setattr(server, "_client", fake_client, raising=False)

    ctx = DummyContext()
    result = await server.handasa_archive.fn(ctx, block="123")

    assert result["success"] is True
    assert result["count"] == 1
    assert result["documents"][0]["external_id"] == "123"
    assert fake_client.calls == 1


@pytest.mark.asyncio
async def test_handasa_archive_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    class FlakyClient:
        def __init__(self) -> None:
            self.calls = 0

        def get_archive(self, block: str, parcel: str | None = None, page_size: int = 50):
            self.calls += 1
            if self.calls < 2:
                raise RuntimeError("temporary error")
            return []

    flaky_client = FlakyClient()
    monkeypatch.setattr(server, "_client", flaky_client, raising=False)
    monkeypatch.setenv("HANDASA_RETRIES", "1")
    monkeypatch.setenv("HANDASA_RETRY_DELAY", "0")

    ctx = DummyContext()
    result = await server.handasa_archive.fn(ctx, block="456")

    assert result["success"] is True
    assert result["count"] == 0
    assert flaky_client.calls == 2


@pytest.mark.asyncio
async def test_handasa_archive_requires_block() -> None:
    ctx = DummyContext()
    with pytest.raises(ValueError):
        await server.handasa_archive.fn(ctx, block="")


@pytest.mark.asyncio
async def test_download_handasa_document(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "file_name": "permit.pdf",
        "content_type": "application/pdf",
        "size": 4,
        "content": b"test",
        "file_path": Path("/tmp/permit.pdf"),
    }

    class FakeClient:
        def download_document(self, unique_id: str, save_to=None, overwrite=False):
            assert unique_id == "doc-1"
            return payload

    monkeypatch.setattr(server, "_client", FakeClient(), raising=False)

    ctx = DummyContext()
    result = await server.download_handasa_document.fn(
        ctx, unique_id="doc-1", return_content=True
    )

    assert result["success"] is True
    assert result["file_name"] == "permit.pdf"
    assert result["content_type"] == "application/pdf"
    assert result["size"] == 4
    assert result["file_path"] == str(payload["file_path"])
    assert result["content_base64"] == base64.b64encode(payload["content"]).decode("utf-8")


@pytest.mark.asyncio
async def test_download_requires_unique_id() -> None:
    ctx = DummyContext()
    with pytest.raises(ValueError):
        await server.download_handasa_document.fn(ctx, unique_id="")
