import logging

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.DEBUG)

mcp = FastMCP("Echo", port=8001)


@mcp.resource("echo://{message}")
def echo_resource(message: str) -> str:
    """Echo a message as a resource"""
    return f"Resource echo: {message}"

@mcp.tool()
def get_weather_tool(city: str, for_date: str) -> dict[str, str]:
    """Returns the weather for a city and a given date"""
    return {"city": city, "weather": "sunny"}

@mcp.tool()
def get_current_date() -> dict[str, str]:
    """Returns the current date"""
    return {"date": "2023-10-01"}

@mcp.prompt()
def echo_prompt(message: str) -> str:
    """Create an echo prompt"""
    return f"Please process this message: {message}"

mcp.run(transport="sse")