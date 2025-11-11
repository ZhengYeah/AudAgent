"""
See LangChain MCP Adapters for more details: https://github.com/langchain-ai/langchain-mcp-adapters
It wraps MCP tools compatible with LangChain and LangGraph.
"""

import logging
import sys
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

PRIVACY_PATH = (Path(__file__).resolve().parent / ".." / "pri_policy" / "anthropic" / "simplified_privacy_model.json").resolve()
sys.path.insert(0, str(Path(__file__).parent.parent / "audagent"))
load_dotenv()
model = ChatOpenAI(model="gpt-4.1")

async def main():
    # --- Initialize Audagent with privacy policy ---
    os.environ["AUDAGENT_PRIVACY_POLICIES"] = str(PRIVACY_PATH)
    import audagent
    # --- End of Audagent initialization ---

    from audagent.utils.custom_logging_formatter import setup_logging
    setup_logging(logging.DEBUG)
    logging.getLogger()

    mcp_client = MultiServerMCPClient(
        {
            "weather": {
                "url": "http://localhost:8001/sse",
                "transport": "sse",
            }
        }
    )
    tools = await mcp_client.get_tools()
    agent = create_agent(model, tools)
    response = await agent.ainvoke({"messages": "What's the weather like in New York City today?"})
    print(response)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())