from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from google.api_core.client_options import ClientOptions
import google.generativeai as genai
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential

from ..types import BaseGenOptions, ChatMessage, LLMClient

# Google API exceptions for error handling
try:
    from google.api_core import exceptions as google_exceptions
except ImportError:
    google_exceptions = None


class GeminiAdapter(LLMClient):
    provider = "gemini"

    @staticmethod
    def _classify_error(exception: Exception) -> Optional[Dict[str, str]]:
        """
        Classify Google API exceptions and return structured error info.
        Returns None if the exception is not a Google API exception.
        """
        if not google_exceptions:
            return None

        error_msg = str(exception).lower()
        actual_exception = exception

        # Unwrap if it's wrapped in another exception
        if hasattr(exception, "__cause__") and exception.__cause__:
            actual_exception = exception.__cause__
            error_msg = str(actual_exception).lower()
        elif hasattr(exception, "__context__") and exception.__context__:
            actual_exception = exception.__context__
            error_msg = str(actual_exception).lower()

        # Check for rate limit errors
        if (
            isinstance(actual_exception, google_exceptions.TooManyRequests)
            or "too many requests" in error_msg
            or "quota exceeded" in error_msg
            or "rate limit" in error_msg
        ):
            return {
                "type": "rate_limit",
                "message": "API rate limit exceeded. Please try again in a minute.",
                "details": str(actual_exception),
            }

        # Check for model not found errors
        if (
            isinstance(actual_exception, google_exceptions.NotFound)
            or "not found" in error_msg
            or "404" in error_msg
        ):
            return {
                "type": "model_not_found",
                "message": "AI model not available. Please check your API configuration.",
                "details": str(actual_exception),
            }

        # Check for invalid argument errors
        if isinstance(actual_exception, google_exceptions.InvalidArgument):
            return {
                "type": "invalid_request",
                "message": "Invalid request to AI service. Please try again.",
                "details": str(actual_exception),
            }

        # Check for permission denied errors
        if isinstance(actual_exception, google_exceptions.PermissionDenied):
            return {
                "type": "permission_denied",
                "message": "API access denied. Please check your API key configuration.",
                "details": str(actual_exception),
            }

        # Check for service unavailable errors
        if isinstance(actual_exception, google_exceptions.ServiceUnavailable):
            return {
                "type": "service_unavailable",
                "message": "AI service is temporarily unavailable. Please try again later.",
                "details": str(actual_exception),
            }

        return None

    def __init__(self) -> None:
        api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured")
        genai.configure(
            api_key=api_key,
            client_options=ClientOptions(
                api_endpoint="https://generativelanguage.googleapis.com"
            ),
            transport="rest",
        )
        self.model_name = settings.GEMINI_MODEL

    def _get_model(
        self,
        json_mode: bool,
        schema: Optional[Dict[str, Any]] | None = None,
        system_instruction: Optional[str] | None = None,
    ):
        generation_config: Dict[str, Any] | None = None
        if json_mode:
            generation_config = {
                "response_mime_type": "application/json",
                "response_schema": schema or None,
            }
        return genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            system_instruction=system_instruction,
        )

    @staticmethod
    def _prepare_chat_messages(
        messages: List[ChatMessage],
    ) -> tuple[Optional[str], List[Dict[str, Any]], Dict[str, Any]]:
        if not messages:
            raise ValueError("No chat messages provided")

        system_parts: List[str] = []
        normalized: List[Dict[str, Any]] = []

        for message in messages:
            if message.role == "system":
                system_parts.append(message.content)
                continue

            role = "user" if message.role == "user" else "model"
            normalized.append({"role": role, "parts": [message.content]})

        if not normalized:
            raise ValueError("At least one user or assistant message is required")

        system_instruction = "\n\n".join(system_parts) if system_parts else None
        history = normalized[:-1]
        last_message = normalized[-1]

        return system_instruction, history, last_message

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5))
    async def generate_text(
        self, prompt: str, options: Optional[BaseGenOptions] = None
    ) -> str:
        opts = options or BaseGenOptions()
        model = self._get_model(bool(opts.json_mode), opts.response_schema)
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
        self,
        messages: List[ChatMessage],
        options: Optional[BaseGenOptions] = None,
    ) -> str:
        opts = options or BaseGenOptions()
        (
            system_instruction,
            history,
            last_message,
        ) = self._prepare_chat_messages(messages)
        if last_message["role"] != "user":
            raise ValueError("The last chat message must have role 'user'")

        model = self._get_model(
            bool(opts.json_mode), opts.response_schema, system_instruction
        )
        session = model.start_chat(history=history)
        response = await session.send_message_async(last_message["parts"][0])
        return response.text
