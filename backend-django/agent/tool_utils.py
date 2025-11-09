"""Utility helpers for LangChain tool integration."""

from __future__ import annotations

import asyncio
import functools
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


def wrap_async_tool(
    async_func: Callable[..., Awaitable[T]],
) -> Callable[..., T]:
    """Wrap an async function for LangChain's synchronous tool interface.

    If no event loop is running the coroutine executes with
    :func:`asyncio.run`. When a loop is active in the current thread the
    coroutine is scheduled on that loop via
    :func:`asyncio.run_coroutine_threadsafe` and the result is awaited with a
    timeout.
    """

    @functools.wraps(async_func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(async_func(*args, **kwargs))

        future = asyncio.run_coroutine_threadsafe(
            async_func(*args, **kwargs),
            loop,
        )
        return future.result(timeout=60)

    return sync_wrapper
