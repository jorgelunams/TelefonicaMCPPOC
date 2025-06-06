from mcp.server.fastmcp import FastMCP

# Instantiate an MCP server instance with a name
mcp = FastMCP("WeatherServer")

@mcp.tool()
def get_weather(city: str) -> str:
    """Return the current weather for a given city. For demo, only 'x boston' is supported."""
    if city.lower() == "boston":
        return "The current temperature in x Boston is 68°F."
    else:
        return f"Sorry, I only have weather data for x Boston."

if __name__ == "__main__":
    # This server will be launched automatically by the MCP stdio agent
    # You don't need to run this file directly - it will be spawned as a subprocess
    mcp.run(transport="stdio")
