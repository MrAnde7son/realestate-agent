import asyncio
import json
from unittest import mock

import requests
from fastmcp import FastMCP, Context

from gov.mcp import server


def _make_response(text: str = "", status: int = 200):
    r = requests.Response()
    r.status_code = status
    r._content = text.encode("utf-8")
    return r


def test_decisive_appraisal_tool():
    html_page = (
        '<ul>'
        '<li class="collector-result-item">'
        '  <a href="/BlobFolder/1.pdf">Decision 1</a>'
        '  <span>תאריך: 01/01/2024</span>'
        '  <span>שמאי: ישראל ישראלי</span>'
        '  <span>ועדה: תל אביב</span>'
        '</li>'
        '<li class="collector-result-item">'
        '  <a href="/BlobFolder/2.pdf">Decision 2</a>'
        '  <span>תאריך: 02/02/2024</span>'
        '  <span>שמאי: רונית שמאית</span>'
        '  <span>ועדה: חיפה</span>'
        '</li>'
        '</ul>'
    )

    def fake_get(url, params=None, headers=None, timeout=None):
        if params.get("skip") == 0:
            return _make_response(html_page)
        return _make_response("<ul></ul>")

    async def run_tool():
        m = FastMCP("test")
        ctx = Context(m)
        with mock.patch("requests.get", side_effect=fake_get):
            result = await server.decisive_appraisal.run(
                {"ctx": ctx, "block": "123", "plot": "456"}
            )
            data = json.loads(result.content[0].text)
            assert len(data) == 2
            assert data[0]["title"] == "Decision 1"
            assert data[0]["pdf_url"].startswith("https://www.gov.il/BlobFolder/1.pdf")

    asyncio.run(run_tool())
