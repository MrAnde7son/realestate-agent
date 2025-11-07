#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the Real Estate Agent
"""

import asyncio
import os
from backend_django.agent.real_estate_agent import RealEstateAgent


async def main():
    """Example conversation with the Real Estate Agent."""
    
    # Initialize agent
    agent = RealEstateAgent(
        llm_provider="openai",  # or "gemini", "groq"
        temperature=0.3,
    )
    
    # Example queries
    queries = [
        "List all assets in Tel Aviv",
        "What properties are available under 4 million NIS?",
        "Can I afford a 4.5M property with 900K savings?",
        "How much would it cost to build 100 sqm in Tel Aviv?",
        "List all my contacts",
    ]
    
    print("Real Estate Agent - Example Conversation\n")
    print("=" * 50)
    
    for query in queries:
        print(f"\nUser: {query}")
        print("-" * 50)
        try:
            response = await agent.chat(query)
            print(f"Agent: {response}")
        except Exception as e:
            print(f"Error: {e}")
        print("=" * 50)


if __name__ == "__main__":
    # Make sure API keys are set
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GEMINI_API_KEY") and not os.getenv("GROQ_API_KEY"):
        print("Error: Please set OPENAI_API_KEY, GEMINI_API_KEY, or GROQ_API_KEY")
        exit(1)
    
    asyncio.run(main())

