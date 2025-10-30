import types

import pytest
from django.test import override_settings

from core.llm.providers.gemini import GeminiAdapter
from core.llm.types import ChatMessage


@override_settings(GEMINI_API_KEY="test-key", GEMINI_MODEL="gemini-2.0-flash")
@pytest.mark.asyncio
async def test_gemini_chat_maps_system_message_to_instruction(monkeypatch):
    captured = {}

    def fake_configure(api_key, **kwargs):
        captured["configured_key"] = api_key
        if "client_options" in kwargs:
            captured["client_options"] = kwargs["client_options"]

    class FakeChatSession:
        async def send_message_async(self, content):
            captured["sent_message"] = content
            return types.SimpleNamespace(text="ok")

    class FakeModel:
        def __init__(
            self,
            model_name,
            generation_config=None,
            system_instruction=None,
        ):
            captured["model_name"] = model_name
            captured["generation_config"] = generation_config
            captured["system_instruction"] = system_instruction

        def start_chat(self, history):
            captured["history"] = history
            return FakeChatSession()

    monkeypatch.setattr("google.generativeai.configure", fake_configure)

    def fake_model_factory(**kwargs):
        return FakeModel(**kwargs)

    monkeypatch.setattr(
        "google.generativeai.GenerativeModel",
        fake_model_factory,
    )

    adapter = GeminiAdapter()

    messages = [
        ChatMessage(role="system", content="You are helpful."),
        ChatMessage(role="system", content="Follow the brief."),
        ChatMessage(role="user", content="Hello"),
        ChatMessage(role="assistant", content="Hi"),
        ChatMessage(role="user", content="Write message"),
    ]

    result = await adapter.chat(messages)

    assert result == "ok"
    assert captured["configured_key"] == "test-key"
    assert captured["model_name"] == "gemini-2.0-flash"
    assert captured["generation_config"] is None
    assert captured["system_instruction"] == (
        "You are helpful.\n\nFollow the brief."
    )
    assert captured["history"] == [
        {"role": "user", "parts": ["Hello"]},
        {"role": "model", "parts": ["Hi"]},
    ]
    assert captured["sent_message"] == "Write message"
    assert (
        captured["client_options"].api_endpoint
        == "https://us-generativelanguage.googleapis.com"
    )
