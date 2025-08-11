import asyncio
import json
from fastmcp import FastMCP, Context
from yad2.mcp import server


async def run_build_url():
    m = FastMCP("test")
    ctx = Context(m)
    result = await server.build_search_url.run({"ctx": ctx, "city": "5000", "topArea": "2"})
    data = json.loads(result.content[0].text)
    assert data["parameters"]["city"] == 5000
    assert data["parameters"]["topArea"] == 2


def test_build_search_url_string_ints():
    asyncio.run(run_build_url())
    schema = server.build_search_url.parameters["properties"]["city"]["anyOf"]
    assert any(s.get("type") == "string" for s in schema)
