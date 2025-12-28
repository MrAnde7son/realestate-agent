import pytest

from core.llm.types import BaseGenOptions, ChatMessage, LLMClient


def test_llm_client_is_abstract():
    with pytest.raises(TypeError):
        LLMClient()


class _MockLLMClient(LLMClient):
    provider = "openai"

    async def generate_text(
        self, prompt: str, options: BaseGenOptions | None = None
    ) -> str:
        return prompt.upper()

    async def generate_json(
        self,
        prompt: str,
        schema: dict,
        options: BaseGenOptions | None = None,
    ) -> dict:
        return {"prompt": prompt, "schema": schema}

    async def chat(
        self, messages: list[ChatMessage], options: BaseGenOptions | None = None
    ) -> str:
        return " ".join(message.content for message in messages)


@pytest.mark.asyncio
async def test_llm_client_subclass_can_be_used():
    client = _MockLLMClient()

    prompt = "hello"
    assert await client.generate_text(prompt) == "HELLO"

    schema = {"type": "object"}
    assert await client.generate_json(prompt, schema) == {
        "prompt": prompt,
        "schema": schema,
    }

    messages = [
        ChatMessage(role="user", content="Hi"),
        ChatMessage(role="assistant", content="there"),
    ]
    assert await client.chat(messages) == "Hi there"
