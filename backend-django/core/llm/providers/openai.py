from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from django.conf import settings
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ..types import BaseGenOptions, ChatMessage, LLMClient


class OpenAIAdapter(LLMClient):
    provider = "openai"

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5))
    async def generate_text(
        self, prompt: str, options: Optional[BaseGenOptions] = None
    ) -> str:
        opts = options or BaseGenOptions()
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=opts.temperature,
        )
        return response.choices[0].message.content or ""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5))
    async def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        options: Optional[BaseGenOptions] = None,
    ) -> Dict[str, Any]:
        opts = options or BaseGenOptions(json=True)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\nReturn ONLY strict JSON that conforms to the provided schema.",
                }
            ],
            temperature=opts.temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        return data

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5))
    async def chat(
        self, messages: List[ChatMessage], options: Optional[BaseGenOptions] = None
    ) -> str:
        opts = options or BaseGenOptions()
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[message.model_dump() for message in messages],
            temperature=opts.temperature,
        )
        return response.choices[0].message.content or ""
