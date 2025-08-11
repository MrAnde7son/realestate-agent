import asyncio
import types
from yad2.mcp import server

class DummyCtx:
    async def info(self, msg: str):
        pass

async def run_build_url():
    result = await server.build_search_url.fn(DummyCtx(), city="5000", topArea="2")
    assert result["parameters"]["city"] == 5000
    assert result["parameters"]["topArea"] == 2


def test_build_search_url_string_ints():
    asyncio.run(run_build_url())
