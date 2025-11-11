# Real Estate Agent - LangChain Integration

A conversational AI agent built with LangChain that helps with real estate tasks using the MCP server tools.

## Overview

The Real Estate Agent is an AI assistant that can:
- Search and analyze properties
- Manage deals and negotiations
- Calculate construction costs
- Analyze mortgage affordability
- Manage CRM contacts, leads, and tasks

## Installation

```bash
pip install -r backend-django/requirements-langchain.txt
```

## Configuration

Set environment variables:

```bash
# LLM Provider (choose one)
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"  # or GOOGLE_API_KEY
export GROQ_API_KEY="your-groq-key"

# AWS Bedrock (alternative LLM provider)
export BEDROCK_AWS_REGION="us-east-1"  # Required
export BEDROCK_AWS_ACCESS_KEY_ID="your-access-key"  # Optional if using IAM role
export BEDROCK_AWS_SECRET_ACCESS_KEY="your-secret-key"  # Optional if using IAM role
export BEDROCK_MODEL_ID="anthropic.claude-3-sonnet-20240229-v1:0"  # Optional, defaults to Claude 3 Sonnet
# Alternative: Use standard AWS credentials
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# Real Estate API
export REALESTATE_API_URL="http://127.0.0.1:8000/api"
export REALESTATE_API_TOKEN="your-api-token"  # Optional
```

## Usage

### CLI Interface

```bash
# Interactive mode
python backend-django/agent/real_estate_agent.py --provider openai
python backend-django/agent/real_estate_agent.py --provider bedrock

# Single query
python backend-django/agent/real_estate_agent.py --provider openai "List all assets in Tel Aviv"
python backend-django/agent/real_estate_agent.py --provider bedrock "List all assets in Tel Aviv"
```

### Python API

```python
from backend_django.agent.real_estate_agent import RealEstateAgent

# Initialize agent
agent = RealEstateAgent(
    llm_provider="openai",
    api_token="your-token",
    temperature=0.3
)

# Chat with agent
response = await agent.chat("Find properties in Tel Aviv under 5 million")
print(response)
```

## Example Conversations

### Property Search
```
You: Find apartments in Tel Aviv under 4 million NIS
Agent: [Searches assets and returns results]

You: Tell me more about asset ID 123
Agent: [Gets asset details, transactions, permits, etc.]
```

### Deal Management
```
You: Create a deal for asset 123
Agent: [Creates deal and confirms]

You: What offers are available for deal 456?
Agent: [Lists offers with financial details]
```

### Mortgage Analysis
```
You: Can I afford a 4.5M property with 900K savings?
Agent: [Analyzes mortgage affordability and provides recommendations]
```

### Expense Calculation
```
You: How much would it cost to build 100 sqm in Tel Aviv?
Agent: [Estimates construction costs with breakdown]
```

### CRM Management
```
You: Create a contact named John Doe with email john@example.com
Agent: [Creates contact]

You: List all active leads
Agent: [Lists leads with status and details]
```

## Available Tools

The agent has access to 16+ tools:

**Assets:**
- `list_assets_tool` - Search properties
- `get_asset_tool` - Get property details
- `create_asset_tool` - Create new property
- `get_asset_transactions_tool` - View transaction history
- `get_asset_appraisal_tool` - Get property appraisal

**Deals:**
- `list_deals_tool` - List deals
- `create_deal_tool` - Create deal
- `get_offer_tool` - View offer details

**Expenses:**
- `estimate_build_cost_tool` - Estimate construction costs
- `get_cost_options_tool` - Get cost estimation options

**Mortgage:**
- `analyze_mortgage_tool` - Analyze mortgage affordability

**CRM:**
- `list_contacts_tool` - List contacts
- `create_contact_tool` - Create contact
- `list_leads_tool` - List leads
- `create_lead_tool` - Create lead
- `list_tasks_tool` - List tasks

## Architecture

```
┌─────────────────┐
│  User Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LangChain Agent │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  MCP Tools      │──────▶│  API Server  │
└─────────────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│  LLM Response   │
└─────────────────┘
```

## Customization

### Change LLM Provider

```python
agent = RealEstateAgent(llm_provider="gemini")  # or "groq", "openai", "bedrock"
```

### AWS Bedrock Configuration

AWS Bedrock uses AWS credentials instead of API keys. You can configure credentials in several ways:

1. **Environment variables** (recommended for development):
   ```bash
   export BEDROCK_AWS_REGION="us-east-1"
   export BEDROCK_AWS_ACCESS_KEY_ID="your-access-key"
   export BEDROCK_AWS_SECRET_ACCESS_KEY="your-secret-key"
   ```

2. **AWS credentials file** (`~/.aws/credentials`):
   ```ini
   [default]
   aws_access_key_id = your-access-key
   aws_secret_access_key = your-secret-key
   ```

3. **IAM role** (recommended for production on EC2/Lambda):
   - No credentials needed, uses instance role automatically

**Available Bedrock Models:**
- `anthropic.claude-3-sonnet-20240229-v1:0` (default)
- `anthropic.claude-3-haiku-20240307-v1:0`
- `anthropic.claude-3-opus-20240229-v1:0`
- `meta.llama2-70b-chat-v1`
- `meta.llama3-8b-instruct-v1:0`
- And more - see [AWS Bedrock Model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html)

### Adjust Temperature

```python
agent = RealEstateAgent(temperature=0.7)  # More creative
```

### Add Custom Tools

Extend the `_create_tools()` method to add more MCP tools.

## Error Handling

The agent handles:
- API errors gracefully
- Invalid tool calls
- Parsing errors
- Rate limiting

## Development

To extend the agent:

1. Add new tools in `_create_tools()`
2. Update system prompt in `_create_agent_executor()`
3. Test with various queries

## Troubleshooting

**"No API key found"**
- Set the appropriate API key environment variable
- For Bedrock: Set `BEDROCK_AWS_REGION` and ensure AWS credentials are configured

**"Connection refused"**
- Ensure the API server is running
- Check `REALESTATE_API_URL` setting

**"Tool execution failed"**
- Verify API token if required
- Check API server logs

