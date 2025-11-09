"""Conversation memory management utilities for the real estate agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Dict, Optional


@dataclass
class ConversationMessage:
    """A single conversation message."""

    role: str
    content: str

    def as_dict(self) -> Dict[str, str]:
        """Return the message as a serialisable dictionary."""
        return {"role": self.role, "content": self.content}


class ConversationMemory:
    """Simple in-memory conversation buffer with bounded size."""

    def __init__(self, max_messages: int = 20) -> None:
        if max_messages <= 0:
            raise ValueError("max_messages must be a positive integer")
        self._max_messages = max_messages
        self._messages: List[ConversationMessage] = []

    @property
    def max_messages(self) -> int:
        """Maximum number of messages stored in memory."""
        return self._max_messages

    def clear(self) -> None:
        """Remove all stored messages."""
        self._messages.clear()

    def add_message(self, role: str, content: Optional[str]) -> None:
        """Add a message to the memory, trimming the buffer if needed."""
        safe_role = (role or "user").strip() or "user"
        safe_content = (content or "").strip()
        self._messages.append(
            ConversationMessage(role=safe_role, content=safe_content)
        )
        self._trim_to_limit()

    def add_user_message(self, content: Optional[str]) -> None:
        """Convenience wrapper for adding user messages."""
        self.add_message("user", content)

    def add_ai_message(self, content: Optional[str]) -> None:
        """Convenience wrapper for adding assistant messages."""
        self.add_message("assistant", content)

    def append_interaction(
        self,
        user_message: Optional[str],
        assistant_message: Optional[str] = None,
    ) -> None:
        """Store a user/assistant interaction."""
        self.add_user_message(user_message)
        if assistant_message is not None:
            self.add_ai_message(assistant_message)

    def extend(self, messages: Iterable[Dict[str, str]]) -> None:
        """Append multiple messages to the memory."""
        for message in messages:
            if not isinstance(message, dict):
                continue
            self.add_message(
                message.get("role", "user"),
                message.get("content"),
            )

    def replace(self, messages: Iterable[Dict[str, str]]) -> None:
        """Replace memory with provided messages."""
        self.clear()
        self.extend(messages)

    def build_history(
        self, external_history: Optional[Iterable[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """Return sanitised history syncing with external data."""
        if external_history is not None:
            sanitized = [
                {
                    "role": (msg.get("role") or "user").strip() or "user",
                    "content": (msg.get("content") or "").strip(),
                }
                for msg in external_history
                if isinstance(msg, dict)
            ]
            self.replace(sanitized)
        return [msg.as_dict() for msg in self._messages]

    def _trim_to_limit(self) -> None:
        """Trim stored messages to respect the configured limit."""
        excess = len(self._messages) - self._max_messages
        if excess > 0:
            del self._messages[:excess]

    def get_messages(self) -> List[Dict[str, str]]:
        """Return a copy of stored messages."""
        return [msg.as_dict() for msg in self._messages]


__all__ = ["ConversationMemory", "ConversationMessage"]
