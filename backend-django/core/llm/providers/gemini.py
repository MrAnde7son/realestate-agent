from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential

from ..types import BaseGenOptions, ChatMessage, LLMClient


class GeminiAdapter(LLMClient):
    provider = "gemini"

    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

    def _get_model(
        self, json_mode: bool, schema: Optional[Dict[str, Any]] | None = None
    ):
        generation_config: Dict[str, Any] | None = None
        if json_mode:
            generation_config = {
                "response_mime_type": "application/json",
                "response_schema": schema or None,
            }
        return genai.GenerativeModel(
            model_name=self.model_name, generation_config=generation_config
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5))
    async def generate_text(
        self, prompt: str, options: Optional[BaseGenOptions] = None
    ) -> str:
        opts = options or BaseGenOptions()
        model = self._get_model(bool(opts.json), opts.response_schema)
        response = await model.generate_content_async([prompt])
        return response.text

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5))
    async def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        options: Optional[BaseGenOptions] = None,
    ) -> Dict[str, Any]:
        model = self._get_model(True, schema)
        response = await model.generate_content_async([prompt])
        return json.loads(response.text)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5))
    async def chat(
        self, messages: List[ChatMessage], options: Optional[BaseGenOptions] = None
    ) -> str:
        opts = options or BaseGenOptions()
        model = self._get_model(bool(opts.json), opts.response_schema)
        history = [
            {"role": message.role, "parts": [message.content]}
            for message in messages[:-1]
        ]
        session = model.start_chat(history=history)
        last = messages[-1]
        response = await session.send_message_async(last.content)
        return response.text
