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
from typing import List, Optional

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# LangChain imports
from langchain_core.tools import BaseTool, StructuredTool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# Import agent components - try multiple import paths for compatibility
try:
    # Standard LangChain 0.3+ imports
    from langchain.agents import AgentExecutor, create_openai_tools_agent
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
except ImportError:
    try:
        # Try alternative import structure
        from langchain.agents.agent import AgentExecutor
        from langchain.agents import create_openai_tools_agent
        from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    except ImportError:
        try:
            # Try with langchain_core prompts
            from langchain.agents import AgentExecutor, create_openai_tools_agent
            from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        except ImportError:
            # Last resort: check if modules exist and import manually
            import langchain.agents as agents_mod
            import langchain.prompts as prompts_mod
            
            AgentExecutor = getattr(agents_mod, 'AgentExecutor', None)
            create_openai_tools_agent = getattr(agents_mod, 'create_openai_tools_agent', None)
            ChatPromptTemplate = getattr(prompts_mod, 'ChatPromptTemplate', None)
            MessagesPlaceholder = getattr(prompts_mod, 'MessagesPlaceholder', None)
            
            if not AgentExecutor or not create_openai_tools_agent:
                # Try langchain_core for prompts
                try:
                    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
                except ImportError:
                    pass
            
            if not all([AgentExecutor, create_openai_tools_agent, ChatPromptTemplate, MessagesPlaceholder]):
                raise ImportError(
                    "Could not import required LangChain components.\n"
                    "Please install: pip install langchain>=0.3.0 langchain-openai langchain-core\n"
                    "Or run: pip install -r backend-django/requirements-langchain.txt"
                )

# Import MCP server functions dynamically
try:
    mcp_server_path = os.path.join(os.path.dirname(__file__), "..", "mcp", "server.py")
    spec = importlib.util.spec_from_file_location("mcp_server", mcp_server_path)
    mcp_server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mcp_server)
    
    # Import functions from MCP server
    list_assets = mcp_server.list_assets
    get_asset = mcp_server.get_asset
    create_asset = mcp_server.create_asset
    get_asset_transactions = mcp_server.get_asset_transactions
    get_asset_appraisal = mcp_server.get_asset_appraisal
    list_deals = mcp_server.list_deals
    create_deal = mcp_server.create_deal
    get_offer = mcp_server.get_offer
    estimate_build_cost = mcp_server.estimate_build_cost
    get_cost_options = mcp_server.get_cost_options
    analyze_mortgage = mcp_server.analyze_mortgage
    list_contacts = mcp_server.list_contacts
    create_contact = mcp_server.create_contact
    list_leads = mcp_server.list_leads
    create_lead = mcp_server.create_lead
    list_tasks = mcp_server.list_tasks
except Exception as e:
    # MCP server not available - create stub functions
    import warnings
    warnings.warn(f"MCP server not available: {e}. Agent will have limited functionality.")
    
    async def _stub_func(*args, **kwargs):
        return {"success": False, "error": "MCP server not available. Please install fastmcp and mcp packages."}
    
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
        
        # Wrap MCP functions as LangChain tools
        # Assets tools
        async def list_assets_tool_func(
            city: Optional[str] = None,
            max_price: Optional[int] = None,
            min_price: Optional[int] = None,
            rooms: Optional[int] = None,
            page: Optional[int] = None,
        ) -> str:
            """List all assets with optional filtering. Use this to search for properties."""
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
            func=list_assets_tool_func,
            name="list_assets_tool",
            description="חיפוש נכסים עם אפשרויות סינון. השתמש בכלי זה כדי לחפש נכסים. מקבל עברית ואנגלית."
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
            func=get_asset_tool_func,
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
            func=create_asset_tool_func,
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
            func=get_asset_transactions_tool_func,
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
            func=get_asset_appraisal_tool_func,
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
            func=list_deals_tool_func,
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
            func=create_deal_tool_func,
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
            func=get_offer_tool_func,
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
            func=estimate_build_cost_tool_func,
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
            func=get_cost_options_tool_func,
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
            func=analyze_mortgage_tool_func,
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
            func=list_contacts_tool_func,
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
            func=create_contact_tool_func,
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
            func=list_leads_tool_func,
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
            func=create_lead_tool_func,
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
            func=list_tasks_tool_func,
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
    
    async def chat(self, message: str, chat_history: Optional[List] = None) -> str:
        """Chat with the agent.
        
        Args:
            message: User message
            chat_history: Optional chat history (list of messages)
        
        Returns:
            Agent response
        """
        history = chat_history or []
        
        result = await self.agent_executor.ainvoke({
            "input": message,
            "chat_history": history,
        })
        
        return result["output"]
    
    def run(self, message: str) -> str:
        """Synchronous version of chat (for CLI usage).
        
        Args:
            message: User message
        
        Returns:
            Agent response
        """
        import asyncio
        return asyncio.run(self.chat(message))


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
