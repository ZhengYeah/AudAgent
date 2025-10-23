import asyncio
import logging
import os

import aiohttp
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.anthropic import AnthropicChatCompletionClient
from audagent.utils.custom_logging_formatter import setup_logging

"""
Import Audagent to monitor LLM interactions
"""
import audagent

setup_logging(logging.DEBUG)
logging.getLogger()
load_dotenv()

async def exchange_rate_tool(from_currency: str, to_currency: str, amount: float = 1.0) -> dict:
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

async def main():
    anthropic_client = AnthropicChatCompletionClient(
        model="claude-sonnet-4-5-20250929", # claude-haiku does not support tools
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    agent = AssistantAgent(
        name="currency_agent",
        model_client=anthropic_client,
        system_message=(
            "You are a currency exchange assistant. Users will ask things like "
            "'Convert 150 USD to JPY', 'What is the rate for GBP to EUR?' "
            "You must call the tool `exchange_rate_tool(from_currency, to_currency, amount)` and then "
            "report the result in human‐friendly text. "
        ),
        tools=[exchange_rate_tool]
    )

    print("Currency Agent ready — type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        user_msg = TextMessage(content=user_input, source="user")
        result = await agent.run(task=user_msg)
        print("Agent:", result.messages[-1].content)


if __name__ == "__main__":
    asyncio.run(main())
