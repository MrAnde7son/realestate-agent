"""Tests for agent token budgeting and compression helpers."""

import sys
import types
from importlib import util
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "backend-django"
    / "agent"
    / "real_estate_agent.py"
)

# Create package placeholders so relative imports work
backend_pkg = types.ModuleType("backend_django")
backend_pkg.__path__ = [str(MODULE_PATH.parents[1])]
sys.modules.setdefault("backend_django", backend_pkg)

agent_pkg = types.ModuleType("backend_django.agent")
agent_pkg.__path__ = [str(MODULE_PATH.parent)]
sys.modules.setdefault("backend_django.agent", agent_pkg)

# Stub external dependencies that are unnecessary for helper tests
langchain_core = types.ModuleType("langchain_core")
sys.modules.setdefault("langchain_core", langchain_core)

langchain_core.tools = types.ModuleType("langchain_core.tools")


class _BaseTool:  # pragma: no cover - simple stub
    pass


class _StructuredTool(_BaseTool):  # pragma: no cover - simple stub
    pass


langchain_core.tools.BaseTool = _BaseTool
langchain_core.tools.StructuredTool = _StructuredTool
sys.modules.setdefault("langchain_core.tools", langchain_core.tools)

langchain_core.callbacks = types.ModuleType("langchain_core.callbacks")


class _BaseCallbackHandler:  # pragma: no cover - simple stub
    pass


langchain_core.callbacks.BaseCallbackHandler = _BaseCallbackHandler
sys.modules.setdefault("langchain_core.callbacks", langchain_core.callbacks)

langchain_openai = types.ModuleType("langchain_openai")


class _ChatOpenAI:  # pragma: no cover - simple stub
    def __init__(self, *args, **kwargs):
        pass


langchain_openai.ChatOpenAI = _ChatOpenAI
sys.modules.setdefault("langchain_openai", langchain_openai)

langchain_google_genai = types.ModuleType("langchain_google_genai")


class _ChatGoogleGenerativeAI:  # pragma: no cover - simple stub
    def __init__(self, *args, **kwargs):
        pass


langchain_google_genai.ChatGoogleGenerativeAI = _ChatGoogleGenerativeAI
sys.modules.setdefault("langchain_google_genai", langchain_google_genai)

langchain_agents = types.ModuleType("langchain.agents")


class _AgentExecutor:  # pragma: no cover - simple stub
    def __init__(self, *args, **kwargs):
        pass


def _create_openai_tools_agent(*args, **kwargs):  # pragma: no cover - simple stub
    return object()


langchain_agents.AgentExecutor = _AgentExecutor
langchain_agents.create_openai_tools_agent = _create_openai_tools_agent
sys.modules.setdefault("langchain.agents", langchain_agents)

langchain_prompts = types.ModuleType("langchain.prompts")


class _ChatPromptTemplate:  # pragma: no cover - simple stub
    @classmethod
    def from_messages(cls, messages):
        return messages


class _MessagesPlaceholder:  # pragma: no cover - simple stub
    def __init__(self, variable_name: str):
        self.variable_name = variable_name


langchain_prompts.ChatPromptTemplate = _ChatPromptTemplate
langchain_prompts.MessagesPlaceholder = _MessagesPlaceholder
sys.modules.setdefault("langchain.prompts", langchain_prompts)

spec = util.spec_from_file_location(
    "backend_django.agent.real_estate_agent",
    MODULE_PATH,
)
real_estate_agent = util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(real_estate_agent)  # type: ignore[assignment]

build_history_with_summary = real_estate_agent.build_history_with_summary
compress_tool_output = real_estate_agent.compress_tool_output
enforce_token_budget = real_estate_agent.enforce_token_budget


@pytest.fixture(autouse=True)
def patch_tokenizer(monkeypatch):
    class DummyTokenizer:
        def encode(self, text: str):
            return list(text.encode("utf-8"))

    monkeypatch.setattr(real_estate_agent, "_get_tokenizer", lambda: DummyTokenizer())


def test_build_history_with_summary_adds_summary_message():
    history = [
        {"role": "user", "content": "מה מצב הפרויקט?"},
        {"role": "assistant", "content": "הפרויקט מתקדם"},
        {"role": "user", "content": "מה העלות?"},
        {"role": "assistant", "content": "כ-2 מיליון"},
        {"role": "user", "content": "ומה לוחות הזמנים?"},
        {"role": "assistant", "content": "12 חודשים"},
    ]

    summarized = build_history_with_summary(history, keep_last=2, summary_max_chars=180)

    assert summarized[0]["role"] == "system"
    assert "תקציר" in summarized[0]["content"]
    assert len(summarized) == 3
    assert summarized[1:] == history[-2:]


def test_enforce_token_budget_trims_old_messages():
    messages = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "first" + " x" * 300},
        {"role": "assistant", "content": "second" + " y" * 300},
        {"role": "user", "content": "latest"},
    ]

    trimmed = enforce_token_budget(messages, max_tokens=300, reserve_for_output=0)

    # Always keeps the newest user message
    assert trimmed[-1]["content"] == "latest"
    # Older messages should be summarized away
    assert any(msg["content"].startswith("[history summarized") for msg in trimmed)


def test_compress_tool_output_truncates_long_text():
    long_text = "start " + "middle " * 400 + " end"

    compressed = compress_tool_output(long_text, max_chars=1200)

    assert "..." in compressed
    assert compressed.startswith("start")
    assert compressed.strip().endswith("end")
