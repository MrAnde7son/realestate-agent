import importlib
import sys
import types
from pathlib import Path
from types import SimpleNamespace


def test_get_mcp_is_lazy_and_registers_once(monkeypatch):
    """FastMCP should be created only when requested and tools registered once."""

    import fastmcp

    project_root = Path(__file__).resolve().parents[2]
    backend_pkg = types.ModuleType("backend_django")
    backend_pkg.__path__ = [str(project_root / "backend-django")]
    sys.modules.setdefault("backend_django", backend_pkg)

    api_pkg = types.ModuleType("backend_django.api_mcp")
    api_pkg.__path__ = [str(project_root / "backend-django" / "api_mcp")]
    sys.modules.setdefault("backend_django.api_mcp", api_pkg)

    created_instances = []
    tool_registrations = []

    class DummyFastMCP:
        def __init__(self, name, instructions=None):
            created_instances.append((name, instructions))
            self._tool_manager = SimpleNamespace(_tools={})

        def tool(self, description=None):  # noqa: D401 - simple wrapper
            def decorator(func):
                self._tool_manager._tools[func.__name__] = func
                tool_registrations.append(func.__name__)
                return func

            return decorator

        def run(self):
            return None

    monkeypatch.setattr(fastmcp, "FastMCP", DummyFastMCP)
    monkeypatch.setattr(fastmcp, "Context", object)

    sys.modules.pop("backend_django.api_mcp.server", None)
    server = importlib.import_module("backend_django.api_mcp.server")

    # Importing the module should not create the MCP server
    assert created_instances == []

    mcp_instance = server.get_mcp()

    assert isinstance(mcp_instance, DummyFastMCP)
    assert created_instances == [("RealEstateAPI", "Real-estate API tools.")]
    assert server._tools_registered is True
    first_tool_count = len(mcp_instance._tool_manager._tools)
    assert first_tool_count > 0

    # Subsequent calls should reuse the same instance and avoid double registration
    second_instance = server.get_mcp()
    assert second_instance is mcp_instance
    assert len(mcp_instance._tool_manager._tools) == first_tool_count
    assert tool_registrations  # at least one registration occurred
