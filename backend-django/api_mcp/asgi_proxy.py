"""Utilities for exposing FastMCP ASGI applications via Django views.

This module provides a thin wrapper that allows us to forward traditional
WSGI-based Django requests to the FastMCP ASGI application that powers the
Real Estate API MCP server.  The wrapper maintains the ASGI contract, keeps
the application's lifespan management intact, and streams the response back
to the caller so long-running SSE responses continue to function correctly.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass
from queue import SimpleQueue
from typing import Awaitable, Callable, Iterable, Iterator, Optional

from django.http import HttpRequest, StreamingHttpResponse

logger = logging.getLogger(__name__)


ASGIReceive = Callable[[], Awaitable[dict]]
ASGISend = Callable[[dict], Awaitable[None]]
ASGIApp = Callable[[dict, ASGIReceive, ASGISend], Awaitable[None]]


@dataclass
class _ResponseState:
    """Container holding the mutable response state for a proxied request."""

    status: int = 200
    headers: list[tuple[bytes, bytes]] = None  # type: ignore[assignment]


class ASGIApplicationProxy:
    """Bridge a FastMCP ASGI application so it can serve Django requests.

    The proxy spins an event loop in a background thread for each request,
    streams response chunks through a thread-safe queue, and exposes a
    Django ``StreamingHttpResponse`` back to the caller.
    """

    def __init__(self, app_factory: Callable[[], ASGIApp]) -> None:
        self._app_factory = app_factory

    def _get_app(self) -> ASGIApp:
        return self._app_factory()

    def handle(self, request: HttpRequest) -> StreamingHttpResponse:
        """Proxy the incoming ``HttpRequest`` to the ASGI application."""

        app = self._get_app()
        scope = self._build_scope(request)

        body_bytes = request.body or b""
        response_state = _ResponseState(status=200, headers=[])
        start_event = threading.Event()
        finished_event = threading.Event()
        queue: SimpleQueue[Optional[bytes]] = SimpleQueue()
        error_holder: dict[str, BaseException] = {}

        # These will be populated inside the worker thread where the event loop lives
        loop_holder: dict[str, asyncio.AbstractEventLoop] = {}
        disconnect_event_holder: dict[str, asyncio.Event] = {}

        def worker() -> None:
            """Run the ASGI app inside an isolated event loop."""

            async def run_app() -> None:
                nonlocal response_state

                disconnect_event = asyncio.Event()
                disconnect_event_holder["event"] = disconnect_event

                body_iter: Iterator[bytes] = iter([body_bytes])
                body_sent = False
                body_complete = False

                async def receive() -> dict:
                    nonlocal body_sent
                    if not body_sent:
                        body_sent = True
                        body = next(body_iter, b"")
                        return {
                            "type": "http.request",
                            "body": body,
                            "more_body": False,
                        }

                    await disconnect_event.wait()
                    return {"type": "http.disconnect"}

                async def send(message: dict) -> None:
                    nonlocal body_complete

                    message_type = message.get("type")
                    if message_type == "http.response.start":
                        response_state.status = message.get("status", 200)
                        response_state.headers = message.get("headers", [])
                        start_event.set()
                    elif message_type == "http.response.body":
                        if not start_event.is_set():
                            start_event.set()

                        chunk = message.get("body", b"")
                        if chunk:
                            queue.put(chunk)

                        more_body = message.get("more_body", False)
                        if not more_body and not body_complete:
                            body_complete = True
                            queue.put(None)
                    else:
                        logger.debug("Unhandled ASGI message type: %s", message_type)

                try:
                    async with app.lifespan(app):  # type: ignore[attr-defined]
                        await app(scope, receive, send)
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.exception("MCP ASGI application failed", exc_info=exc)
                    error_holder["exception"] = exc
                    if not start_event.is_set():
                        start_event.set()
                        queue.put(None)
                finally:
                    if not start_event.is_set():
                        start_event.set()
                    if not body_complete:
                        queue.put(None)
                    finished_event.set()

            loop = asyncio.new_event_loop()
            loop_holder["loop"] = loop
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_app())
            finally:
                loop.close()

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        start_event.wait()

        if "exception" in error_holder:
            thread.join(timeout=1)
            raise error_holder["exception"]

        def stream() -> Iterable[bytes]:
            try:
                while True:
                    chunk = queue.get()
                    if chunk is None:
                        break
                    yield chunk
            finally:
                disconnect_event = disconnect_event_holder.get("event")
                loop = loop_holder.get("loop")
                if disconnect_event and loop:
                    loop.call_soon_threadsafe(disconnect_event.set)
                finished_event.wait(timeout=1)
                thread.join(timeout=1)

        response = StreamingHttpResponse(stream(), status=response_state.status)
        for name, value in response_state.headers:
            try:
                header_name = name.decode("latin-1")
                header_value = value.decode("latin-1")
            except Exception:  # pragma: no cover - defensive
                continue

            if header_name.lower() == "set-cookie":
                response.cookies.load(header_value)
            else:
                response.headers[header_name] = header_value

        return response

    @staticmethod
    def _build_scope(request: HttpRequest) -> dict:
        """Build an ASGI scope from the Django ``HttpRequest``."""

        headers = [
            (key.lower().encode("latin-1"), value.encode("latin-1"))
            for key, value in request.headers.items()
        ]

        server_host = request.get_host().split(":", 1)[0]
        try:
            server_port = int(request.get_port())
        except (TypeError, ValueError):  # pragma: no cover - defensive
            server_port = 80

        client_addr = request.META.get("REMOTE_ADDR")
        client_port = request.META.get("REMOTE_PORT")
        client_tuple: Optional[tuple[str, int]] = None
        if client_addr:
            try:
                client_tuple = (client_addr, int(client_port))  # type: ignore[arg-type]
            except (TypeError, ValueError):  # pragma: no cover - defensive
                client_tuple = (client_addr, 0)

        http_version = request.META.get("SERVER_PROTOCOL", "HTTP/1.1").split("/", 1)[-1]

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": http_version,
            "method": request.method,
            "scheme": request.scheme,
            "path": request.path,
            "raw_path": request.get_full_path().encode("utf-8"),
            "query_string": request.META.get("QUERY_STRING", "").encode("utf-8"),
            "headers": headers,
            "client": client_tuple,
            "server": (server_host, server_port),
        }

        return scope
