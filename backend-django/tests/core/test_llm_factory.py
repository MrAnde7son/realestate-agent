from django.test import override_settings

from core.llm.factory import create_llm_client
from core.llm.providers.gemini import GeminiAdapter


@override_settings(
    GEMINI_API_KEY=None,
    GEMINI_MODEL=None,
    GOOGLE_API_KEY="google-key",
    GOOGLE_MODEL="gemini-2.0-flash",
)
def test_create_llm_client_uses_google_api_key(monkeypatch):
    captured = {}

    def fake_configure(api_key, **kwargs):
        captured["api_key"] = api_key
        if "client_options" in kwargs:
            captured["client_options"] = kwargs["client_options"]

    monkeypatch.setattr("google.generativeai.configure", fake_configure)

    client = create_llm_client("gemini")

    assert isinstance(client, GeminiAdapter)
    assert captured["api_key"] == "google-key"
    assert (
        captured["client_options"].api_endpoint
        == "https://us-generativelanguage.googleapis.com"
    )
    assert client.model_name is None
