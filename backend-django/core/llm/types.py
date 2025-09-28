from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel

LLMProvider = Literal["gemini", "openai"]


class BaseGenOptions(BaseModel):
    temperature: float = 0.2
    json: bool = False
    response_schema: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMClient:
    provider: LLMProvider

    async def generate_text(
        self, prompt: str, options: Optional[BaseGenOptions] = None
    ) -> str:
        raise NotImplementedError

    async def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        options: Optional[BaseGenOptions] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    async def chat(
        self, messages: List[ChatMessage], options: Optional[BaseGenOptions] = None
    ) -> str:
        raise NotImplementedError
