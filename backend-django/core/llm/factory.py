from django.conf import settings

from .providers.gemini import GeminiAdapter
from .providers.openai import OpenAIAdapter
from .types import LLMClient, LLMProvider


def create_llm_client(provider: LLMProvider | None = None) -> LLMClient:
    selected = provider or settings.LLM_DEFAULT_PROVIDER
    if selected == "gemini":
        try:
            return GeminiAdapter()
        except ValueError:
            if provider is None and settings.OPENAI_API_KEY:
                return OpenAIAdapter()
            raise
    if selected == "openai":
        try:
            return OpenAIAdapter()
        except ValueError:
            if provider is None and settings.GEMINI_API_KEY:
                return GeminiAdapter()
            raise
    raise ValueError(f"Unknown LLM provider: {selected}")
