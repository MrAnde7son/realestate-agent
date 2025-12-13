import builtins
import importlib
import sys


def test_views_import_is_lazy(monkeypatch):
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "fastmcp":
            raise AssertionError("fastmcp was imported during api_mcp.views import")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    for module_name in ["api_mcp.views", "api_mcp.server", "fastmcp"]:
        sys.modules.pop(module_name, None)

    views_module = importlib.import_module("api_mcp.views")

    assert "api_mcp.server" not in sys.modules
    assert "fastmcp" not in sys.modules
    assert hasattr(views_module, "_get_mcp")


def test_server_import_is_lazy(monkeypatch):
    original_import = builtins.__import__
    fastmcp_attempts = []

    def guarded_import(name, *args, **kwargs):
        if name == "fastmcp":
            fastmcp_attempts.append(name)
            raise AssertionError("fastmcp was imported during api_mcp.server import")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    for module_name in ["api_mcp.server", "fastmcp"]:
        sys.modules.pop(module_name, None)

    server_module = importlib.import_module("api_mcp.server")

    assert server_module._mcp is None
    assert not fastmcp_attempts
