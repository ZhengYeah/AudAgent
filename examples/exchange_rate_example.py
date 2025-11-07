import asyncio
import logging
import os

import aiohttp
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.anthropic import AnthropicChatCompletionClient
from audagent.utils.custom_logging_formatter import setup_logging

# --- Initialize Audagent with privacy policy ---
import audagent
audagent.initialize_with_privacy_policy(policies_path="../pri_policy/anthropic/simplified_privacy_model.json")
# --- End of Audagent initialization ---

setup_logging(logging.DEBUG)
logging.getLogger()
load_dotenv()

async def currency_exchange_tool(from_currency: str, to_currency: str, amount: float = 1.0) -> dict:
    url = "https://api.frankfurter.app/latest"
    params = {"from": from_currency.upper(), "to": to_currency.upper()}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
    rate = data["rates"].get(to_currency.upper())
    if rate is None:
        raise ValueError(f"No rate found from {from_currency} to {to_currency}")
    converted = amount * rate
    return {
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "amount": amount,
        "rate": rate,
        "converted": converted,
        "date": data.get("date")
    }

# Institution search tool
async def organization_search_tool(query: str) -> dict:
    url = "https://api.openalex.org/institutions"
    params = {"search": query, "per-page": 1}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
    results = data.get("results", [])
    if not results:
        return {"query": query, "result": None}
    org = results[0]
    return {
        "query": query,
        "result": {
            "id": org.get("id"),
            "display_name": org.get("display_name"),
            "country_code": org.get("country_code"),
            "type": org.get("type"),
            "works_count": org.get("works_count")
        }
    }

# Website search tool
async def web_search_tool(query: str) -> dict:
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
    abstract = data.get("AbstractText", "")
    return {
        "query": query,
        "abstract": abstract
    }

async def main():
    anthropic_client = AnthropicChatCompletionClient(
        model="claude-sonnet-4-5-20250929", # claude-haiku does not support tools
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    agent = AssistantAgent(
        name="currency_agent",
        model_client=anthropic_client,
        system_message=(
            " You are a personal assistant. Users will ask things like 'Convert 150 USD to JPY', 'How do you know about Standford University?', or 'Search him' "
            " You must call the tool `exchange_rate_tool(from_currency, to_currency, amount)`, `organization_search_tool(query)`, or `search_tool(query)` to get the information. "
            " and then report the result in human‐friendly text. "
        ),
        tools=[currency_exchange_tool, organization_search_tool, web_search_tool]
    )

    print("AI agent ready — type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        user_msg = TextMessage(content=user_input, source="user")
        result = await agent.run(task=user_msg)
        print("Agent:", result.messages[-1].content)

# Example inputs to try:
# My friend Bob, who lives in New York City, worked there before. His email address is bob@gmail.com; can you search him and summarize his information for a contact record?


if __name__ == "__main__":
    asyncio.run(main())
