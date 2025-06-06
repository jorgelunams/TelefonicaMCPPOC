from mcp.server.fastmcp import FastMCP
import json

# Instantiate an MCP server instance with a name
mcp = FastMCP("WeatherServer")

# Load customers from a .txt file (JSON array of customer objects)
def load_customers_dict(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        customers_list = json.load(f)
    # Create a dictionary with customer_id as key
    return {c['customer_id']: c for c in customers_list}

# Load the customers dictionary at startup
CUSTOMERS_FILE = "customers.txt"
CUSTOMERS_DICT = load_customers_dict(CUSTOMERS_FILE)

@mcp.tool()
def get_weather(city: str) -> str:
    """Return the current weather for a given city. For demo, only 'x boston' is supported."""
    if city.lower() == "boston":
        return "The current temperature in x Boston is 68°F."
    else:
        return f"Sorry, I only have weather data for x Boston."

@mcp.tool()
def get_customer_by_id(customer_id: str) -> dict:
    """Retrieve customer information by customer ID."""
    customer = CUSTOMERS_DICT.get(customer_id)
    if customer:
        return customer
    else:
        return {"error": f"Customer with ID {customer_id} not found."}

@mcp.tool()
def get_all_customers() -> list:
    """Devuelve una lista de todos los clientes."""
    return list(CUSTOMERS_DICT.values())

@mcp.tool()
def find_customers_by_name(partial_name: str) -> list:
    """Busca clientes cuyo nombre contenga el texto dado (búsqueda insensible a mayúsculas/minúsculas)."""
    partial = partial_name.lower()
    return [c for c in CUSTOMERS_DICT.values() if partial in c.get('nombre', '').lower()]

if __name__ == "__main__":
    # This server will be launched automatically by the MCP stdio agent
    # You don't need to run this file directly - it will be spawned as a subprocess
    mcp.run(transport="stdio")
