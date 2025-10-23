from django.test import override_settings

from core.llm.factory import create_llm_client
from core.llm.providers.gemini import GeminiAdapter


@override_settings(
    GEMINI_API_KEY=None,
    GEMINI_MODEL=None,
    GOOGLE_API_KEY="google-key",
    GOOGLE_MODEL="gemini-1.5-pro",
)
def test_create_llm_client_uses_google_api_key(monkeypatch):
    captured = {}

    def fake_configure(api_key):
        captured["api_key"] = api_key

    monkeypatch.setattr("google.generativeai.configure", fake_configure)

    client = create_llm_client("gemini")

    assert isinstance(client, GeminiAdapter)
    assert captured["api_key"] == "google-key"
    assert client.model_name == "gemini-1.5-pro"
