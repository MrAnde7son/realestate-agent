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
from langchain_core.tools import BaseTool, tool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# Import MCP server functions dynamically
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
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            return ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=temperature,
                api_key=api_key,
            )
        elif provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required")
            return ChatGoogleGenerativeAI(
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                temperature=temperature,
                google_api_key=api_key,
            )
        elif provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
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
        from langchain_core.tools import tool
        
        # Create a context object for MCP tools
        class MockContext:
            def info(self, msg: str):
                pass
        
        ctx = MockContext()
        
        # Wrap MCP functions as LangChain tools
        # Assets tools
        @tool
        async def list_assets_tool(
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
                        return f"Found {len(assets)} assets:\n" + "\n".join([
                            f"- Asset {a.get('id')}: {a.get('address', 'N/A')} - {a.get('price', 'N/A')} NIS"
                            for a in assets[:10]
                        ])
                    return str(data)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        async def get_asset_tool(asset_id: int, include_documents: bool = False) -> str:
            """Get detailed information for a specific asset by ID."""
            try:
                result = await get_asset(ctx, asset_id, include_documents)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    return f"Asset {asset_id}:\n" + str(data)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        async def create_asset_tool(
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
                    return f"Asset created successfully: {data}"
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        async def get_asset_transactions_tool(asset_id: int) -> str:
            """Get transaction history for an asset."""
            try:
                result = await get_asset_transactions(ctx, asset_id)
                if isinstance(result, dict) and result.get("success"):
                    return f"Transactions for asset {asset_id}: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        async def get_asset_appraisal_tool(asset_id: int) -> str:
            """Get appraisal analysis for an asset including comparable sales."""
            try:
                result = await get_asset_appraisal(ctx, asset_id)
                if isinstance(result, dict) and result.get("success"):
                    return f"Appraisal for asset {asset_id}: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Deal tools
        @tool
        async def list_deals_tool(
            stage: Optional[str] = None,
            asset_id: Optional[int] = None,
        ) -> str:
            """List all deals, optionally filtered by stage or asset."""
            try:
                result = await list_deals(ctx, stage, None, asset_id)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    if isinstance(data, list):
                        return f"Found {len(data)} deals: {data}"
                    return str(data)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        async def create_deal_tool(
            asset_id: int,
            stage: Optional[str] = "discovery",
        ) -> str:
            """Create a new deal for an asset."""
            try:
                result = await create_deal(ctx, asset_id, stage)
                if isinstance(result, dict) and result.get("success"):
                    return f"Deal created: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        async def get_offer_tool(offer_id: int) -> str:
            """Get offer details including financial information."""
            try:
                result = await get_offer(ctx, offer_id)
                if isinstance(result, dict) and result.get("success"):
                    return f"Offer {offer_id}: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Expense calculation tools
        @tool
        async def estimate_build_cost_tool(
            area_m2: float,
            scope: Optional[List[str]] = None,
            region: Optional[str] = None,
            quality: Optional[str] = None,
        ) -> str:
            """Estimate building construction costs in square meters."""
            try:
                result = await estimate_build_cost(ctx, area_m2, scope, region, quality)
                if isinstance(result, dict) and result.get("success"):
                    return f"Cost estimate: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        async def get_cost_options_tool() -> str:
            """Get available options for cost estimation (regions, qualities, scopes)."""
            try:
                result = await get_cost_options(ctx)
                if isinstance(result, dict) and result.get("success"):
                    return f"Cost options: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Mortgage tools
        @tool
        async def analyze_mortgage_tool(
            property_price: float,
            savings_total: float,
            annual_rate_pct: Optional[float] = None,
            term_years: Optional[int] = None,
        ) -> str:
            """Analyze mortgage affordability and payment scenarios."""
            try:
                result = await analyze_mortgage(ctx, property_price, savings_total, annual_rate_pct, term_years)
                if isinstance(result, dict) and result.get("success"):
                    return f"Mortgage analysis: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        # CRM tools
        @tool
        async def list_contacts_tool() -> str:
            """List all CRM contacts."""
            try:
                result = await list_contacts(ctx)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    if isinstance(data, list):
                        return f"Found {len(data)} contacts: {data}"
                    return str(data)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        async def create_contact_tool(
            name: str,
            email: Optional[str] = None,
            phone: Optional[str] = None,
        ) -> str:
            """Create a new CRM contact."""
            try:
                result = await create_contact(ctx, name, email, phone)
                if isinstance(result, dict) and result.get("success"):
                    return f"Contact created: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        async def list_leads_tool(status: Optional[str] = None) -> str:
            """List all leads, optionally filtered by status."""
            try:
                result = await list_leads(ctx, status)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    if isinstance(data, list):
                        return f"Found {len(data)} leads: {data}"
                    return str(data)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        async def create_lead_tool(contact_id: int, asset_id: int) -> str:
            """Create a new lead linking a contact to an asset."""
            try:
                result = await create_lead(ctx, contact_id, asset_id)
                if isinstance(result, dict) and result.get("success"):
                    return f"Lead created: {result.get('data', {})}"
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        async def list_tasks_tool(status: Optional[str] = None) -> str:
            """List all CRM tasks, optionally filtered by status."""
            try:
                result = await list_tasks(ctx, None, None, status)
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    if isinstance(data, list):
                        return f"Found {len(data)} tasks: {data}"
                    return str(data)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
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
        system_prompt = """You are a helpful real estate agent AI assistant. You help users with:

1. **Property Search & Analysis**: Search for properties, get property details, view transactions, permits, plans, and appraisals
2. **Deal Management**: Create and manage deals, view negotiations and offers
3. **Expense Calculations**: Estimate construction costs and get cost options
4. **Mortgage Analysis**: Analyze mortgage affordability and payment scenarios
5. **CRM Management**: Manage contacts, leads, and tasks

When users ask questions:
- Use the appropriate tools to fetch real data
- Provide clear, helpful explanations
- Format numbers and prices in a readable way
- If you don't have enough information, ask clarifying questions
- Always verify asset IDs and other identifiers before using them

Be professional, friendly, and thorough in your responses."""

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

