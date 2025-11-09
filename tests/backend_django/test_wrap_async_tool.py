"""Tests for the wrap_async_tool helper used by LangChain tools."""

import asyncio
import concurrent.futures
import inspect

from agent.tool_utils import wrap_async_tool


async def _sample_async(value: int) -> int:
    await asyncio.sleep(0)
    return value * 2


def test_wrap_async_tool_runs_without_running_loop():
    """The wrapper should use asyncio.run when no loop is active."""
    wrapper = wrap_async_tool(_sample_async)
    result = wrapper(21)
    assert result == 42


def test_wrap_async_tool_uses_existing_running_loop(monkeypatch):
    """The wrapper should submit to an existing event loop."""

    dummy_loop = object()
    captured = {}

    def fake_get_running_loop():
        return dummy_loop

    future = concurrent.futures.Future()
    future.set_result("ok")

    def fake_run_coroutine_threadsafe(coro, loop):
        captured["coro"] = coro
        captured["loop"] = loop
        return future

    monkeypatch.setattr(asyncio, "get_running_loop", fake_get_running_loop)
    monkeypatch.setattr(
        asyncio,
        "run_coroutine_threadsafe",
        fake_run_coroutine_threadsafe,
    )

    wrapper = wrap_async_tool(_sample_async)
    result = wrapper(5)

    assert result == "ok"
    assert captured["loop"] is dummy_loop
    coroutine = captured["coro"]
    assert inspect.iscoroutine(coroutine)
    coroutine.close()
