import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_PATH = ROOT_DIR / "backend-django"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from agent.memory import ConversationMemory  # noqa: E402


def test_add_and_retrieve_messages():
    memory = ConversationMemory(max_messages=5)
    memory.add_user_message("  שלום  ")
    memory.add_ai_message(" היי ")

    messages = memory.get_messages()
    assert messages == [
        {"role": "user", "content": "שלום"},
        {"role": "assistant", "content": "היי"},
    ]


def test_memory_limit_trims_old_messages():
    memory = ConversationMemory(max_messages=4)
    for idx in range(3):
        memory.append_interaction(f"שאלה {idx}", f"תשובה {idx}")

    messages = memory.get_messages()
    assert len(messages) == 4
    assert messages[0]["content"] == "שאלה 1"
    assert messages[1]["content"] == "תשובה 1"
    assert messages[2]["content"] == "שאלה 2"
    assert messages[3]["content"] == "תשובה 2"


def test_build_history_sanitises_external_input():
    memory = ConversationMemory(max_messages=5)
    external = [
        {"role": "user", "content": " שלום"},
        {"role": "assistant", "content": " מה נשמע? "},
        {"role": None, "content": None},
    ]

    history = memory.build_history(external)
    assert history == [
        {"role": "user", "content": "שלום"},
        {"role": "assistant", "content": "מה נשמע?"},
        {"role": "user", "content": ""},
    ]

    external[0]["content"] = "משתנה"
    assert memory.get_messages()[0]["content"] == "שלום"


def test_append_interaction_without_assistant_message():
    memory = ConversationMemory(max_messages=5)
    memory.append_interaction("שאלה", None)

    messages = memory.get_messages()
    assert messages == [{"role": "user", "content": "שאלה"}]


def test_invalid_max_messages():
    with pytest.raises(ValueError):
        ConversationMemory(max_messages=0)
