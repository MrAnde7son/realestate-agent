#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handasa FastMCP Server."""

import asyncio
import base64
import os
import sys
from typing import Any, Dict, Optional

from fastmcp import Context, FastMCP

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from handasa.client import HandasaClient

mcp = FastMCP(
    "HandasaTelAviv",
    dependencies=["requests"],
)

_client: Optional[HandasaClient] = None


def _get_client() -> HandasaClient:
    global _client
    if _client is None:
        timeout = float(os.getenv("HANDASA_TIMEOUT", "90"))
        _client = HandasaClient(timeout=timeout)
    return _client


def _should_retry(attempt: int, retries: int) -> bool:
    return attempt < retries


@mcp.tool()
async def handasa_archive(
    ctx: Context,
    block: str,
    parcel: Optional[str] = None,
    page_size: int = 50,
) -> Dict[str, Any]:
    """Fetch the Handasa permit archive for a given block/parcel."""

    if not block:
        raise ValueError("'block' is required")

    client = _get_client()
    retries = int(os.getenv("HANDASA_RETRIES", "0"))
    delay = float(os.getenv("HANDASA_RETRY_DELAY", "1.0"))

    attempt = 0
    last_error: Optional[Exception] = None

    while True:
        try:
            await ctx.info(
                f"Fetching Handasa archive for block={block} parcel={parcel or '-'}"
            )
            documents = client.get_archive(
                block=block, parcel=parcel, page_size=int(page_size)
            )
            return {
                "success": True,
                "block": block,
                "parcel": parcel,
                "count": len(documents),
                "documents": documents,
            }
        except Exception as exc:  # pragma: no cover - network errors handled via retry
            last_error = exc
            await ctx.error(f"Handasa archive fetch failed: {exc}")
            if _should_retry(attempt, retries):
                attempt += 1
                await asyncio.sleep(delay)
                continue
            break

    raise RuntimeError(f"Failed to fetch Handasa archive: {last_error}")


@mcp.tool()
async def download_handasa_document(
    ctx: Context,
    unique_id: str,
    save_to: Optional[str] = None,
    overwrite: bool = False,
    return_content: bool = False,
) -> Dict[str, Any]:
    """Download a document from the Handasa portal."""

    if not unique_id:
        raise ValueError("'unique_id' is required")

    client = _get_client()
    await ctx.info(f"Downloading Handasa document {unique_id}")

    payload = client.download_document(
        unique_id=unique_id, save_to=save_to, overwrite=overwrite
    )

    result: Dict[str, Any] = {
        "success": True,
        "unique_id": unique_id,
        "file_name": payload.get("file_name"),
        "content_type": payload.get("content_type"),
        "size": payload.get("size", 0),
    }

    file_path = payload.get("file_path")
    if file_path:
        result["file_path"] = str(file_path)

    if return_content:
        content_bytes = payload.get("content", b"") or b""
        result["content_base64"] = base64.b64encode(content_bytes).decode("utf-8")

    return result


if __name__ == "__main__":
    mcp.run()
