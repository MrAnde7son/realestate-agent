#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Real Estate Agent

A conversational AI agent built with LangChain that can help with real estate tasks
using the MCP server tools for assets, deals, expenses, mortgage calculations, and CRM.
"""

import os
import sys
import importlib.util
import asyncio
import time
import logging
from typing import List, Optional, Dict, Any, Callable

from functools import lru_cache

# Add backend-django directory to path before agent imports
backend_django_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_django_path not in sys.path:
    sys.path.insert(0, backend_django_path)

# Load .env file if available (before any environment variable access)
try:
    from dotenv import load_dotenv
    # Try to find .env file in project root or backend-django directory
    project_root = os.path.abspath(os.path.join(backend_django_path, ".."))
    env_file = os.path.join(project_root, '.env')
    if not os.path.exists(env_file):
        env_file = os.path.join(backend_django_path, '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file, override=False)
except ImportError:
    # python-dotenv not available, skip
    pass
except Exception:
    # Ignore errors loading .env file
    pass

logger = logging.getLogger(__name__)

from agent.internet_fetcher import get_fetcher
from agent.memory import ConversationMemory

# LangChain imports
from langchain_core.tools import BaseTool, StructuredTool
from langchain_core.callbacks import BaseCallbackHandler
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field

from agent.tool_utils import wrap_async_tool

# Import MCP server functions dynamically
_agent_import_error = None
try:
    mcp_server_path = os.path.join(os.path.dirname(__file__), "..", "api_mcp", "server.py")
    if not os.path.exists(mcp_server_path):
        raise ImportError(f"MCP server file not found at {mcp_server_path}")
    
    spec = importlib.util.spec_from_file_location("mcp_server", mcp_server_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load MCP server from {mcp_server_path}")
    
    mcp_server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mcp_server)
    
    # Import functions from MCP server
    # FastMCP decorates functions as FunctionTool objects, so we need to access the underlying function
    # Use .fn attribute to get the actual async function
    def get_underlying_func(tool_obj):
        """Extract the underlying async function from a FastMCP FunctionTool."""
        if hasattr(tool_obj, 'fn') and callable(tool_obj.fn):
            return tool_obj.fn
        else:
            # Fallback: return as-is (shouldn't happen)
            return tool_obj
    
    list_assets = get_underlying_func(mcp_server.list_assets)
    get_asset_filters = get_underlying_func(mcp_server.get_asset_filters)
    get_asset = get_underlying_func(mcp_server.get_asset)
    create_asset = get_underlying_func(mcp_server.create_asset)
    get_asset_data = get_underlying_func(mcp_server.get_asset_data)
    list_deals = get_underlying_func(mcp_server.list_deals)
    create_deal = get_underlying_func(mcp_server.create_deal)
    get_offer = get_underlying_func(mcp_server.get_offer)
    estimate_build_cost = get_underlying_func(mcp_server.estimate_build_cost)
    get_cost_options = get_underlying_func(mcp_server.get_cost_options)
    calculate_deal_expenses = get_underlying_func(mcp_server.calculate_deal_expenses)
    analyze_mortgage = get_underlying_func(mcp_server.analyze_mortgage)
    list_contacts = get_underlying_func(mcp_server.list_contacts)
    create_contact = get_underlying_func(mcp_server.create_contact)
    list_leads = get_underlying_func(mcp_server.list_leads)
    create_lead = get_underlying_func(mcp_server.create_lead)
    list_tasks = get_underlying_func(mcp_server.list_tasks)
except Exception as e:
    # MCP server not available - create stub functions
    import warnings
    _agent_import_error = str(e)
    warnings.warn(f"MCP server not available: {e}. Agent will have limited functionality.")
    
    async def _stub_func(*args, **kwargs):
        error_msg = f"MCP server not available. Error: {_agent_import_error}. Please ensure fastmcp is installed: pip install fastmcp"
        return {"success": False, "error": error_msg}
    
    list_assets = _stub_func
    get_asset_filters = _stub_func
    get_asset = _stub_func
    create_asset = _stub_func
    get_asset_data = _stub_func
    list_deals = _stub_func
    create_deal = _stub_func
    get_offer = _stub_func
    estimate_build_cost = _stub_func
    get_cost_options = _stub_func
    calculate_deal_expenses = _stub_func
    analyze_mortgage = _stub_func
    list_contacts = _stub_func
    create_contact = _stub_func
    list_leads = _stub_func
    create_lead = _stub_func
    list_tasks = _stub_func


# Patch LangChain's parse_ai_message_to_tool_action to handle None args
# This must be done BEFORE any LangChain imports that use this function
def _patch_langchain_tool_parser():
    """Patch LangChain's tool parser to handle None tool call args.
    
    The error occurs in tools.py line 63-64:
    _tool_input = tool_call["args"]  # This can be None
    tool_input = _tool_input.get("__arg1", _tool_input)  # Fails if _tool_input is None
    
    We patch both the function AND patch it in openai_tools.py which also calls it.
    """
    try:
        # Patch in tools module
        from langchain.agents.output_parsers import tools as tools_module
        from langchain.agents.output_parsers import openai_tools as openai_tools_module
        import json
        
        # Save original functions
        _original_parse_tools = tools_module.parse_ai_message_to_tool_action
        _original_parse_openai = openai_tools_module.parse_ai_message_to_openai_tool_action
        
        def _safe_parse_ai_message_to_tool_action(message):
            """Wrapper that handles None tool call args."""
            logger.debug("Patched parse_ai_message_to_tool_action called")
            # CRITICAL: Fix additional_kwargs BEFORE parsing
            if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
                tool_calls_raw = message.additional_kwargs.get("tool_calls", [])
                if tool_calls_raw:
                    for tool_call_dict in tool_calls_raw:
                        if isinstance(tool_call_dict, dict):
                            func = tool_call_dict.get("function", {})
                            if isinstance(func, dict):
                                arguments = func.get("arguments")
                                # Fix None, empty, or JSON "null" string
                                if arguments is None or arguments == "" or arguments == "null" or arguments == "None":
                                    func["arguments"] = "{}"
                                # Also validate it's valid JSON
                                try:
                                    parsed = json.loads(func["arguments"])
                                    if parsed is None:  # json.loads("null") returns None
                                        func["arguments"] = "{}"
                                except json.JSONDecodeError:
                                    func["arguments"] = "{}"
            
            # Fix existing tool_calls
            # ToolCall is a TypedDict, so we can't use isinstance()
            # Instead, check if it has the expected attributes
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    # Check if it's a ToolCall-like object (has 'args' attribute/key)
                    if hasattr(tool_call, 'args'):
                        if tool_call.args is None:
                            tool_call.args = {}
                        elif not isinstance(tool_call.args, dict):
                            tool_call.args = {}
                    elif isinstance(tool_call, dict) and 'args' in tool_call:
                        # Handle dict-like ToolCall
                        if tool_call.get('args') is None:
                            tool_call['args'] = {}
                        elif not isinstance(tool_call.get('args'), dict):
                            tool_call['args'] = {}
            
            # Call original with error handling
            try:
                return _original_parse_tools(message)
            except AttributeError as e:
                if "'NoneType' object has no attribute 'get'" in str(e):
                    logger.warning("Caught NoneType error, fixing and retrying...")
                    # Re-fix everything
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        for tool_call in message.tool_calls:
                            # Handle both object and dict-like ToolCall
                            if hasattr(tool_call, 'args') and tool_call.args is None:
                                tool_call.args = {}
                            elif isinstance(tool_call, dict) and tool_call.get('args') is None:
                                tool_call['args'] = {}
                    if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
                        tool_calls_raw = message.additional_kwargs.get("tool_calls", [])
                        if tool_calls_raw:
                            for tool_call_dict in tool_calls_raw:
                                if isinstance(tool_call_dict, dict):
                                    func = tool_call_dict.get("function", {})
                                    if isinstance(func, dict):
                                        arguments = func.get("arguments")
                                        if arguments is None or arguments == "" or arguments == "null":
                                            func["arguments"] = "{}"
                    try:
                        return _original_parse_tools(message)
                    except Exception:
                        from langchain_core.agents import AgentFinish
                        return AgentFinish(
                            return_values={"output": "אירעה שגיאה בעיבוד הבקשה. אנא נסה לנסח מחדש את השאלה."},
                            log="Error: Tool call parsing failed"
                        )
                raise
        
        # Note: ToolCall is a TypedDict, not a class, so we can't patch __init__
        # Instead, we rely on fixing the args before they're used in the parser
        
        # Apply patches
        tools_module.parse_ai_message_to_tool_action = _safe_parse_ai_message_to_tool_action
        
        # Also patch openai_tools - it calls parse_ai_message_to_tool_action internally
        # We need to ensure it uses our patched version
        def _safe_parse_openai(message):
            """Wrapper for OpenAI tools parser that uses our patched function."""
            # This will call our patched _safe_parse_ai_message_to_tool_action
            return _original_parse_openai(message)
        
        openai_tools_module.parse_ai_message_to_openai_tool_action = _safe_parse_openai
        
        # CRITICAL: Also patch the import in openai_tools to use our patched version
        # openai_tools imports parse_ai_message_to_tool_action, so we need to update that reference
        if hasattr(openai_tools_module, 'parse_ai_message_to_tool_action'):
            # Update the imported reference
            openai_tools_module.parse_ai_message_to_tool_action = _safe_parse_ai_message_to_tool_action
        
        logger.info("Patched LangChain tool parser (tools + openai_tools)")
    except Exception as e:
        logger.error("Could not patch LangChain tool parser: %s", e, exc_info=True)

# Apply patch IMMEDIATELY - before any other LangChain code runs
_patch_langchain_tool_parser()


def _safe_int_env(var_name: str, default: int) -> int:
    """Return integer value from environment with safe fallback."""
    try:
        value = os.getenv(var_name)
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        logger.warning("Invalid integer for %s: %s. Using default %s.", var_name, value, default)
        return default


@lru_cache(maxsize=1)
def _get_tokenizer():
    """Lazily load and cache the tokenizer used for budgeting."""
    try:
        from tiktoken import get_encoding

        return get_encoding("cl100k_base")
    except ImportError as exc:
        logger.error("tiktoken is required for token budgeting but is not installed: %s", exc)
        raise


def enforce_token_budget(messages, max_tokens: int, reserve_for_output: int = 1024):
    """Ensure total tokens for messages stay within max_tokens - reserve."""

    if max_tokens <= 0:
        return messages

    tokenizer = _get_tokenizer()

    def count(msg):
        content = msg.get("content") or ""
        return len(tokenizer.encode(content))

    total = sum(count(m) for m in messages)
    target = max_tokens - max(reserve_for_output, 0)
    if total <= target:
        return messages

    trimmed = []
    running = 0
    for msg in reversed(messages):  # newest → oldest
        c = count(msg)
        if running + c <= target:
            trimmed.append(msg)
            running += c
        elif msg.get("role") != "system":
            trimmed.append({"role": "system", "content": "[history summarized due to budget]"})
            break
    trimmed.reverse()
    return trimmed


def _normalize_content(text: str) -> str:
    """Normalize whitespace in text for summaries."""
    if not text:
        return ""
    return " ".join(text.split())


def build_history_with_summary(
    history: List[Dict[str, str]],
    keep_last: int = 4,
    summary_max_chars: int = 600,
) -> List[Dict[str, str]]:
    """Return chat history keeping the latest turns and adding a summary for older ones."""

    if not history:
        return []

    keep_last = max(keep_last, 0)
    summary_max_chars = max(summary_max_chars, 120)

    sanitized = [
        {"role": msg.get("role", "user"), "content": msg.get("content", "")}
        for msg in history
        if isinstance(msg, dict)
    ]

    if len(sanitized) <= keep_last or keep_last == 0:
        return sanitized[-keep_last:] if keep_last else sanitized

    older_messages = sanitized[:-keep_last]
    recent_messages = sanitized[-keep_last:]

    summary_parts = []
    for msg in older_messages:
        role = (msg.get("role") or "user").upper()
        content = _normalize_content(msg.get("content") or "")
        if not content:
            continue
        summary_parts.append(f"{role}: {content}")

    if not summary_parts:
        return recent_messages

    summary_text = " | ".join(summary_parts)
    summary_text = summary_text[:summary_max_chars]

    summary_message = {
        "role": "system",
        "content": f"[תקציר שיחה]: {summary_text}",
    }

    return [summary_message, *recent_messages]


def compress_tool_output(text: str, max_chars: int = 1200) -> str:
    """Compress verbose tool output while preserving the most useful parts."""

    if text is None:
        return ""

    text = str(text)
    if len(text) <= max_chars:
        return text

    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact

    head = compact[:800]
    tail = compact[-300:]
    trimmed_chars = max(len(compact) - (len(head) + len(tail)), 0)
    return f"{head}\n...[trimmed {trimmed_chars} chars]...\n{tail}"


class ToolCallTracker(BaseCallbackHandler):
    """Callback handler to track tool calls during agent execution."""
    
    def __init__(self):
        self.tool_calls = []
        self.current_tool_call = None
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """Called when a tool starts running."""
        tool_name = serialized.get("name", "unknown_tool")
        logger.info("🔧 Tool started: %s with input: %s", tool_name, str(input_str)[:100])
        tool_hebrew = translate_tool_name(tool_name)
        self.current_tool_call = {
            "tool": tool_name,
            "tool_hebrew": tool_hebrew,
            "input": input_str,
            "status": "running",
            "output": None
        }
        self.tool_calls.append(self.current_tool_call)
    
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a tool finishes running."""
        if self.current_tool_call:
            tool_name = self.current_tool_call["tool"]
            self.current_tool_call["status"] = "completed"
            self.current_tool_call["output"] = compress_tool_output(output)
            logger.info("✅ Tool completed: %s", tool_name)
            self.current_tool_call = None
    
    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when a tool encounters an error."""
        if self.current_tool_call:
            self.current_tool_call["status"] = "error"
            self.current_tool_call["output"] = f"Error: {str(error)}"
            self.current_tool_call = None
    
    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """Get all tracked tool calls."""
        return self.tool_calls.copy()


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming LLM responses and tracking tool calls."""
    
    def __init__(self):
        self.tool_calls = []
        self.current_tool_call = None
        self.chunk_queue = asyncio.Queue(maxsize=1000)  # Increased queue size
        self.complete_response = ""
        self._finished = False
    
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Called when a new token is generated."""
        self.complete_response += token
        logger.debug("Received LLM token: %s (total length: %d)", token[:50], len(self.complete_response))
        # Put token in queue for async consumption
        try:
            self.chunk_queue.put_nowait({"type": "chunk", "content": token})
        except asyncio.QueueFull:
            logger.warning("Chunk queue full, skipping token")
            pass  # Queue is full, skip this chunk
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """Called when a tool starts running."""
        tool_name = serialized.get("name", "unknown_tool")
        logger.info("🔧 Tool started (streaming): %s with input: %s", tool_name, str(input_str)[:100])
        tool_hebrew = translate_tool_name(tool_name)
        self.current_tool_call = {
            "tool": tool_name,
            "tool_hebrew": tool_hebrew,
            "input": input_str,
            "status": "running",
            "output": None
        }
        self.tool_calls.append(self.current_tool_call)
        # Emit tool call start event - handle queue full gracefully
        try:
            self.chunk_queue.put_nowait({
                "type": "tool_call_start",
                "tool": tool_name,
                "tool_hebrew": tool_hebrew,
                "input": str(input_str)[:100] if input_str else ""
            })
        except asyncio.QueueFull:
            # If queue is full, try to make space by removing old chunks
            try:
                # Remove one old chunk to make space
                self.chunk_queue.get_nowait()
                self.chunk_queue.put_nowait({
                    "type": "tool_call_start",
                    "tool": tool_name,
                    "input": str(input_str)[:100] if input_str else ""
                })
            except Exception:
                pass  # If still can't add, skip this event
    
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a tool finishes running."""
        if self.current_tool_call:
            tool_name = self.current_tool_call["tool"]
            tool_hebrew = translate_tool_name(tool_name)
            self.current_tool_call["status"] = "completed"
            compressed_output = compress_tool_output(output)
            self.current_tool_call["output"] = compressed_output
            logger.info("✅ Tool completed (streaming): %s", tool_name)
            self.current_tool_call = None
            try:
                self.chunk_queue.put_nowait({
                    "type": "tool_call_end",
                    "tool": tool_name,
                    "tool_hebrew": tool_hebrew,
                    "output": compressed_output
                })
            except asyncio.QueueFull:
                # Try to make space
                try:
                    self.chunk_queue.get_nowait()
                    self.chunk_queue.put_nowait({
                        "type": "tool_call_end",
                        "tool": tool_name,
                        "tool_hebrew": tool_hebrew,
                        "output": compressed_output
                    })
                except:
                    pass
    
    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when a tool encounters an error."""
        if self.current_tool_call:
            self.current_tool_call["status"] = "error"
            self.current_tool_call["output"] = f"Error: {str(error)}"
            tool_name = self.current_tool_call["tool"]
            tool_hebrew = translate_tool_name(tool_name)
            self.current_tool_call = None
            try:
                self.chunk_queue.put_nowait({
                    "type": "tool_call_error",
                    "tool": tool_name,
                    "tool_hebrew": tool_hebrew,
                    "error": str(error)
                })
            except asyncio.QueueFull:
                pass
    
    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """Get all tracked tool calls."""
        return self.tool_calls.copy()
    
    def get_complete_response(self) -> str:
        """Get complete response."""
        return self.complete_response
    
    def mark_finished(self):
        """Mark streaming as finished."""
        self._finished = True
        try:
            self.chunk_queue.put_nowait({"type": "finished"})
        except asyncio.QueueFull:
            pass
    
    async def get_next_event(self, timeout: float = 0.1):
        """Get next event from queue."""
        try:
            return await asyncio.wait_for(self.chunk_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None


def translate_tool_name(tool_name: str) -> str:
    """Translate tool name to Hebrew."""
    translations = {
        "list_assets_tool": "חיפוש נכסים",
        "get_asset_filters_tool": "קבלת אפשרויות סינון",
        "get_asset_tool": "קבלת פרטי נכס",
        "create_asset_tool": "יצירת נכס",
        "calculate_deal_expenses_tool": "חישוב הוצאות עסקה",
        "get_asset_data_tool": "קבלת תת-משאב נכס",
        "list_deals_tool": "רשימת עסקאות",
        "create_deal_tool": "יצירת עסקה",
        "get_offer_tool": "קבלת פרטי הצעה",
        "estimate_build_cost_tool": "הערכת עלות בנייה",
        "get_cost_options_tool": "קבלת אפשרויות עלות",
        "analyze_mortgage_tool": "ניתוח משכנתא",
        "list_contacts_tool": "רשימת אנשי קשר",
        "create_contact_tool": "יצירת איש קשר",
        "list_leads_tool": "רשימת לידים",
        "create_lead_tool": "יצירת ליד",
        "list_tasks_tool": "רשימת משימות",
        "fetch_web_page_tool": "שליפת דף אינטרנט",
    }
    return translations.get(tool_name, tool_name.replace("_tool", "").replace("_", " "))


class RealEstateAgent:
    """Real Estate Agent powered by LangChain."""
    
    # Class-level cache for available cities (shared across all instances)
    # This is more efficient since agents are created per HTTP request
    _available_cities_cache: Optional[List[str]] = None
    
    def __init__(
        self,
        llm_provider: str = "openai",
        api_token: Optional[str] = None,
        api_url: Optional[str] = None,
        temperature: float = 0.3,
        user_api_key: Optional[str] = None,
        internet_enabled: bool = False,
        enable_memory: bool = True,
        memory_max_messages: int = 50,
        memory: Optional[ConversationMemory] = None,
    ):
        """Initialize the Real Estate Agent.

        Args:
            llm_provider: LLM provider to use ("openai", "gemini", or "groq")
            api_token: Optional API token for authenticated requests
            api_url: Optional API base URL (defaults to env var or localhost)
            temperature: LLM temperature setting
            user_api_key: Optional user's API key for LLM (overrides environment variables)
            internet_enabled: Enable Internet access (default: False). When enabled, allows
                             fetching web pages from whitelisted domains only.
            enable_memory: Enable storing chat history in memory.
            memory_max_messages: Maximum number of messages to keep in memory.
            memory: Optional pre-configured memory object (overrides other memory settings).
        """
        self.api_token = api_token or os.getenv("REALESTATE_API_TOKEN")  # Use provided token or fallback to env var
        self.api_url = api_url or os.getenv("REALESTATE_API_URL", "http://127.0.0.1:8000/api")
        self.user_api_key = user_api_key  # Store user's API key
        self.internet_enabled = internet_enabled

        self.max_input_tokens = _safe_int_env("AGENT_MAX_INPUT_TOKENS", 120_000)
        self.output_token_reserve = _safe_int_env("AGENT_OUTPUT_TOKEN_RESERVE", 1024)
        self.history_keep_last = _safe_int_env("AGENT_HISTORY_KEEP_LAST", 4)
        self.history_summary_max_chars = _safe_int_env("AGENT_HISTORY_SUMMARY_MAX_CHARS", 600)
        self._tool_budget_message_cache: Optional[Dict[str, str]] = None

        if self.api_token:
            os.environ["REALESTATE_API_TOKEN"] = self.api_token
        else:
            logger.warning("No API token provided to agent - MCP tools may not work properly")
        os.environ["REALESTATE_API_URL"] = self.api_url
        
        # Initialize LLM
        self.llm = self._create_llm(llm_provider, temperature, user_api_key)
        
        # Create tools
        self.tools = self._create_tools()
        logger.info("Created %d tools for agent", len(self.tools))

        # Configure memory
        self.memory = None
        if memory is not None:
            self.memory = memory
        elif enable_memory:
            try:
                self.memory = ConversationMemory(max_messages=memory_max_messages)
            except Exception as exc:
                logger.error("Failed to initialise conversation memory: %s", exc)
                self.memory = None

        # Create agent
        self.agent_executor = self._create_agent_executor()

    def clear_memory(self) -> None:
        """Clear stored conversation history."""
        if self.memory is not None:
            self.memory.clear()

    def _sanitize_chat_history(self, chat_history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
        """Return a sanitized copy of provided chat history."""
        sanitized: List[Dict[str, str]] = []
        if not chat_history:
            return sanitized
        for message in chat_history:
            if not isinstance(message, dict):
                continue
            role = str(message.get("role", "user")).strip() or "user"
            content = str(message.get("content", "")).strip()
            sanitized.append({"role": role, "content": content})
        return sanitized

    def _build_chat_history(self, chat_history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
        """Combine external chat history with internal memory if enabled."""
        if self.memory is not None:
            return self.memory.build_history(chat_history)
        return self._sanitize_chat_history(chat_history)

    def _record_interaction(self, user_message: str, agent_response: str) -> None:
        """Persist the latest interaction to memory if available."""
        if self.memory is None:
            return
        self.memory.append_interaction(user_message, agent_response)

    def _create_llm(self, provider: str, temperature: float, user_api_key: Optional[str] = None):
        """Create LLM instance based on provider."""
        # Helper to get API key from user key first, then env or Django settings
        def get_api_key(env_var_name: str, settings_attr: str = None, expected_provider: str = None) -> tuple[Optional[str], str]:
            """Return (key, source) tuple where source indicates where key came from."""
            # Use user's API key ONLY if it matches the expected provider
            # This prevents using a Groq key for OpenAI, etc.
            if user_api_key and expected_provider:
                # Check if user_api_key is for the expected provider by checking env vars
                # If we're looking for GROQ_API_KEY and user_api_key was passed, assume it's for the current provider
                # The views.py code ensures the correct key is passed for the selected provider
                provider_key_map = {
                    "groq": "GROQ_API_KEY",
                    "openai": "OPENAI_API_KEY",
                    "gemini": "GEMINI_API_KEY"
                }
                if expected_provider in provider_key_map and env_var_name == provider_key_map[expected_provider]:
                    return user_api_key.strip(), "user"
            
            # Fall back to environment variable
            key = os.getenv(env_var_name)
            if key:
                return key.strip(), "environment"
            # Try Django settings if available
            try:
                from django.conf import settings
                from django.core.exceptions import ImproperlyConfigured
                if settings_attr:
                    # Accessing settings attributes may trigger ImproperlyConfigured if Django isn't configured
                    try:
                        key = getattr(settings, settings_attr, None)
                        if key:
                            return key.strip(), "django_settings"
                    except ImproperlyConfigured:
                        # Django not configured, skip Django settings
                        pass
            except ImportError:
                # Django not installed, skip Django settings
                pass
            return None, "none"
        
        if provider == "openai":
            api_key, key_source = get_api_key("OPENAI_API_KEY", "OPENAI_API_KEY", expected_provider=provider)
            if not api_key or not api_key.strip():
                logger.error("OPENAI_API_KEY is missing or empty (source: %s)", key_source)
                raise ValueError("OPENAI_API_KEY is required and must not be empty")
            if len(api_key.strip()) < 10:
                logger.warning("OPENAI_API_KEY appears to be too short (likely invalid) - length: %d, source: %s", 
                             len(api_key.strip()), key_source)
            # Log key info (first 10 chars + last 4 chars for debugging, but not full key)
            key_preview = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else api_key[:10] + "..."
            logger.info("Using OpenAI LLM - Model: %s, Key source: %s, Key preview: %s", 
                       os.getenv("OPENAI_MODEL", "gpt-4o-mini"), key_source, key_preview)
            return ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=temperature,
                api_key=api_key.strip(),  # Ensure no leading/trailing whitespace
                streaming=True,  # Enable streaming for callbacks
            )
        elif provider == "gemini":
            api_key1, source1 = get_api_key("GEMINI_API_KEY", "GEMINI_API_KEY", expected_provider=provider)
            api_key2, source2 = get_api_key("GOOGLE_API_KEY", "GOOGLE_API_KEY", expected_provider=provider)
            api_key = api_key1 or api_key2
            key_source = source1 if api_key1 else source2
            if not api_key or not api_key.strip():
                logger.error("GEMINI_API_KEY/GOOGLE_API_KEY is missing or empty (checked: GEMINI=%s, GOOGLE=%s)", 
                           source1, source2)
                raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is required and must not be empty")
            key_preview = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else api_key[:10] + "..."
            logger.info("Using Gemini LLM - Model: %s, Key source: %s, Key preview: %s", 
                       os.getenv("GEMINI_MODEL", "gemini-2.0-flash"), key_source, key_preview)
            return ChatGoogleGenerativeAI(
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                temperature=temperature,
                google_api_key=api_key.strip(),  # Ensure no leading/trailing whitespace
                streaming=True,  # Enable streaming for callbacks
            )
        elif provider == "groq":
            api_key, key_source = get_api_key("GROQ_API_KEY", "GROQ_API_KEY", expected_provider=provider)
            if not api_key or not api_key.strip():
                logger.error("GROQ_API_KEY is missing or empty (source: %s)", key_source)
                raise ValueError("GROQ_API_KEY is required and must not be empty")
            key_preview = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else api_key[:10] + "..."
            groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            logger.info("Using Groq LLM - Model: %s, Key source: %s, Key preview: %s", 
                       groq_model, key_source, key_preview)
            # Groq uses OpenAI-compatible API
            return ChatOpenAI(
                model=groq_model,
                temperature=temperature,
                api_key=api_key.strip(),  # Ensure no leading/trailing whitespace
                base_url="https://api.groq.com/openai/v1",
                streaming=True,  # Enable streaming for callbacks
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def _create_tools(self) -> List[BaseTool]:
        """Create LangChain tools from MCP server functions.
        
        MockContext: A dummy context object passed to MCP functions.
        Some MCP functions expect a context parameter for logging/info.
        This is just a placeholder - it doesn't affect functionality.
        """
        # Create a context object for MCP tools
        # This is just a dummy object - MCP functions might expect a context parameter
        class MockContext:
            def info(self, msg: str):
                pass  # No-op - just satisfies the interface
        
        ctx = MockContext()
        logger.debug("Creating tools with MockContext (dummy context object)")
        
        # Helper functions for projection-first list handling
        def _safe_limit(n: Optional[int], default: int = 5, hard_max: int = 50) -> int:
            """Safely convert limit parameter to int with bounds."""
            try:
                if n is None:
                    return default
                return max(1, min(int(n), hard_max))
            except Exception:
                return default
        
        def _fmt_list(items: list, key_fields: list[str], max_items: int) -> str:
            """Format list items with field projection."""
            if not isinstance(items, list):
                return str(items)
            out = []
            for x in items[:max_items]:
                line = " | ".join(f"{k}: {x.get(k)}" for k in key_fields if k in x)
                out.append(f"- {line or str(x)[:200]}")
            more = "" if len(items) <= max_items else f"\n…(+{len(items)-max_items} נוספים)"
            return "\n".join(out) + more
        
        def _normalize_city_name(city: str) -> str:
            """Normalize city name for comparison (remove spaces, dashes, etc.)."""
            if not city:
                return ""
            # Remove common separators and normalize whitespace
            normalized = city.replace("-", " ").replace("–", " ").replace("—", " ")
            normalized = " ".join(normalized.split())  # Normalize whitespace
            return normalized.strip()
        
        def _find_best_city_match(city: str, available_cities: List[str]) -> Optional[str]:
            """Find the best matching city name from available cities.
            
            Returns the exact match if found, otherwise tries fuzzy matching.
            """
            if not city or not available_cities:
                return None
            
            city_normalized = _normalize_city_name(city)
            
            # First, try exact match (case-insensitive)
            for available_city in available_cities:
                if city_normalized == _normalize_city_name(available_city):
                    return available_city
            
            # Try substring match (city name contains the search term or vice versa)
            for available_city in available_cities:
                available_normalized = _normalize_city_name(available_city)
                if city_normalized in available_normalized or available_normalized in city_normalized:
                    return available_city
            
            # Try matching after removing common suffixes/prefixes
            # For example, "תל אביב" should match "תל אביב יפו" or "תל אביב-יפו"
            city_words = set(city_normalized.split())
            for available_city in available_cities:
                available_normalized = _normalize_city_name(available_city)
                available_words = set(available_normalized.split())
                # If all words from the search city are in the available city, it's a match
                if city_words and city_words.issubset(available_words):
                    return available_city
            
            return None
        
        async def _get_available_cities() -> List[str]:
            """Get available cities from cache or API."""
            if RealEstateAgent._available_cities_cache is None:
                try:
                    result = await get_asset_filters(ctx)
                    if isinstance(result, dict) and result.get("success"):
                        filters = result.get("filters", {})
                        RealEstateAgent._available_cities_cache = filters.get("cities", [])
                    else:
                        RealEstateAgent._available_cities_cache = []
                except Exception:
                    RealEstateAgent._available_cities_cache = []
            return RealEstateAgent._available_cities_cache or []
        
        # Generic tool enrichment system
        async def _enrich_asset_list_item(asset: Dict[str, Any]) -> Dict[str, Any]:
            """Enrich a single asset item with listings data."""
            asset_id = asset.get("id")
            if not asset_id:
                return asset
            
            # Build address string from available fields
            # Try multiple ways to get address info
            asset_city = asset.get("city") or asset.get("city_name") or ""
            asset_street = asset.get("street") or asset.get("street_name") or ""
            asset_number = asset.get("number") or asset.get("house_number")
            asset_neighborhood = asset.get("neighborhood") or asset.get("neighborhood_name") or ""
            
            # If we don't have address components, try to get full asset data
            if not asset_city and not asset_street:
                try:
                    full_asset_result = await get_asset(ctx, asset_id, include_documents=False)
                    if isinstance(full_asset_result, dict) and full_asset_result.get("success"):
                        full_asset = full_asset_result.get("data", {})
                        asset_city = full_asset.get("city") or asset_city
                        asset_street = full_asset.get("street") or asset_street
                        asset_number = full_asset.get("number") or asset_number
                        asset_neighborhood = full_asset.get("neighborhood") or asset_neighborhood
                except Exception as e:
                    logger.debug(f"Could not fetch full asset {asset_id} for address: {e}", exc_info=True)
            
            address_parts = []
            if asset_street:
                address_parts.append(asset_street)
                if asset_number:
                    address_parts.append(str(asset_number))
            if asset_neighborhood:
                address_parts.append(f"({asset_neighborhood})")
            if asset_city:
                address_parts.append(asset_city)
            address = ", ".join(address_parts) if address_parts else f"נכס #{asset_id}"
            
            # Fetch listings to get price information
            try:
                listings_result = await get_asset_data(ctx, asset_id=asset_id, kind="listings", limit=1, compact=False)
                enriched_data = {
                    "address": address,
                    "id": asset_id,
                }
                
                if isinstance(listings_result, dict) and listings_result.get("success"):
                    listings_data = listings_result.get("data", [])
                    if listings_data:
                        listing = listings_data[0]
                        price = listing.get("price")
                        if price:
                            if price < 100000:
                                enriched_data["price"] = f"₪{price:,}/חודש (השכרה)"
                            else:
                                enriched_data["price"] = f"₪{price:,}"
                        
                        rooms = listing.get("rooms") or listing.get("rooms_display")
                        if rooms:
                            enriched_data["rooms"] = f"{rooms} חדרים"
                        
                        size = listing.get("size")
                        if size:
                            enriched_data["size"] = f"{size} מ\"ר"
                        
                        prop_type = listing.get("property_type")
                        if prop_type:
                            enriched_data["property_type"] = prop_type
                
                return enriched_data
            except Exception as e:
                logger.debug(f"Could not enrich asset {asset_id}: {e}", exc_info=True)
                return {"address": address, "id": asset_id}
        
        def _format_enriched_item(item: Dict[str, Any], formatter: Optional[Callable[[Dict[str, Any]], str]] = None) -> str:
            """Format an enriched item using a custom formatter or default format."""
            if formatter:
                return formatter(item)
            
            # Default formatting: try to build a nice string
            parts = []
            
            # Address or name first
            if "address" in item:
                parts.append(f"**{item['address']}**")
            elif "name" in item:
                parts.append(f"**{item['name']}**")
            
            # Price if available
            if "price" in item:
                parts.append(f"מחיר: {item['price']}")
            
            # Property type or other type field
            if "property_type" in item:
                parts.append(f"סוג: {item['property_type']}")
            
            # Rooms
            if "rooms" in item:
                parts.append(item['rooms'])
            
            # Size
            if "size" in item:
                parts.append(item['size'])
            
            # Email/Phone for contacts
            if "email" in item and item.get("email"):
                parts.append(f"אימייל: {item['email']}")
            if "phone" in item and item.get("phone"):
                parts.append(f"טלפון: {item['phone']}")
            
            return " • ".join(parts) if parts else str(item)
        
        async def _enrich_list_output(
            tool_name: str,
            data: List[Dict[str, Any]],
            limit: int,
            enrichment_func: Optional[Callable[[Dict[str, Any]], Any]] = None,
            formatter: Optional[Callable[[Dict[str, Any]], str]] = None,
        ) -> str:
            """Generic function to enrich list tool outputs.
            
            Args:
                tool_name: Name of the tool (for logging)
                data: List of items to enrich
                limit: Maximum number of items to process
                enrichment_func: Async function(item) -> enriched_item_dict
                formatter: Function(enriched_item) -> formatted_string
            """
            if not data:
                return "לא נמצאו תוצאות."
            
            if not enrichment_func:
                # No enrichment needed, use default formatting
                formatted_items = []
                for item in data[:limit]:
                    formatted_items.append(_format_enriched_item(item, formatter))
                result_text = "\n".join(f"{i+1}. {item}" for i, item in enumerate(formatted_items))
                if len(data) > limit:
                    result_text += f"\n\n…(+{len(data) - limit} נוספים)"
                return result_text
            
            # Enrich items
            enriched_items = []
            for item in data[:limit]:
                try:
                    enriched = await enrichment_func(item)
                    enriched_items.append(enriched)
                except Exception as e:
                    logger.debug(f"Error enriching item in {tool_name}: {e}", exc_info=True)
                    enriched_items.append(item)
            
            # Format enriched items
            formatted_items = []
            for item in enriched_items:
                formatted_items.append(_format_enriched_item(item, formatter))
            
            result_text = "\n".join(f"{i+1}. {item}" for i, item in enumerate(formatted_items))
            if len(data) > limit:
                result_text += f"\n\n…(+{len(data) - limit} נוספים)"
            
            return result_text
        
        # Wrap MCP functions as LangChain tools
        # Assets tools
        async def list_assets_tool_func(
            city: Optional[str] = None,
            neighborhood: Optional[str] = None,
            max_price: Optional[int] = None,
            min_price: Optional[int] = None,
            rooms: Optional[int] = None,
            area_min: Optional[float] = None,
            area_max: Optional[float] = None,
            rent_price_min: Optional[int] = None,
            rent_price_max: Optional[int] = None,
            seller_type: Optional[str] = None,
            commercial: Optional[str] = None,
            type: Optional[str] = None,
            rental_sale: Optional[str] = None,
            status: Optional[str] = None,
            zoning: Optional[str] = None,
            user_assets: Optional[str] = None,
            page: Optional[int] = None,
            fields: Optional[Any] = None,
            limit: Optional[int] = 5,
        ) -> str:
            """List all assets with optional filtering. Returns formatted results with addresses, prices, and property details.
            
            IMPORTANT: When user asks for "rental properties" or "properties for rent" (נכסים להשכרה), 
            use rental_sale="rent". When user asks for "properties for sale" (נכסים למכירה), use rental_sale="sale".
            The user_assets parameter is ONLY for filtering by ownership/watchlist, NOT for rent vs sale filtering.
            
            Parameters:
            - city: City name (use get_asset_filters_tool() to see available formats)
            - neighborhood: Neighborhood name
            - max_price: Maximum price in shekels (for sale properties)
            - min_price: Minimum price in shekels (for sale properties)
            - rooms: Number of rooms
            - area_min: Minimum area in square meters
            - area_max: Maximum area in square meters
            - rent_price_min: Minimum rent price in shekels per month (use with rental_sale="rent")
            - rent_price_max: Maximum rent price in shekels per month (use with rental_sale="rent")
            - seller_type: Filter by seller type - "broker", "private", or "all" (default: "all")
            - commercial: Filter by property type - "commercial", "residential", or "all" (default: "all")
            - type: Property type filter
            - rental_sale: CRITICAL - Filter by rental/sale type. Use "rent" for rental properties (נכסים להשכרה), 
              "sale" for properties for sale (נכסים למכירה), "all" for both (default: "all").
              When user mentions "rentals", "for rent", "השכרה" - ALWAYS use rental_sale="rent".
            - status: Filter by asset status - "done", "enriching", "failed", "pending", or "all" (default: "all")
            - zoning: Zoning filter
            - user_assets: Filter by ownership/watchlist ONLY - "watchlist" for assets in user's watchlist, 
              "mine" for user's own assets, "others" for others' assets, or "all" (default: "all").
              DO NOT use this for filtering rent vs sale - use rental_sale instead.
            - page: Page number for pagination
            - fields: Optional list of field names to return (can be a list or comma-separated string)
            - limit: Maximum number of items to return (default: 5, max: 50)
            
            Examples:
            - User asks "rental properties in Tel Aviv" -> use rental_sale="rent", city="תל אביב"
            - User asks "properties for sale under 2M" -> use rental_sale="sale", max_price=2000000
            - User asks "my watchlist" -> use user_assets="watchlist"
            
            Returns formatted list ready to present to user.
            """
            try:
                limit = _safe_limit(limit, default=5, hard_max=50)
                corrected_city = city
                
                # If city is provided, try to correct it automatically
                if city:
                    available_cities = await _get_available_cities()
                    if available_cities:
                        matched_city = _find_best_city_match(city, available_cities)
                        if matched_city and matched_city != city:
                            # Found a better match, use it automatically
                            corrected_city = matched_city
                            logger.info(f"Auto-corrected city name: '{city}' -> '{corrected_city}'")
                
                # Normalize fields parameter: handle both string and list inputs
                # This handles cases where the LLM passes fields as a string instead of an array
                fields_list = None
                if fields is not None:
                    if isinstance(fields, str):
                        # Convert comma-separated string to list
                        fields_list = [f.strip() for f in fields.split(",") if f.strip()]
                    elif isinstance(fields, list):
                        fields_list = fields
                    else:
                        # Fallback: try to convert to list
                        try:
                            fields_list = list(fields) if fields else None
                        except (TypeError, ValueError):
                            fields_list = None
                
                # Ensure essential fields are always included for address building
                # We need street, number, city, neighborhood to build addresses
                essential_fields = ["id", "street", "number", "city", "neighborhood"]
                if fields_list:
                    # Merge user's fields with essential fields, preserving order
                    api_fields = list(dict.fromkeys(essential_fields + fields_list))  
                else:
                    api_fields = essential_fields
                
                result = await list_assets(
                    ctx,
                    city=corrected_city,
                    neighborhood=neighborhood,
                    max_price=max_price,
                    min_price=min_price,
                    rooms=rooms,
                    area_min=area_min,
                    area_max=area_max,
                    rent_price_min=rent_price_min,
                    rent_price_max=rent_price_max,
                    seller_type=seller_type,
                    commercial=commercial,
                    type=type,
                    rental_sale=rental_sale,
                    status=status,
                    zoning=zoning,
                    user_assets=user_assets,
                    page=page,
                    fields=api_fields,
                    limit=limit,
                    compact=True
                )
                
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", [])
                    
                    # If we got empty results and city was corrected, inform the user
                    if not data and city and corrected_city != city:
                        return f"תוקן שם העיר מ-'{city}' ל-'{corrected_city}'. לא נמצאו נכסים התואמים את הקריטריונים."
                    
                    # If we got empty results and city wasn't corrected (no match found), suggest checking filters
                    if not data and city and corrected_city == city:
                        available_cities = await _get_available_cities()
                        if available_cities:
                            # Double-check if there's a match we might have missed
                            matched_city = _find_best_city_match(city, available_cities)
                            if not matched_city:
                                # No match found, suggest checking filters
                                return f"לא נמצאו נכסים בעיר '{city}'. אנא השתמש ב-get_asset_filters_tool() כדי לראות את שמות הערים הזמינים."
                    
                    enriched_result = await _enrich_list_output(
                        tool_name="list_assets_tool",
                        data=data,
                        limit=limit,
                        enrichment_func=_enrich_asset_list_item,
                    )
                    
                    # Ensure we return a clear, complete response
                    final_result = enriched_result
                    if not final_result.strip():
                        return "לא נמצאו נכסים התואמים את הקריטריונים."
                    
                    # Add a clear completion marker to help the LLM recognize this as final
                    # The formatted results are complete - no need to call the tool again
                    return final_result
                
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        list_assets_tool = StructuredTool.from_function(
            func=wrap_async_tool(list_assets_tool_func),
            name="list_assets_tool",
            description="חיפוש נכסים עם מסננים. חשוב: כאשר המשתמש מבקש נכסים להשכרה (rentals) - השתמש ב-rental_sale='rent'. כאשר המשתמש מבקש נכסים למכירה - השתמש ב-rental_sale='sale'. הפרמטר user_assets מיועד רק לסינון לפי בעלות/רשימת מעקב, לא לסינון השכרה מול מכירה. לבדיקת מסננים זמינים get_asset_filters_tool."
        )
        
        async def get_asset_filters_tool_func() -> str:
            """Get available filter options including cities, property types, neighborhoods, etc.
            
            This is essential before searching for properties to ensure you use the correct city name format.
            Returns a dictionary with available filter values including:
            - cities: List of available city names (use exact name from this list)
            - types: List of property types
            - neighborhoods: List of neighborhoods
            - And more...
            """
            try:
                result = await get_asset_filters(ctx)
                if isinstance(result, dict) and result.get("success"):
                    filters = result.get("filters", {})
                    cities = filters.get("cities", [])
                    # Update the cache with fresh data
                    RealEstateAgent._available_cities_cache = cities
                    cities_str = ', '.join(cities[:20]) + ('...' if len(cities) > 20 else '')
                    types_str = ', '.join(filters.get('types', [])[:10]) + ('...' if len(filters.get('types', [])) > 10 else '')
                    neighborhoods_str = ', '.join(filters.get('neighborhoods', [])[:10]) + ('...' if len(filters.get('neighborhoods', [])) > 10 else '')
                    return f"מסננים זמינים:\n" + \
                           f"ערים: {cities_str}\n" + \
                           f"סוגי נכסים: {types_str}\n" + \
                           f"שכונות: {neighborhoods_str}\n" + \
                           "\nהשתמש בשם העיר המדויק מרשימת הערים לחיפוש."
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        get_asset_filters_tool = StructuredTool.from_function(
            func=wrap_async_tool(get_asset_filters_tool_func),
            name="get_asset_filters_tool",
            description="קבלת מסננים זמינים לנכסים."
        )
        
        async def get_asset_tool_func(
            asset_id: int,
            include_documents: bool = False,
            fields: Optional[List[str]] = None,
        ) -> str:
            """Get detailed information for a specific asset by ID."""
            try:
                result = await get_asset(ctx, asset_id, include_documents)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    if fields:
                        data = {k: data.get(k) for k in fields if k in data}
                    # Keep this single-object formatting compact
                    return "\n".join(f"{k}: {v}" for k, v in data.items())
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        get_asset_tool = StructuredTool.from_function(
            func=wrap_async_tool(get_asset_tool_func),
            name="get_asset_tool",
            description="קבלת פרטי נכס לפי מזהה."
        )
        
        async def create_asset_tool_func(
            address: Optional[str] = None,
            city: Optional[str] = None,
            street: Optional[str] = None,
            number: Optional[int] = None,
        ) -> str:
            """Create a new asset/property. Provide address information."""
            try:
                result = await create_asset(ctx, None, address, city, street, number)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    return f"נכס נוצר בהצלחה: {data}"
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        create_asset_tool = StructuredTool.from_function(
            func=wrap_async_tool(create_asset_tool_func),
            name="create_asset_tool",
            description="יצירת נכס חדש עם כתובת."
        )
        
        class GetAssetDataInput(BaseModel):
            """Input schema for get_asset_data_tool."""
            asset_id: int = Field(description="The ID of the asset")
            kind: str = Field(description="Type of data to retrieve - one of: transactions, permits, plans, appraisal, listings, documents")
            fields: Optional[List[str]] = Field(default=None, description="Optional list of field names to return")
            limit: Optional[int] = Field(default=5, description="Maximum number of items to return (default: 5)")
        
        async def get_asset_data_tool_func(
            asset_id: int,
            kind: str,  # "transactions" | "permits" | "plans" | "appraisal" | "listings" | "documents"
            fields: Optional[List[str]] = None,
            limit: Optional[int] = 5,
        ) -> str:
            """Get asset subresource data with field projection and limiting.
            
            Parameters:
            - asset_id: The ID of the asset
            - kind: Type of data to retrieve - one of: transactions, permits, plans, appraisal, listings, documents
            - fields: Optional list of field names to return
            - limit: Maximum number of items to return (default: 5)
            """
            try:
                limit = _safe_limit(limit, default=5)
                result = await get_asset_data(ctx, asset_id=asset_id, kind=kind, fields=fields, limit=limit, compact=True)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", [])
                    # Choose minimal sensible defaults per kind
                    defaults = {
                        "transactions": ["dealDate", "dealAmount", "assetArea", "floorNo"],
                        "permits": ["permit_id", "status", "issued_at", "title"],
                        "plans": ["plan_number", "name", "status"],
                        "appraisal": ["estPrice", "method", "updatedAt"],
                        "listings": ["source", "price", "rooms", "area", "url"],
                        "documents": ["id", "title", "type", "created_at", "size"],
                    }
                    key_fields = fields or defaults.get(kind, ["id"])
                    return _fmt_list(data, key_fields, limit)
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        get_asset_data_tool = StructuredTool.from_function(
            func=wrap_async_tool(get_asset_data_tool_func),
            name="get_asset_data_tool",
            description="קבלת תת-משאב של נכס עם שדות ומגבלה (transactions/permits/plans/appraisal/listings/documents).",
            args_schema=GetAssetDataInput
        )
        
        # Deal tools
        async def list_deals_tool_func(
            stage: Optional[str] = None,
            asset_id: Optional[int] = None,
            fields: Optional[List[str]] = None,
            limit: Optional[int] = 5,
        ) -> str:
            """List all deals, optionally filtered by stage or asset."""
            try:
                limit = _safe_limit(limit)
                result = await list_deals(ctx, stage=stage, asset_id=asset_id, fields=fields, limit=limit, compact=True)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", [])
                    # Custom formatter for deals
                    def format_deal(deal: Dict[str, Any]) -> str:
                        parts = []
                        if "id" in deal:
                            parts.append(f"**עסקה #{deal['id']}**")
                        if "stage" in deal:
                            parts.append(f"שלב: {deal['stage']}")
                        if "asset_id" in deal:
                            parts.append(f"נכס #{deal['asset_id']}")
                        if "updated_at" in deal and deal.get("updated_at"):
                            parts.append(f"עודכן: {deal['updated_at']}")
                        return " • ".join(parts) if parts else str(deal)
                    
                    return await _enrich_list_output(
                        tool_name="list_deals_tool",
                        data=data,
                        limit=limit,
                        enrichment_func=None,
                        formatter=format_deal,
                    )
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        list_deals_tool = StructuredTool.from_function(
            func=wrap_async_tool(list_deals_tool_func),
            name="list_deals_tool",
            description="רשימת עסקאות עם סינון אופציונלי."
        )
        
        async def create_deal_tool_func(
            asset_id: int,
            stage: Optional[str] = "discovery",
        ) -> str:
            """Create a new deal for an asset."""
            try:
                result = await create_deal(ctx, asset_id, stage)
                if isinstance(result, dict) and result.get("success"):
                    return f"עסקה נוצרה: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        create_deal_tool = StructuredTool.from_function(
            func=wrap_async_tool(create_deal_tool_func),
            name="create_deal_tool",
            description="יצירת עסקה חדשה לנכס."
        )
        
        async def get_offer_tool_func(offer_id: int) -> str:
            """Get offer details including financial information."""
            try:
                result = await get_offer(ctx, offer_id)
                if isinstance(result, dict) and result.get("success"):
                    return f"הצעה {offer_id}: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        get_offer_tool = StructuredTool.from_function(
            func=wrap_async_tool(get_offer_tool_func),
            name="get_offer_tool",
            description="קבלת פרטי הצעה."
        )
        
        # Expense calculation tools
        async def estimate_build_cost_tool_func(
            area_m2: float,
            scope: Optional[List[str]] = None,
            region: Optional[str] = None,
            quality: Optional[str] = None,
        ) -> str:
            """Estimate building construction costs in square meters."""
            try:
                result = await estimate_build_cost(ctx, area_m2, scope, region, quality)
                if isinstance(result, dict) and result.get("success"):
                    return f"הערכת עלות: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        estimate_build_cost_tool = StructuredTool.from_function(
            func=wrap_async_tool(estimate_build_cost_tool_func),
            name="estimate_build_cost_tool",
            description="הערכת עלויות בנייה במ\"ר."
        )
        
        async def get_cost_options_tool_func() -> str:
            """Get available options for construction cost estimation only (regions, qualities, scopes).
            
            Only relevant for land properties (מגרשים) when estimating building costs.
            Not needed for regular deal expense calculations.
            """
            try:
                result = await get_cost_options(ctx)
                if isinstance(result, dict) and result.get("success"):
                    return f"אפשרויות עלות: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        get_cost_options_tool = StructuredTool.from_function(
            func=wrap_async_tool(get_cost_options_tool_func),
            name="get_cost_options_tool",
            description="קבלת אפשרויות עלות להערכת עלויות בנייה בלבד עבור מגרשים."
        )
        
        async def calculate_deal_expenses_tool_func(
            price: float,
            buyers: Optional[List[Dict[str, Any]]] = None,
            area: Optional[float] = None,
            property_type: Optional[str] = None,
            services: Optional[List[Dict[str, Any]]] = None,
            vat_rate: Optional[float] = None,
            construction_area: Optional[float] = None,
            construction_cost_per_sqm: Optional[float] = None,
            construction_includes_vat: Optional[bool] = None,
        ) -> str:
            """Calculate complete deal expenses including purchase tax, service costs, and construction costs.
            
            If buyers are not specified, uses the current logged-in user as the default buyer with 100% share.
            Building expenses are only calculated for land property type (מגרשים).
            """
            try:
                # The calculate_deal_expenses function in MCP server will handle default buyer logic
                # No need to set default here as it's handled upstream
                
                result = await calculate_deal_expenses(
                    ctx, price, buyers, area, property_type, services, 
                    vat_rate, construction_area, construction_cost_per_sqm, construction_includes_vat
                )
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    # Format the result nicely
                    total_tax = data.get("totalTax", 0)
                    service_total = data.get("serviceTotal", 0)
                    construction_cost = data.get("constructionCost", 0)
                    total = data.get("total", 0)
                    
                    breakdown = data.get("breakdown", [])
                    breakdown_text = "\n".join([
                        f"  - {b.get('buyer', {}).get('name', 'Buyer')}: {b.get('portionPrice', 0):,.0f}₪, מס: {b.get('tax', 0):,.0f}₪ ({b.get('track', 'regular')})"
                        for b in breakdown
                    ])
                    
                    return f"""חישוב הוצאות עסקה:
מחיר נכס: {price:,.0f}₪
מס רכישה: {total_tax:,.0f}₪
עלויות שירות: {service_total:,.0f}₪
עלויות בנייה: {construction_cost:,.0f}₪
סה"כ: {total:,.0f}₪

פירוט מס רכישה:
{breakdown_text}"""
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        calculate_deal_expenses_tool = StructuredTool.from_function(
            func=wrap_async_tool(calculate_deal_expenses_tool_func),
            name="calculate_deal_expenses_tool",
            description="חישוב הוצאות עסקה כולל מס רכישה, עלויות שירות ועלויות בנייה. אם לא צוינו קונים, משתמש במשתמש הנוכחי כקונה ברירת מחדל."
        )
        
        # Mortgage tools
        def _format_mortgage_analysis(data: Dict[str, Any]) -> str:
            """Format mortgage analysis results in a user-friendly Hebrew format."""
            if not isinstance(data, dict):
                return str(data)
            
            lines = []
            lines.append("📊 ניתוח משכנתא")
            lines.append("")
            
            # Metrics section
            metrics = data.get("metrics", {})
            if metrics:
                lines.append("📈 נתוני הכנסות והוצאות:")
                med_income = metrics.get("median_monthly_income", 0)
                med_expense = metrics.get("median_monthly_expense", 0)
                surplus = metrics.get("monthly_surplus_estimate", 0)
                
                if med_income > 0:
                    lines.append(f"  • הכנסה חודשית ממוצעת: ₪{med_income:,.0f}")
                if med_expense > 0:
                    lines.append(f"  • הוצאה חודשית ממוצעת: ₪{med_expense:,.0f}")
                if surplus > 0:
                    lines.append(f"  • עודף חודשי משוער: ₪{surplus:,.0f}")
                lines.append("")
            
            # Recommendation section
            recommendation = data.get("recommendation", {})
            if recommendation:
                lines.append("💡 המלצות:")
                approved_loan = recommendation.get("approved_loan_ceiling", 0)
                recommended_payment = recommendation.get("recommended_monthly_payment", 0)
                cash_gap = recommendation.get("cash_gap_for_purchase", 0)
                
                # Always show approved loan amount
                lines.append(f"  • סכום משכנתא מומלץ: ₪{approved_loan:,.0f}")
                
                # Show monthly payment
                if recommended_payment > 0:
                    # Check if this is estimated (based on LTV) or calculated from income
                    max_loan_from_payment = recommendation.get("max_loan_from_payment", 0)
                    if max_loan_from_payment == 0 and approved_loan > 0:
                        # Estimated payment based on LTV loan
                        lines.append(f"  • תשלום חודשי משוער: ₪{recommended_payment:,.0f} (מבוסס על LTV 70%)")
                    else:
                        # Calculated from actual income data
                        lines.append(f"  • תשלום חודשי מומלץ: ₪{recommended_payment:,.0f}")
                else:
                    lines.append("  • תשלום חודשי מומלץ: ₪0 (לא ניתן לחשב ללא נתוני הכנסות)")
                
                # Show cash gap information
                if cash_gap > 0:
                    lines.append(f"  ⚠️  פער הון עצמי: ₪{cash_gap:,.0f} (חסר לקניית הנכס)")
                elif cash_gap == 0 and approved_loan > 0:
                    lines.append("  ✓ הון עצמי מספיק לקניית הנכס")
                lines.append("")
            
            # Notes section
            notes = data.get("notes", [])
            if notes:
                lines.append("ℹ️  הערות:")
                for note in notes:
                    lines.append(f"  • {note}")
                lines.append("")
            
            return "\n".join(lines)
        
        async def analyze_mortgage_tool_func(
            property_price: float,
            savings_total: float,
            annual_rate_pct: Optional[float] = None,
            term_years: Optional[int] = None,
        ) -> str:
            """Analyze mortgage affordability and payment scenarios."""
            try:
                result = await analyze_mortgage(ctx, property_price, savings_total, annual_rate_pct, term_years)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    return _format_mortgage_analysis(data)
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        analyze_mortgage_tool = StructuredTool.from_function(
            func=wrap_async_tool(analyze_mortgage_tool_func),
            name="analyze_mortgage_tool",
            description="ניתוח יכולת משכנתא."
        )
        
        # CRM tools
        async def list_contacts_tool_func(
            fields: Optional[List[str]] = None,
            limit: Optional[int] = 5,
        ) -> str:
            """List all CRM contacts."""
            try:
                limit = _safe_limit(limit)
                result = await list_contacts(ctx, page=1, page_size=limit, fields=fields, limit=limit, compact=True)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", [])
                    # Use generic enrichment system (no enrichment needed, just formatting)
                    return await _enrich_list_output(
                        tool_name="list_contacts_tool",
                        data=data,
                        limit=limit,
                        enrichment_func=None,  # Contacts already have all needed data
                    )
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        list_contacts_tool = StructuredTool.from_function(
            func=wrap_async_tool(list_contacts_tool_func),
            name="list_contacts_tool",
            description="רשימת אנשי קשר ב-CRM."
        )
        
        async def create_contact_tool_func(
            name: str,
            email: Optional[str] = None,
            phone: Optional[str] = None,
        ) -> str:
            """Create a new CRM contact."""
            try:
                result = await create_contact(ctx, name, email, phone)
                if isinstance(result, dict) and result.get("success"):
                    return f"איש קשר נוצר: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        create_contact_tool = StructuredTool.from_function(
            func=wrap_async_tool(create_contact_tool_func),
            name="create_contact_tool",
            description="יצירת איש קשר ב-CRM."
        )
        
        async def list_leads_tool_func(
            status: Optional[str] = None,
            fields: Optional[List[str]] = None,
            limit: Optional[int] = 5,
        ) -> str:
            """List all leads, optionally filtered by status."""
            try:
                limit = _safe_limit(limit)
                result = await list_leads(ctx, status=status, fields=fields, limit=limit, compact=True)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", [])
                    # Custom formatter for leads
                    def format_lead(lead: Dict[str, Any]) -> str:
                        parts = []
                        if "contact" in lead and isinstance(lead.get("contact"), dict):
                            contact_name = lead["contact"].get("name", "")
                            if contact_name:
                                parts.append(f"**{contact_name}**")
                        if "status" in lead:
                            parts.append(f"סטטוס: {lead['status']}")
                        if "asset_id" in lead:
                            parts.append(f"נכס #{lead['asset_id']}")
                        if "updated_at" in lead and lead.get("updated_at"):
                            parts.append(f"עודכן: {lead['updated_at']}")
                        return " • ".join(parts) if parts else str(lead)
                    
                    return await _enrich_list_output(
                        tool_name="list_leads_tool",
                        data=data,
                        limit=limit,
                        enrichment_func=None,
                        formatter=format_lead,
                    )
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        list_leads_tool = StructuredTool.from_function(
            func=wrap_async_tool(list_leads_tool_func),
            name="list_leads_tool",
            description="רשימת לידים עם סינון אופציונלי."
        )
        
        async def create_lead_tool_func(contact_id: int, asset_id: int) -> str:
            """Create a new lead linking a contact to an asset."""
            try:
                result = await create_lead(ctx, contact_id, asset_id)
                if isinstance(result, dict) and result.get("success"):
                    return f"ליד נוצר: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        create_lead_tool = StructuredTool.from_function(
            func=wrap_async_tool(create_lead_tool_func),
            name="create_lead_tool",
            description="יצירת ליד חדש לנכס."
        )
        
        async def list_tasks_tool_func(
            status: Optional[str] = None,
            fields: Optional[List[str]] = None,
            limit: Optional[int] = 5,
        ) -> str:
            """List all CRM tasks, optionally filtered by status."""
            try:
                limit = _safe_limit(limit)
                result = await list_tasks(ctx, contact_id=None, lead_id=None, status=status, page=None, page_size=None, fields=fields, limit=limit, compact=True)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", [])
                    # Custom formatter for tasks
                    def format_task(task: Dict[str, Any]) -> str:
                        parts = []
                        if "title" in task:
                            parts.append(f"**{task['title']}**")
                        if "status" in task:
                            parts.append(f"סטטוס: {task['status']}")
                        if "due_at" in task and task.get("due_at"):
                            parts.append(f"תאריך יעד: {task['due_at']}")
                        if "contact" in task and isinstance(task.get("contact"), dict):
                            contact_name = task["contact"].get("name", "")
                            if contact_name:
                                parts.append(f"איש קשר: {contact_name}")
                        return " • ".join(parts) if parts else str(task)
                    
                    return await _enrich_list_output(
                        tool_name="list_tasks_tool",
                        data=data,
                        limit=limit,
                        enrichment_func=None,
                        formatter=format_task,
                    )
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        list_tasks_tool = StructuredTool.from_function(
            func=wrap_async_tool(list_tasks_tool_func),
            name="list_tasks_tool",
            description="רשימת משימות עם סינון אופציונלי."
        )
        
        tools_list = [
            list_assets_tool,
            get_asset_filters_tool,
            get_asset_tool,
            create_asset_tool,
            get_asset_data_tool,
            list_deals_tool,
            create_deal_tool,
            get_offer_tool,
            estimate_build_cost_tool,
            get_cost_options_tool,
            calculate_deal_expenses_tool,
            analyze_mortgage_tool,
            list_contacts_tool,
            create_contact_tool,
            list_leads_tool,
            create_lead_tool,
            list_tasks_tool,
        ]
        
        # Add Internet access tool if enabled
        if self.internet_enabled:
            async def fetch_web_page_tool_func(url: str, scope: Optional[str] = None) -> str:
                """Fetch a web page from allowed domains only.
                
                IMPORTANT: 
                - For yad2.co.il, mavat.iplan.gov.il, govmap.gov.il, nadlan.gov.il, madlan.co.il - 
                  use the appropriate MCP tools instead! They provide better structured data.
                - This tool is for sites WITHOUT MCP servers or one-off lookups.
                
                Allowed domains:
                - *.gov.il - All Israeli government websites (e.g., data.gov.il, mavat.iplan.gov.il, etc.)
                - boi.org.il - Bank of Israel (interest rates, mortgage data)
                - nadlaner.com, api.nadlaner.com - Internal application domains
                
                The tool:
                - Only allows GET requests (no POST/PUT/DELETE)
                - Converts HTML to plain text (no JavaScript execution)
                - Limits response size to 1 MB
                - Implements rate limiting (5 requests per minute)
                - Filters out potential injection vectors
                - Caches responses for efficiency
                
                Parameters:
                - url: Full URL to fetch (must start with http:// or https://)
                - scope: Optional description of why you're fetching this URL (for logging)
                
                Returns:
                - Plain text content extracted from the page
                - Source URL (may differ if redirected)
                - Error message if fetch failed
                """
                try:
                    fetcher = get_fetcher()
                    result = fetcher.fetch(url, scope)
                    
                    if result.get('success'):
                        content = result.get('content', '')
                        source_url = result.get('url', url)
                        cached = result.get('cached', False)
                        
                        response = f"Content from {source_url}:\n\n{content}"
                        if cached:
                            response += "\n\n[Retrieved from cache]"
                        return response
                    else:
                        error = result.get('error', 'Unknown error')
                        return f"Error fetching {url}: {error}"
                except Exception as e:
                    logger.exception("Error in fetch_web_page_tool: %s", e)
                    return f"Error fetching {url}: {str(e)}"
            
            fetch_web_page_tool = StructuredTool.from_function(
                func=wrap_async_tool(fetch_web_page_tool_func),
                name="fetch_web_page_tool",
                description="שליפת דפי אינטרנט מדומיינים מורשים בלבד."
            )
            
            tools_list.append(fetch_web_page_tool)
            logger.info("Internet access tool enabled")
        
        # Log tool names for debugging
        tool_names = [tool.name for tool in tools_list]
        logger.debug("Created tools: %s", ", ".join(tool_names))
        
        return tools_list
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Create the agent executor with system prompt."""
        scope_sentence = (
            "אתה עוזר AI מקצועי לסוכני נדל\"ן, המסייע בחיפוש וניתוח נכסים, ניהול עסקאות, "
            "חישובי הוצאות, ניתוח משכנתא וניהול CRM."
        )

        internet_access_note = ""
        if self.internet_enabled:
            internet_access_note = "\nיש לך גישה מוגבלת לדפי אינטרנט מדומיינים מורשים באמצעות fetch_web_page_tool."

        language_sentence = (
            "ענה בעברית למשתמשים בעברית ועבור לשפה אחרת רק אם התבקשת במפורש. הצג נתונים בצורה ברורה בעברית."
        )
        
        tool_output_instruction = (
            "\n\nכאשר כלי מחזיר תוצאות מפורמטות, הצג אותן ישירות למשתמש."
        )

        system_prompt = f"{scope_sentence}{internet_access_note}\n\n{language_sentence}{tool_output_instruction}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)

        self.system_prompt = system_prompt

        # Simple error handler for parsing errors
        def handle_parsing_error(error: Exception) -> str:
            """Handle parsing errors gracefully."""
            error_msg = str(error)
            logger.error("Parsing error occurred: %s", error_msg)
            if "'NoneType' object has no attribute 'get'" in error_msg or "NoneType" in error_msg:
                return "אירעה שגיאה בעיבוד הבקשה. אנא נסה לנסח מחדש את השאלה."
            return "אירעה שגיאה בעיבוד הבקשה. אנא נסה שוב."
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,  # Enable verbose to show tool chain in logs
            handle_parsing_errors=handle_parsing_error,
            max_iterations=5,
            return_intermediate_steps=False,
        )

    def _get_tools_budget_message(self) -> Optional[Dict[str, str]]:
        """Return a system message describing tools for budgeting calculations."""

        if not self.tools:
            return None

        if self._tool_budget_message_cache is not None:
            return self._tool_budget_message_cache.copy()

        descriptions = []
        for tool in self.tools:
            name = getattr(tool, "name", "tool")
            description = _normalize_content(getattr(tool, "description", ""))
            if description:
                descriptions.append(f"{name}: {description}")
            else:
                descriptions.append(name)

        if not descriptions:
            return None

        content = "Available tools:\n" + "\n".join(descriptions)
        self._tool_budget_message_cache = {"role": "system", "content": content}
        return self._tool_budget_message_cache.copy()

    def _prepare_history_for_llm(
        self,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]],
    ) -> List[Dict[str, str]]:
        """Prepare chat history with summaries and enforce token budget.
        
        Note: System prompt and current user message are already in the ChatPromptTemplate,
        so we only need to prepare the history itself. Token budgeting accounts for
        system prompts and current message, but they're not included in the returned history.
        """

        history = chat_history or []
        processed_history = build_history_with_summary(
            history,
            keep_last=self.history_keep_last,
            summary_max_chars=self.history_summary_max_chars,
        )

        # Calculate token budget for history only (system prompt and current message are in template)
        system_prompt = getattr(self, "system_prompt", "")
        tool_budget_message = self._get_tools_budget_message()
        
        # Build full message set for token budgeting (but won't be returned)
        budget_messages: List[Dict[str, str]] = []
        if system_prompt:
            budget_messages.append({"role": "system", "content": system_prompt})
        if tool_budget_message:
            budget_messages.append(tool_budget_message)
        budget_messages.extend(processed_history)
        budget_messages.append({"role": "user", "content": user_message})

        # Enforce token budget on full message set
        trimmed_messages = enforce_token_budget(
            budget_messages,
            max_tokens=self.max_input_tokens,
            reserve_for_output=self.output_token_reserve,
        )

        # Extract only history messages (filter out system prompt, tool budget, and current user message)
        trimmed_history: List[Dict[str, str]] = []
        tool_budget_content = tool_budget_message.get("content") if tool_budget_message else None
        total_messages = len(trimmed_messages)
        
        for index, msg in enumerate(trimmed_messages):
            role = msg.get("role")
            content = msg.get("content")
            
            # Skip system prompt (already in template)
            if system_prompt and role == "system" and content == system_prompt:
                continue
            # Skip tool budget message (not needed in history)
            if tool_budget_content and role == "system" and content == tool_budget_content:
                continue
            # Skip current user message (already in template as {input})
            if index == total_messages - 1 and role == "user" and content == user_message:
                continue
            
            trimmed_history.append({"role": role or "user", "content": content or ""})

        return trimmed_history

    async def chat(self, message: str, chat_history: Optional[List] = None, track_tool_calls: bool = True) -> Dict[str, Any]:
        """Chat with the agent.
        
        Args:
            message: User message
            chat_history: Optional chat history (list of messages)
            track_tool_calls: Whether to track tool calls
        
        Returns:
            Dictionary with 'response' and 'tool_calls' keys
        
        Raises:
            Exception: If agent execution fails, with a user-friendly error message
        """
        history = self._build_chat_history(chat_history)
        prepared_history = self._prepare_history_for_llm(message, history)

        try:
            if track_tool_calls:
                callback = ToolCallTracker()
                result = await self.agent_executor.ainvoke(
                    {"input": message, "chat_history": prepared_history},
                    config={"callbacks": [callback]}
                )
                tool_calls = callback.get_tool_calls()
                # Translate tool names to Hebrew
                for tool_call in tool_calls:
                    tool_call["tool_hebrew"] = translate_tool_name(tool_call["tool"])
                response_text = result.get("output", "")
                
                # Check if we have formatted results from list tools
                # If so, use them as the final answer even if LLM didn't generate a response
                list_tool_names = ["list_assets_tool", "list_contacts_tool", "list_tasks_tool", 
                                  "list_leads_tool", "list_deals_tool"]
                formatted_tool_output = None
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool", "")
                    if tool_name in list_tool_names:
                        output = tool_call.get("output", "")
                        # Check if output contains formatted results
                        if output and ("₪" in output or "מחיר:" in output or "**" in output or 
                                     "סטטוס:" in output or "•" in output):
                            formatted_tool_output = output
                            break
                
                # If we have formatted tool output and no LLM response, use tool output as final answer
                if formatted_tool_output and not response_text:
                    logger.info("Using formatted tool output as final response (no LLM response)")
                    response_text = formatted_tool_output
                # If we have both, check if LLM response already includes the tool output
                elif formatted_tool_output and response_text:
                    # Check if response already includes tool outputs
                    has_tool_outputs = any(
                        keyword in response_text for keyword in ["₪", "מחיר:", "**", "סטטוס:", "•"]
                    )
                    if not has_tool_outputs:
                        logger.info("LLM response doesn't include tool outputs, but tool output is formatted - using tool output")
                        response_text = formatted_tool_output
                
                # Only show tool outputs if response doesn't already include formatted results
                if not formatted_tool_output:
                    tool_outputs_section = []
                    for tool_call in tool_calls:
                        if tool_call.get("output"):
                            tool_hebrew = tool_call.get("tool_hebrew", tool_call.get("tool", ""))
                            output = tool_call["output"]
                            
                            # Skip showing raw list tool outputs if they're just IDs without details
                            if tool_call.get("tool") in list_tool_names:
                                # Only show if it doesn't contain formatted results
                                if not ("₪" in output or "מחיר:" in output or "**" in output or 
                                       "סטטוס:" in output or "•" in output):
                                    # Skip raw interim outputs
                                    continue
                            
                            # Format tool output nicely
                            tool_outputs_section.append(f"**{tool_hebrew}:**")
                            tool_outputs_section.append(output)
                            tool_outputs_section.append("")  # Empty line between tools
                    
                    # Only append if we have tool outputs to show
                    if tool_outputs_section:
                        tool_outputs_text = "\n".join(tool_outputs_section).strip()
                        
                        if not response_text:
                            # No LLM response, use tool outputs
                            logger.info("No LLM response, using tool outputs")
                            response_text = tool_outputs_text
                        else:
                            # Check if response already includes tool outputs
                            has_tool_outputs = any(
                                keyword in response_text for keyword in ["id:", "נמצאו", "property", "נכס", "₪"]
                            )
                            # If response doesn't include tool outputs, append them
                            if not has_tool_outputs:
                                logger.info("Appending tool outputs to response")
                                response_text = f"{response_text}\n\n---\n\n**תוצאות החיפוש:**\n{tool_outputs_text}"
                            else:
                                logger.info("Response already includes tool outputs")
                else:
                    logger.info("Using formatted tool output as final response")
                
                self._record_interaction(message, response_text)
                return {
                    "response": response_text,
                    "tool_calls": tool_calls
                }
            else:
                result = await self.agent_executor.ainvoke({
                    "input": message,
                    "chat_history": prepared_history,
                })
                response_text = result.get("output", "")
                self._record_interaction(message, response_text)
                return {
                    "response": response_text,
                    "tool_calls": []
                }
        except Exception as e:
            # Log the full error for debugging
            logger.exception("Error in agent chat: %s", e)
            # Extract user-friendly error message
            error_msg = self._extract_error_message(e)
            # Raise with user-friendly message
            raise Exception(error_msg) from e
    
    async def chat_stream(self, message: str, chat_history: Optional[List] = None):
        """Stream chat responses from the agent.
        
        Args:
            message: User message
            chat_history: Optional chat history (list of messages)
        
        Yields:
            Dictionary events with 'type' and data:
            - {'type': 'tool_call_start', 'tool': str, 'tool_hebrew': str, 'input': str}
            - {'type': 'tool_call_end', 'tool': str, 'tool_hebrew': str, 'output': str}
            - {'type': 'tool_call_error', 'tool': str, 'tool_hebrew': str, 'error': str}
            - {'type': 'chunk', 'content': str}
            - {'type': 'complete', 'response': str, 'tool_calls': list}
            - {'type': 'error', 'error': str}
        """
        history = self._build_chat_history(chat_history)
        prepared_history = self._prepare_history_for_llm(message, history)
        callback = StreamingCallbackHandler()
        
        # Run agent execution in background task
        async def run_agent():
            try:
                logger.info("Starting agent execution for message: %s", message[:100])
                # Stream agent execution with timeout
                # AgentExecutor.astream yields intermediate steps, not final output
                # The callback handler will receive LLM tokens via on_llm_new_token
                final_output = None
                last_chunk_keys = set()  # Track what keys we've seen in chunks
                
                async def stream_with_timeout():
                    nonlocal final_output, last_chunk_keys
                    chunk_count = 0
                    last_chunk = None
                    async for chunk in self.agent_executor.astream(
                        {"input": message, "chat_history": prepared_history},
                        config={"callbacks": [callback]}
                    ):
                        chunk_count += 1
                        last_chunk = chunk  # Keep track of last chunk
                        # Log chunks for debugging (astream yields intermediate agent steps)
                        logger.debug("Agent step %d received: %s", chunk_count, str(chunk)[:200])
                        
                        # Track chunk structure
                        if isinstance(chunk, dict):
                            last_chunk_keys.update(chunk.keys())
                            # Check for output in various possible keys
                            for key in ["output", "messages", "agent_outcome", "return_values"]:
                                if key in chunk:
                                    value = chunk[key]
                                    # Handle different value types
                                    if isinstance(value, str) and value:
                                        final_output = value
                                        logger.info("Found final output in chunk[%s]: %s", key, value[:100])
                                        break
                                    elif isinstance(value, list) and value:
                                        # Sometimes output is in a list of messages
                                        for msg in value:
                                            if hasattr(msg, 'content') and msg.content:
                                                final_output = str(msg.content)
                                                logger.info("Found final output in chunk[%s] message: %s", key, final_output[:100])
                                                break
                                        if final_output:
                                            break
                            
                            # If we found final output, ensure it's captured
                            if final_output and final_output not in callback.complete_response:
                                logger.info("Final output not in callback, adding it directly")
                                callback.complete_response = final_output
                                # Send as a single chunk event
                                try:
                                    callback.chunk_queue.put_nowait({"type": "chunk", "content": final_output})
                                except asyncio.QueueFull:
                                    # If queue is full, at least ensure response is captured
                                    pass
                    
                    logger.info("Agent astream finished. Total chunks: %d, Last chunk keys: %s", 
                              chunk_count, last_chunk_keys)
                    logger.info("Last chunk content: %s", str(last_chunk)[:500] if last_chunk else "None")
                    # Signal that astream has finished - this helps the outer loop detect completion
                    # even if we're still doing post-processing
                    try:
                        callback.chunk_queue.put_nowait({"type": "astream_finished"})
                    except asyncio.QueueFull:
                        # Try to make space
                        try:
                            callback.chunk_queue.get_nowait()
                            callback.chunk_queue.put_nowait({"type": "astream_finished"})
                        except:
                            pass
                    # If astream finished but we have no response, the agent executor is done
                    # but the LLM might not have generated a final response
                    if not callback.complete_response and not final_output:
                        logger.warning("Agent executor finished but no LLM response was generated")
                        # Try to extract from last chunk one more time
                        if last_chunk and isinstance(last_chunk, dict):
                            logger.info("Attempting to extract output from last chunk: %s", list(last_chunk.keys()))
                
                await asyncio.wait_for(stream_with_timeout(), timeout=300.0)  # 5 minute timeout
                logger.info("Agent execution completed successfully. Final output from chunks: %s", final_output)
                logger.info("Callback complete_response length: %d", len(callback.complete_response))
                logger.info("Callback complete_response content: %s", callback.complete_response[:500] if callback.complete_response else "Empty")
                
                # Wait a bit for any remaining tokens to come through the callback
                # Sometimes tokens arrive slightly after astream finishes
                await asyncio.sleep(0.5)  # Wait 500ms for any delayed tokens
                logger.info("After wait, callback complete_response length: %d", len(callback.complete_response))
                
                # Ensure final output is captured if it wasn't streamed via tokens
                # The final_output from chunks might contain the complete response
                if final_output:
                    # If final_output is longer or different, use it
                    if len(final_output) > len(callback.complete_response):
                        logger.info("Final output from chunks is longer, updating callback response")
                        callback.complete_response = final_output
                    elif final_output not in callback.complete_response:
                        logger.info("Final output not in callback response, appending it")
                        callback.complete_response += final_output
                
                # If we still have no response but tools were called, check if we have formatted tool output
                # Use formatted tool output as final response if available
                if not callback.complete_response:
                    tool_calls = callback.get_tool_calls()
                    list_tool_names = ["list_assets_tool", "list_contacts_tool", "list_tasks_tool", 
                                      "list_leads_tool", "list_deals_tool"]
                    for tool_call in tool_calls:
                        tool_name = tool_call.get("tool", "")
                        if tool_name in list_tool_names:
                            output = tool_call.get("output", "")
                            if output and ("₪" in output or "מחיר:" in output or "**" in output or 
                                         "סטטוס:" in output or "•" in output):
                                logger.info("No LLM response but have formatted tool output - using it")
                                callback.complete_response = output
                                break
                
                logger.info("Final callback response length after processing: %d", len(callback.complete_response))
                logger.info("Final callback response preview: %s", callback.complete_response[:200] if callback.complete_response else "Empty")
                logger.info("Tool calls count: %d", len(callback.get_tool_calls()))
                callback.mark_finished()
            except asyncio.TimeoutError:
                logger.error("Agent execution timed out after 5 minutes")
                try:
                    error_msg = "הבקשה ארכה יותר מדי זמן. אנא נסה שוב."
                    callback.chunk_queue.put_nowait({"type": "error", "error": error_msg})
                except Exception:
                    pass
                callback.mark_finished()
            except Exception as e:
                logger.exception("Error in agent execution: %s", e)
                try:
                    # Use the error extraction method for consistent error messages
                    error_msg = self._extract_error_message(e)
                    callback.chunk_queue.put_nowait({"type": "error", "error": error_msg})
                except Exception:
                    # Fallback if error extraction fails
                    try:
                        callback.chunk_queue.put_nowait({"type": "error", "error": "אירעה שגיאה בעת ביצוע הסוכן. אנא נסה שוב."})
                    except Exception:
                        pass
                finally:
                    callback.mark_finished()
        
        # Start agent execution
        agent_task = asyncio.create_task(run_agent())
        
        try:
            # Stream events from callback queue
            max_wait_time = 300  # Maximum 5 minutes total wait time
            start_time = time.time()
            consecutive_timeouts = 0
            max_consecutive_timeouts = 20  # Stop after 2 seconds of no events (20 * 0.1s)
            # Reduced from 50 to 20 because if agent executor finishes, we should break quickly
            
            agent_finished = False
            error_occurred = False
            
            while True:
                # Check if agent task is done
                if agent_task.done():
                    agent_finished = True
                    # Check if task raised an exception
                    if agent_task.exception():
                        exception = agent_task.exception()
                        logger.exception("Agent task raised exception: %s", exception)
                        error_occurred = True
                        # Send error event if not already sent
                        error_sent = False
                        while not callback.chunk_queue.empty():
                            try:
                                event = callback.chunk_queue.get_nowait()
                                if event and event.get("type") == "error":
                                    error_sent = True
                                    yield event
                                elif event and event.get("type") != "finished":
                                    if event.get("type") in ["tool_call_start", "tool_call_end", "tool_call_error"]:
                                        event["tool_hebrew"] = translate_tool_name(event.get("tool", ""))
                                    yield event
                            except Exception:
                                break
                        # If no error event was found in queue, send one
                        if not error_sent:
                            # Use the error extraction method for consistent error messages
                            error_msg = self._extract_error_message(exception)
                            yield {"type": "error", "error": error_msg}
                    else:
                        # Agent finished successfully, drain remaining events
                        # Make sure to yield all chunks and tool events before breaking
                        while not callback.chunk_queue.empty():
                            try:
                                event = callback.chunk_queue.get_nowait()
                                if event and event.get("type") != "finished":
                                    if event.get("type") in ["tool_call_start", "tool_call_end", "tool_call_error"]:
                                        event["tool_hebrew"] = translate_tool_name(event.get("tool", ""))
                                    yield event
                            except Exception:
                                break
                    break
                
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > max_wait_time:
                    logger.warning("Agent chat stream timeout after %s seconds", max_wait_time)
                    yield {
                        "type": "error",
                        "error": "הבקשה ארכה יותר מדי זמן. אנא נסה שוב."
                    }
                    error_occurred = True
                    break
                
                # Get next event
                event = await callback.get_next_event(timeout=0.1)
                if event:
                    consecutive_timeouts = 0  # Reset timeout counter
                    if event.get("type") == "finished":
                        agent_finished = True
                        break
                    # If astream finished, we know the agent executor is done
                    # Even if run_agent() is still doing post-processing, we can break
                    # after a short delay to allow final processing
                    if event.get("type") == "astream_finished":
                        logger.info("Agent executor astream finished, will break after final processing")
                        final_timeouts = 0
                        for _ in range(10):  # 10 * 0.1s = 1 second
                            final_event = await callback.get_next_event(timeout=0.1)
                            if final_event:
                                final_timeouts = 0  # Reset timeout counter
                                if final_event.get("type") == "finished":
                                    agent_finished = True
                                    break
                                # Yield any final events
                                if final_event.get("type") in ["tool_call_start", "tool_call_end", "tool_call_error"]:
                                    final_event["tool_hebrew"] = translate_tool_name(final_event.get("tool", ""))
                                yield final_event
                            else:
                                final_timeouts += 1
                                # If no events for 0.5 seconds after astream finished, break
                                if final_timeouts >= 5:
                                    logger.info("No more events after astream finished, breaking")
                                    agent_finished = True
                                    break
                        # Break out of main loop since astream is done
                        if agent_finished:
                            break
                        continue
                    # Add Hebrew translation for tool events
                    if event.get("type") in ["tool_call_start", "tool_call_end", "tool_call_error"]:
                        event["tool_hebrew"] = translate_tool_name(event.get("tool", ""))
                    yield event
                else:
                    # No event received (timeout)
                    consecutive_timeouts += 1
                    # Check if agent task is done first (before hitting max timeouts)
                    if agent_task.done():
                        agent_finished = True
                        logger.info("Agent task finished, breaking from event loop")
                        break
                    elif consecutive_timeouts >= max_consecutive_timeouts:
                        # If agent is still running but no events for a while, check if it's actually stuck
                        logger.warning("No events received for %s seconds, but agent still running. Checking task status...", 
                                     consecutive_timeouts * 0.1)
                        # Check one more time if task is done
                        if agent_task.done():
                            agent_finished = True
                            logger.info("Agent task finished during timeout check, breaking")
                            break
                        # Check if we have a complete response - if so, break even if task isn't done
                        if callback.complete_response:
                            logger.info("Have complete response but agent still processing, breaking early")
                            agent_finished = True
                            break
                        # Check if callback is marked as finished
                        if callback._finished:
                            logger.info("Callback marked as finished, breaking")
                            agent_finished = True
                            break
                        # If we've been waiting for more than 10 seconds total, force break
                        elapsed = time.time() - start_time
                        if elapsed > 10.0:
                            logger.warning("Agent task still running after 10 seconds with no events, forcing break")
                            agent_finished = True
                            break
                        # If still running but less than 10 seconds, reset counter and continue
                        logger.warning("Agent task still running, continuing to wait...")
                        consecutive_timeouts = 0  # Reset to allow more time, but log more frequently
            
            # Wait for agent to finish (with timeout) if not already done
            if not agent_finished:
                try:
                    await asyncio.wait_for(agent_task, timeout=5.0)
                    agent_finished = True
                except asyncio.TimeoutError:
                    logger.warning("Agent task did not finish within timeout")
                    # Send error event
                    yield {
                        "type": "error",
                        "error": "הסוכן לא סיים את המשימה בזמן. ייתכן שהתהליך תקוע."
                    }
                    return
            
            # Only send completion event if no error occurred
            if not error_occurred and agent_finished:
                # Get final tool calls and translate
                tool_calls = callback.get_tool_calls()
                for tool_call in tool_calls:
                    tool_call["tool_hebrew"] = translate_tool_name(tool_call["tool"])
                
                # Send completion event
                final_response = callback.get_complete_response()
                logger.info("Agent finished. Response length: %d, Tool calls: %d", 
                          len(final_response) if final_response else 0, len(tool_calls))
                logger.info("Final response content (first 200 chars): %s", 
                          (final_response or "")[:200])
                
                # Check if response already includes formatted results from any list tool
                # Generic detection: look for formatted output patterns
                has_formatted_results = False
                list_tool_names = ["list_assets_tool", "list_contacts_tool", "list_tasks_tool", 
                                  "list_leads_tool", "list_deals_tool"]
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool", "")
                    if tool_name in list_tool_names:
                        output = tool_call.get("output", "")
                        # Check if output contains formatted results (with prices, addresses, bold text, etc.)
                        if output and ("₪" in output or "מחיר:" in output or "**" in output or 
                                     "סטטוס:" in output or "•" in output):
                            has_formatted_results = True
                            break
                
                # Only show tool outputs if response doesn't already include formatted results
                if not has_formatted_results:
                    tool_outputs_section = []
                    for tool_call in tool_calls:
                        if tool_call.get("output"):
                            tool_hebrew = tool_call.get("tool_hebrew", tool_call.get("tool", ""))
                            output = tool_call["output"]
                            
                            # Skip showing raw list tool outputs if they're just IDs without details
                            if tool_call.get("tool") in list_tool_names:
                                # Only show if it doesn't contain formatted results
                                if not ("₪" in output or "מחיר:" in output or "**" in output or 
                                       "סטטוס:" in output or "•" in output):
                                    # Skip raw interim outputs
                                    continue
                            
                            # Format tool output nicely
                            tool_outputs_section.append(f"**{tool_hebrew}:**")
                            tool_outputs_section.append(output)
                            tool_outputs_section.append("")  # Empty line between tools
                    
                    # Only append if we have tool outputs to show
                    if tool_outputs_section:
                        tool_outputs_text = "\n".join(tool_outputs_section).strip()
                        
                        if not final_response:
                            # No LLM response, use tool outputs
                            logger.info("No LLM response in stream, using tool outputs")
                            final_response = tool_outputs_text
                        else:
                            # Check if response already includes tool outputs
                            has_tool_outputs = any(
                                keyword in final_response for keyword in ["id:", "נמצאו", "property", "נכס", "₪"]
                            )
                            # If response doesn't include tool outputs, append them
                            if not has_tool_outputs:
                                logger.info("Appending tool outputs to streamed response")
                                final_response = f"{final_response}\n\n---\n\n**תוצאות החיפוש:**\n{tool_outputs_text}"
                            else:
                                logger.info("Streamed response already includes tool outputs")
                else:
                    logger.info("Skipping tool outputs in stream - response already contains formatted results")
                
                # Always send complete event if agent finished successfully
                # Even if response is empty, we should send the event with tool calls
                complete_event = {
                    "type": "complete",
                    "response": final_response or "",
                    "tool_calls": tool_calls
                }
                logger.info("Sending complete event with response length: %d", 
                          len(complete_event["response"]))
                self._record_interaction(message, final_response or "")
                yield complete_event
            elif error_occurred:
                logger.warning("Agent finished with error, not sending complete event")
            else:
                logger.warning("Agent did not finish properly")
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e)
            }
        finally:
            # Ensure agent task is cancelled if still running
            if not agent_task.done():
                agent_task.cancel()
                try:
                    await agent_task
                except asyncio.CancelledError:
                    pass
    
    def run(self, message: str) -> str:
        """Synchronous version of chat (for CLI usage).
        
        Args:
            message: User message
        
        Returns:
            Agent response string
        
        Raises:
            Exception: If agent execution fails, with a user-friendly error message
        """
        import asyncio
        try:
            result = asyncio.run(self.chat(message, track_tool_calls=False))
            response = result.get("response", "") if isinstance(result, dict) else result
            if not response:
                return "לא התקבלה תשובה מהסוכן."
            return response
        except Exception as e:
            # Extract meaningful error message
            error_msg = self._extract_error_message(e)
            raise Exception(error_msg) from e
    
    def _extract_error_message(self, exception: Exception) -> str:
        """Extract user-friendly error message from exception."""
        error_str = str(exception)
        error_lower = error_str.lower()
        
        # Handle NoneType parsing errors (most common issue)
        if "'nonetype' object has no attribute 'get'" in error_lower:
            return "אירעה שגיאה בעיבוד הבקשה. אנא נסה לנסח מחדש את השאלה."
        
        # Handle model decommissioned errors
        if "model" in error_lower and ("decommissioned" in error_lower or "no longer supported" in error_lower):
            return "המודל שנבחר הוצא משימוש. אנא עדכן את משתנה הסביבה GROQ_MODEL למודל תקף."
        
        # Handle API key errors
        if "api key" in error_lower or "authentication" in error_lower or "401" in error_str:
            return "שגיאת אימות: מפתח API לא תקף או חסר."
        
        # Handle rate limit errors
        if "rate limit" in error_lower or "429" in error_str:
            return "השירות עמוס כרגע. אנא נסה שוב בעוד כמה דקות."
        
        # Handle timeout errors
        if "timeout" in error_lower:
            return "הבקשה ארכה יותר מדי זמן. אנא נסה שוב."
        
        # Handle connection errors
        if "connection" in error_lower or "network" in error_lower:
            return "בעיית חיבור לשירות. אנא בדוק את החיבור לאינטרנט ונסה שוב."
        
        # Handle quota errors
        if "quota" in error_lower or "limit" in error_lower:
            return "המגבלה היומית הושגה. אנא נסה שוב מחר."
        
        # Generic fallback
        return "אירעה שגיאה בעת ביצוע הסוכן. אנא נסה שוב."


def main():
    """CLI interface for the Real Estate Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Real Estate Agent CLI")
    # Get default provider from environment variable, fallback to "openai"
    default_provider = os.getenv("LLM_DEFAULT_PROVIDER", "openai").lower()
    if default_provider not in ["openai", "gemini", "groq"]:
        default_provider = "openai"
    parser.add_argument(
        "--provider",
        choices=["openai", "gemini", "groq"],
        default=default_provider,
        help=f"LLM provider to use (default: {default_provider} from LLM_DEFAULT_PROVIDER env var)",
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help="API base URL (defaults to REALESTATE_API_URL env var or localhost)",
    )
    parser.add_argument(
        "--api-token",
        default=None,
        help="API token for authentication (defaults to REALESTATE_API_TOKEN env var)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="LLM temperature (default: 0.3)",
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Message to send to the agent",
    )
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = RealEstateAgent(
        llm_provider=args.provider,
        api_token=args.api_token,
        api_url=args.api_url,
        temperature=args.temperature,
    )
    
    if args.message:
        # Single message mode
        response = agent.run(args.message)
        print(response)
    else:
        # Interactive mode
        print("Real Estate Agent - Interactive Mode")
        print("Type 'exit' or 'quit' to end the conversation\n")
        
        chat_history = []
        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break
                
                response = agent.run(user_input)
                if response:
                    print(f"\nAgent: {response}\n")
                else:
                    print("\nAgent: לא התקבלה תשובה.\n")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                # Error message is already user-friendly from _extract_error_message
                error_msg = str(e)
                print(f"\nError: {error_msg}\n")
                logger.exception("Error in interactive mode: %s", e)


if __name__ == "__main__":
    main()
