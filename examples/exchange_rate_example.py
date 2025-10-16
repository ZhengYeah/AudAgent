import os
import time
import asyncio
from typing import Annotated, Literal

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from audagent.core import initialize

claude_config_list = [{
    "model": "claude-3.0",
    "api_key": os.getenv("CLAUDE_API_KEY"),
    "api_type": "anthropic"
}]

CurrencySybmol = Literal["USD", "EUR"]

def exchange_rate(from_currency: CurrencySybmol,to_currency: CurrencySybmol) -> float:
    if from_currency == to_currency:
        return 1.0
    elif from_currency == "USD" and to_currency == "EUR":
        return 0.91
    elif from_currency == "EUR" and to_currency == "USD":
        return 1.1
    else:
        raise ValueError("Unsupported currency pair")

model_client = OpenAIChatCompletionClient(
        model="gpt-4o",
        # api_key = "your_openai_api_key"
)

chatbot = AssistantAgent(
    name="chatbot",
    system_message="For currency exchange, only use the functions provided. Respond TERMINATE when the task is complete.",
    model_client=model_client,
    tools=[exchange_rate],
)

if __name__ == "__main__":
    initialize()
    chat_result = chatbot.run(task="What is 100 USD in EUR and what is 100 EUR in USD?")
    print(chat_result)
    time.sleep(5)  # wait for all async logging to complete
