import json
from typing import Optional, cast

from django.conf import settings

from .factory import create_llm_client
from .types import LLMProvider


def _normalize_provider(provider: Optional[str]) -> Optional[LLMProvider]:
    if provider in ("gemini", "openai"):
        return cast(LLMProvider, provider)
    return None


def pick_provider_from_request(request) -> Optional[LLMProvider]:
    if not settings.LLM_ALLOW_OVERRIDE:
        return None

    provider = _normalize_provider(request.GET.get("provider"))
    if provider:
        return provider

    header_provider = _normalize_provider(request.headers.get("X-LLM-Provider"))
    if header_provider:
        return header_provider

    try:
        body = request.body.decode("utf-8")
        if body and '"provider"' in body:
            payload = json.loads(body)
            if isinstance(payload, dict):
                return _normalize_provider(payload.get("provider"))
    except Exception:
        pass

    return None


def get_llm(request):
    provider = pick_provider_from_request(request)
    return create_llm_client(provider)
