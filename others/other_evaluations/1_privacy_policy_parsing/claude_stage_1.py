import asyncio
import os
from pathlib import Path
import sys
import json

from dotenv import load_dotenv

# Add path of audagent to sys.path (not necessary if you have installed audagent)
path_audagent = (Path(__file__).resolve().parent / "..").resolve()
sys.path.insert(0, str(path_audagent))

ANTHROPIC_POLICY = (Path(__file__).resolve().parent / ".." / ".." / ".." / "privacy_policy" / "anthropic" / "simplified_privacy_model.json").resolve()

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.anthropic import AnthropicChatCompletionClient

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".." / ".." / ".." / "examples" / ".env", override=True)

async def main():
    anthropic_client = AnthropicChatCompletionClient(
        model="claude-sonnet-4-5-20250929", # claude-haiku does not support tools
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    agent = AssistantAgent(
        name="currency_agent",
        model_client=anthropic_client,
        system_message=(
            " I will give you a privacy policy written in natural language. Your task is to analyze this privacy policy and convert it into a structured formal representation. "
            " The formal representation should capture each collected data type, along with its collection method, usage purpose, disclosure to which third parties (if any), and retention policy. "
            " More specifically, please use the following schema: "
            " ``` "
            " { "
            " \"types_of_data_collected\": one data type collected, e.g. \"personal identifiable information\", \"usage data\". "
            " \"methods_of_collection\": the methods used to collect this data, e.g. \"directly from users\" or \"indirectly through cookies\". "
            " \"data_usage\": purposes for which this data is used, e.g. \"improving services\", \"personalization\", \"marketing\". "
            " \"third_party_disclosure\": third parties with whom the data is shared, e.g. \"service providers\", \"advertisers\", \"not disclosed to third parties\". "
            " \"retention_period\": how long data is retained, e.g. \"30 days\", \"until user deletes it\", "
            " } "
            " ``` "      
            " Each data type should be represented as a separate object in a list. "
            " If certain information is not specified in the privacy policy, please indicate it as \"not specified\". "
            " Please provide the formal representation in JSON format. Here is the privacy policy to analyze: "
        ),
        tools=[]
    )

    with open(ANTHROPIC_POLICY, "r") as f:
        policy_content = f.read()

    result = await agent.run(task=TextMessage(content=policy_content, source="user"), cancellation_token=CancellationToken())
    result_text = result.messages[-1].content

    # Sanitize the output JSON: remove any beginning or trailing text that is not part of the JSON, and ensure it can be parsed as JSON
    try:
        json_start = result_text.find("[")
        json_end = result_text.rfind("]") + 1
        json_str = result_text[json_start:json_end]
        parsed_json = json.loads(json_str)
        file_path = Path(__file__).resolve().parent / "claude_parsed_policy.json"
        with open(file_path, "w") as f:
            json.dump(parsed_json, f, indent=2)
        print("Parsed JSON output has been saved to 'claude_parsed_policy.json'.")
        # Print the number of data types collected according to the parsed JSON
        print(f"\033[33mNumber of data types collected: {len(parsed_json)}\033[0m")
    except json.JSONDecodeError:
        print("Failed to parse the output as JSON. Please check the content of 'claude_parsed_policy.json' for details.")

if __name__ == "__main__":
    asyncio.run(main())