from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel

LLMProvider = Literal["gemini", "openai", "groq"]


class BaseGenOptions(BaseModel):
    temperature: float = 0.2
    json_mode: bool = False
    response_schema: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMClient(ABC):
    provider: LLMProvider

    @abstractmethod
    async def generate_text(
        self, prompt: str, options: Optional[BaseGenOptions] = None
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        options: Optional[BaseGenOptions] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def chat(
        self, messages: List[ChatMessage], options: Optional[BaseGenOptions] = None
    ) -> str:
        raise NotImplementedError
