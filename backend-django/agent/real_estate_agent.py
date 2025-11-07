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
import threading
import time
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# LangChain imports
from langchain_core.tools import BaseTool, StructuredTool
from langchain_core.callbacks import BaseCallbackHandler
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# Add project root to path (after imports to satisfy linter)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
    get_asset = get_underlying_func(mcp_server.get_asset)
    create_asset = get_underlying_func(mcp_server.create_asset)
    get_asset_transactions = get_underlying_func(mcp_server.get_asset_transactions)
    get_asset_appraisal = get_underlying_func(mcp_server.get_asset_appraisal)
    list_deals = get_underlying_func(mcp_server.list_deals)
    create_deal = get_underlying_func(mcp_server.create_deal)
    get_offer = get_underlying_func(mcp_server.get_offer)
    estimate_build_cost = get_underlying_func(mcp_server.estimate_build_cost)
    get_cost_options = get_underlying_func(mcp_server.get_cost_options)
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
    get_asset = _stub_func
    create_asset = _stub_func
    get_asset_transactions = _stub_func
    get_asset_appraisal = _stub_func
    list_deals = _stub_func
    create_deal = _stub_func
    get_offer = _stub_func
    estimate_build_cost = _stub_func
    get_cost_options = _stub_func
    analyze_mortgage = _stub_func
    list_contacts = _stub_func
    create_contact = _stub_func
    list_leads = _stub_func
    create_lead = _stub_func
    list_tasks = _stub_func


class ToolCallTracker(BaseCallbackHandler):
    """Callback handler to track tool calls during agent execution."""
    
    def __init__(self):
        self.tool_calls = []
        self.current_tool_call = None
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """Called when a tool starts running."""
        tool_name = serialized.get("name", "unknown_tool")
        self.current_tool_call = {
            "tool": tool_name,
            "input": input_str,
            "status": "running",
            "output": None
        }
        self.tool_calls.append(self.current_tool_call)
    
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a tool finishes running."""
        if self.current_tool_call:
            self.current_tool_call["status"] = "completed"
            self.current_tool_call["output"] = output[:200]  # Truncate long outputs
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
        # Put token in queue for async consumption
        try:
            self.chunk_queue.put_nowait({"type": "chunk", "content": token})
        except asyncio.QueueFull:
            pass  # Queue is full, skip this chunk
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """Called when a tool starts running."""
        tool_name = serialized.get("name", "unknown_tool")
        self.current_tool_call = {
            "tool": tool_name,
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
            self.current_tool_call["status"] = "completed"
            self.current_tool_call["output"] = str(output)[:200] if output else ""  # Truncate long outputs
            tool_name = self.current_tool_call["tool"]
            self.current_tool_call = None
            try:
                self.chunk_queue.put_nowait({
                    "type": "tool_call_end",
                    "tool": tool_name,
                    "output": str(output)[:200] if output else ""
                })
            except asyncio.QueueFull:
                # Try to make space
                try:
                    self.chunk_queue.get_nowait()
                    self.chunk_queue.put_nowait({
                        "type": "tool_call_end",
                        "tool": tool_name,
                        "output": str(output)[:200] if output else ""
                    })
                except:
                    pass
    
    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when a tool encounters an error."""
        if self.current_tool_call:
            self.current_tool_call["status"] = "error"
            self.current_tool_call["output"] = f"Error: {str(error)}"
            tool_name = self.current_tool_call["tool"]
            self.current_tool_call = None
            try:
                self.chunk_queue.put_nowait({
                    "type": "tool_call_error",
                    "tool": tool_name,
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
        "get_asset_tool": "קבלת פרטי נכס",
        "create_asset_tool": "יצירת נכס",
        "get_asset_transactions_tool": "קבלת היסטוריית עסקאות",
        "get_asset_appraisal_tool": "קבלת הערכת שווי",
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
    }
    return translations.get(tool_name, tool_name.replace("_tool", "").replace("_", " "))


class RealEstateAgent:
    """Real Estate Agent powered by LangChain."""
    
    def __init__(
        self,
        llm_provider: str = "openai",
        api_token: Optional[str] = None,
        api_url: Optional[str] = None,
        temperature: float = 0.3,
    ):
        """Initialize the Real Estate Agent.
        
        Args:
            llm_provider: LLM provider to use ("openai", "gemini", or "groq")
            api_token: Optional API token for authenticated requests
            api_url: Optional API base URL (defaults to env var or localhost)
            temperature: LLM temperature setting
        """
        self.api_token = api_token or os.getenv("REALESTATE_API_TOKEN")
        self.api_url = api_url or os.getenv("REALESTATE_API_URL", "http://127.0.0.1:8000/api")
        
        # Set environment variables for MCP tools
        if self.api_token:
            os.environ["REALESTATE_API_TOKEN"] = self.api_token
        os.environ["REALESTATE_API_URL"] = self.api_url
        
        # Initialize LLM
        self.llm = self._create_llm(llm_provider, temperature)
        
        # Create tools
        self.tools = self._create_tools()
        
        # Create agent
        self.agent_executor = self._create_agent_executor()
    
    def _create_llm(self, provider: str, temperature: float):
        """Create LLM instance based on provider."""
        # Helper to get API key from env or Django settings
        def get_api_key(env_var_name: str, settings_attr: str = None) -> Optional[str]:
            key = os.getenv(env_var_name)
            if key:
                return key
            # Try Django settings if available
            try:
                from django.conf import settings
                if settings_attr:
                    return getattr(settings, settings_attr, None)
            except ImportError:
                pass
            return None
        
        if provider == "openai":
            api_key = get_api_key("OPENAI_API_KEY", "OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            return ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=temperature,
                api_key=api_key,
            )
        elif provider == "gemini":
            api_key = get_api_key("GEMINI_API_KEY", "GEMINI_API_KEY") or get_api_key("GOOGLE_API_KEY", "GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required")
            return ChatGoogleGenerativeAI(
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                temperature=temperature,
                google_api_key=api_key,
            )
        elif provider == "groq":
            api_key = get_api_key("GROQ_API_KEY", "GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable is required")
            # Groq uses OpenAI-compatible API
            return ChatOpenAI(
                model=os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
                temperature=temperature,
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1",
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def _create_tools(self) -> List[BaseTool]:
        """Create LangChain tools from MCP server functions."""
        # Create a context object for MCP tools
        class MockContext:
            def info(self, msg: str):
                pass
        
        ctx = MockContext()
        
        # Helper function to wrap async tool functions for LangChain
        def wrap_async_tool(async_func):
            """Wrap an async function to be used with LangChain tools."""
            import functools
            
            @functools.wraps(async_func)
            def sync_wrapper(*args, **kwargs):
                """Synchronous wrapper that runs the async function."""
                # Check if we're in an async context
                try:
                    # Try to get the running loop
                    loop = asyncio.get_running_loop()
                    # We're in an async context - need to run in a separate thread with its own loop
                    result = None
                    exception = None
                    
                    def run_in_new_loop():
                        nonlocal result, exception
                        try:
                            # Create a new event loop in this thread
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                result = new_loop.run_until_complete(async_func(*args, **kwargs))
                            finally:
                                new_loop.close()
                        except Exception as e:
                            exception = e
                    
                    thread = threading.Thread(target=run_in_new_loop, daemon=True)
                    thread.start()
                    thread.join(timeout=300)  # 5 minute timeout
                    
                    if thread.is_alive():
                        raise TimeoutError("Tool execution timed out")
                    
                    if exception:
                        raise exception
                    return result
                except RuntimeError:
                    # No running loop - we can use asyncio.run directly
                    return asyncio.run(async_func(*args, **kwargs))
            
            return sync_wrapper
        
        # Wrap MCP functions as LangChain tools
        # Assets tools
        async def list_assets_tool_func(
            city: Optional[str] = None,
            max_price: Optional[int] = None,
            min_price: Optional[int] = None,
            rooms: Optional[int] = None,
            page: Optional[int] = None,
        ) -> str:
            """List all assets with optional filtering. Use this to search for properties.
            
            Parameters:
            - city: City name (e.g., 'תל אביב', 'ירושלים') - REQUIRED for location-based searches
            - max_price: Maximum price in shekels (e.g., 4000000 for 4 million)
            - min_price: Minimum price in shekels
            - rooms: Number of rooms
            - page: Page number for pagination (default: 1)
            
            Example: list_assets_tool(city='תל אביב', max_price=4000000)
            """
            try:
                result = await list_assets(ctx, city, max_price, min_price, rooms, page)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    if isinstance(data, dict) and "results" in data:
                        assets = data["results"]
                        return f"נמצאו {len(assets)} נכסים:\n" + "\n".join([
                            f"- נכס {a.get('id')}: {a.get('address', 'לא זמין')} - {a.get('price', 'לא זמין')} ש\"ח"
                            for a in assets[:10]
                        ])
                    return str(data)
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        list_assets_tool = StructuredTool.from_function(
            func=wrap_async_tool(list_assets_tool_func),
            name="list_assets_tool",
            description="""חיפוש נכסים עם אפשרויות סינון. 
            
            פרמטרים:
            - city: שם העיר (לדוגמה: 'תל אביב', 'ירושלים') - חובה לחיפוש לפי מיקום
            - max_price: מחיר מקסימלי בשקלים (לדוגמה: 4000000 עבור 4 מיליון)
            - min_price: מחיר מינימלי בשקלים
            - rooms: מספר חדרים
            - page: מספר עמוד (ברירת מחדל: 1)
            
            דוגמה: list_assets_tool(city='תל אביב', max_price=4000000)
            
            חשוב: השתמש בפרמטר 'city' לחיפוש לפי מיקום, לא 'location' או 'lang'."""
        )
        
        async def get_asset_tool_func(asset_id: int, include_documents: bool = False) -> str:
            """Get detailed information for a specific asset by ID."""
            try:
                result = await get_asset(ctx, asset_id, include_documents)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    return f"נכס {asset_id}:\n" + str(data)
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        get_asset_tool = StructuredTool.from_function(
            func=wrap_async_tool(get_asset_tool_func),
            name="get_asset_tool",
            description="קבלת פרטים מפורטים על נכס ספציפי לפי מזהה. מקבל עברית ואנגלית."
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
            description="יצירת נכס חדש. יש לספק פרטי כתובת. מקבל עברית ואנגלית."
        )
        
        async def get_asset_transactions_tool_func(asset_id: int) -> str:
            """Get transaction history for an asset."""
            try:
                result = await get_asset_transactions(ctx, asset_id)
                if isinstance(result, dict) and result.get("success"):
                    return f"עסקאות עבור נכס {asset_id}: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        get_asset_transactions_tool = StructuredTool.from_function(
            func=wrap_async_tool(get_asset_transactions_tool_func),
            name="get_asset_transactions_tool",
            description="קבלת היסטוריית עסקאות של נכס."
        )
        
        async def get_asset_appraisal_tool_func(asset_id: int) -> str:
            """Get appraisal analysis for an asset including comparable sales."""
            try:
                result = await get_asset_appraisal(ctx, asset_id)
                if isinstance(result, dict) and result.get("success"):
                    return f"הערכת שווי עבור נכס {asset_id}: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        get_asset_appraisal_tool = StructuredTool.from_function(
            func=wrap_async_tool(get_asset_appraisal_tool_func),
            name="get_asset_appraisal_tool",
            description="קבלת ניתוח הערכת שווי של נכס כולל מכירות דומות."
        )
        
        # Deal tools
        async def list_deals_tool_func(
            stage: Optional[str] = None,
            asset_id: Optional[int] = None,
        ) -> str:
            """List all deals, optionally filtered by stage or asset."""
            try:
                result = await list_deals(ctx, stage, None, asset_id)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    if isinstance(data, list):
                        return f"נמצאו {len(data)} עסקאות: {data}"
                    return str(data)
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        list_deals_tool = StructuredTool.from_function(
            func=wrap_async_tool(list_deals_tool_func),
            name="list_deals_tool",
            description="רשימת כל העסקאות, עם אפשרות סינון לפי שלב או נכס. מקבל עברית ואנגלית."
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
            description="יצירת עסקה חדשה עבור נכס."
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
            description="קבלת פרטי הצעה כולל מידע פיננסי."
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
            description="הערכת עלויות בנייה במטר רבוע."
        )
        
        async def get_cost_options_tool_func() -> str:
            """Get available options for cost estimation (regions, qualities, scopes)."""
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
            description="קבלת אפשרויות זמינות להערכת עלויות (אזורים, איכויות, היקפים)."
        )
        
        # Mortgage tools
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
                    return f"ניתוח משכנתא: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        analyze_mortgage_tool = StructuredTool.from_function(
            func=wrap_async_tool(analyze_mortgage_tool_func),
            name="analyze_mortgage_tool",
            description="ניתוח יכולת משכנתא ותרחישי תשלום."
        )
        
        # CRM tools
        async def list_contacts_tool_func() -> str:
            """List all CRM contacts."""
            try:
                result = await list_contacts(ctx)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    if isinstance(data, list):
                        return f"נמצאו {len(data)} אנשי קשר: {data}"
                    return str(data)
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        list_contacts_tool = StructuredTool.from_function(
            func=wrap_async_tool(list_contacts_tool_func),
            name="list_contacts_tool",
            description="רשימת כל אנשי הקשר ב-CRM."
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
            description="יצירת איש קשר חדש ב-CRM."
        )
        
        async def list_leads_tool_func(status: Optional[str] = None) -> str:
            """List all leads, optionally filtered by status."""
            try:
                result = await list_leads(ctx, status)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    if isinstance(data, list):
                        return f"נמצאו {len(data)} לידים: {data}"
                    return str(data)
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        list_leads_tool = StructuredTool.from_function(
            func=wrap_async_tool(list_leads_tool_func),
            name="list_leads_tool",
            description="רשימת כל הלידים, עם אפשרות סינון לפי סטטוס."
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
            description="יצירת ליד חדש המקשר איש קשר לנכס."
        )
        
        async def list_tasks_tool_func(status: Optional[str] = None) -> str:
            """List all CRM tasks, optionally filtered by status."""
            try:
                result = await list_tasks(ctx, None, None, status)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    if isinstance(data, list):
                        return f"נמצאו {len(data)} משימות: {data}"
                    return str(data)
                return str(result)
            except Exception as e:
                return f"שגיאה: {str(e)}"
        
        list_tasks_tool = StructuredTool.from_function(
            func=wrap_async_tool(list_tasks_tool_func),
            name="list_tasks_tool",
            description="רשימת כל המשימות ב-CRM, עם אפשרות סינון לפי סטטוס."
        )
        
        return [
            list_assets_tool,
            get_asset_tool,
            create_asset_tool,
            get_asset_transactions_tool,
            get_asset_appraisal_tool,
            list_deals_tool,
            create_deal_tool,
            get_offer_tool,
            estimate_build_cost_tool,
            get_cost_options_tool,
            analyze_mortgage_tool,
            list_contacts_tool,
            create_contact_tool,
            list_leads_tool,
            create_lead_tool,
            list_tasks_tool,
        ]
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Create the agent executor with system prompt."""
        system_prompt = """אתה עוזר AI מקצועי לסוכני נדל"ן. אתה עוזר למשתמשים עם:

1. **חיפוש וניתוח נכסים**: חיפוש נכסים, קבלת פרטי נכסים, צפייה בעסקאות, היתרים, תוכניות והערכות שווי
2. **ניהול עסקאות**: יצירה וניהול עסקאות, צפייה במשא ומתן והצעות
3. **חישובי הוצאות**: הערכת עלויות בנייה ואפשרויות עלויות
4. **ניתוח משכנתא**: ניתוח יכולת משכנתא ותרחישי תשלום
5. **ניהול CRM**: ניהול אנשי קשר, לידים ומשימות

כאשר משתמשים שואלים שאלות:
- השתמש בכלים המתאימים כדי לאחזר נתונים אמיתיים
- תן הסברים ברורים ומועילים
- ערוך מספרים ומחירים בצורה קריאה
- אם אין לך מספיק מידע, שאל שאלות הבהרה
- תמיד בדוק מזהה נכסים ומזהים אחרים לפני השימוש בהם

**שפה**: אתה עובד בעיקר בעברית. תגיב בעברית למשתמשים שמדברים עברית. 
תמיד השתמש בעברית כשאתה מתקשר עם המשתמש, אלא אם כן הוא מבקש במפורש שפה אחרת.
כשאתה מציג נתונים, ערוך אותם בצורה קריאה בעברית עם פורמט נכון למספרים ומחירים.

היה מקצועי, ידידותי ומקיף בתגובות שלך."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
        )
    
    async def chat(self, message: str, chat_history: Optional[List] = None, track_tool_calls: bool = True) -> Dict[str, Any]:
        """Chat with the agent.
        
        Args:
            message: User message
            chat_history: Optional chat history (list of messages)
            track_tool_calls: Whether to track tool calls
        
        Returns:
            Dictionary with 'response' and 'tool_calls' keys
        """
        history = chat_history or []
        
        if track_tool_calls:
            callback = ToolCallTracker()
            result = await self.agent_executor.ainvoke(
                {"input": message, "chat_history": history},
                config={"callbacks": [callback]}
            )
            tool_calls = callback.get_tool_calls()
            # Translate tool names to Hebrew
            for tool_call in tool_calls:
                tool_call["tool_hebrew"] = translate_tool_name(tool_call["tool"])
            return {
                "response": result["output"],
                "tool_calls": tool_calls
            }
        else:
            result = await self.agent_executor.ainvoke({
                "input": message,
                "chat_history": history,
            })
            return {
                "response": result["output"],
                "tool_calls": []
            }
    
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
        history = chat_history or []
        callback = StreamingCallbackHandler()
        
        # Run agent execution in background task
        async def run_agent():
            try:
                async for _ in self.agent_executor.astream(
                    {"input": message, "chat_history": history},
                    config={"callbacks": [callback]}
                ):
                    pass  # Just consume the stream
                callback.mark_finished()
            except Exception as e:
                try:
                    callback.chunk_queue.put_nowait({"type": "error", "error": str(e)})
                except Exception:
                    pass
                callback.mark_finished()
        
        # Start agent execution
        agent_task = asyncio.create_task(run_agent())
        
        try:
            # Stream events from callback queue
            max_wait_time = 300  # Maximum 5 minutes total wait time
            start_time = time.time()
            consecutive_timeouts = 0
            max_consecutive_timeouts = 50  # Stop after 5 seconds of no events (50 * 0.1s)
            
            while True:
                # Check if agent task is done
                if agent_task.done():
                    # Agent finished, drain remaining events
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
                    break
                
                # Get next event
                event = await callback.get_next_event(timeout=0.1)
                if event:
                    consecutive_timeouts = 0  # Reset timeout counter
                    if event.get("type") == "finished":
                        break
                    # Add Hebrew translation for tool events
                    if event.get("type") in ["tool_call_start", "tool_call_end", "tool_call_error"]:
                        event["tool_hebrew"] = translate_tool_name(event.get("tool", ""))
                    yield event
                else:
                    # No event received (timeout)
                    consecutive_timeouts += 1
                    if consecutive_timeouts >= max_consecutive_timeouts:
                        # Check if agent is still running
                        if agent_task.done():
                            break
                        # If agent is still running but no events, log warning and continue
                        logger.warning("No events received for %s seconds, but agent still running", 
                                     consecutive_timeouts * 0.1)
                        consecutive_timeouts = 0  # Reset to allow more time
            
            # Wait for agent to finish (with timeout)
            try:
                await asyncio.wait_for(agent_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Agent task did not finish within timeout")
                # Send error event
                yield {
                    "type": "error",
                    "error": "הסוכן לא סיים את המשימה בזמן. ייתכן שהתהליך תקוע."
                }
                return
            
            # Get final tool calls and translate
            tool_calls = callback.get_tool_calls()
            for tool_call in tool_calls:
                tool_call["tool_hebrew"] = translate_tool_name(tool_call["tool"])
            
            # Send completion event
            yield {
                "type": "complete",
                "response": callback.get_complete_response(),
                "tool_calls": tool_calls
            }
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
        """
        import asyncio
        result = asyncio.run(self.chat(message, track_tool_calls=False))
        return result.get("response", "") if isinstance(result, dict) else result


def main():
    """CLI interface for the Real Estate Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Real Estate Agent CLI")
    parser.add_argument(
        "--provider",
        choices=["openai", "gemini", "groq"],
        default="openai",
        help="LLM provider to use",
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
                print(f"\nAgent: {response}\n")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
