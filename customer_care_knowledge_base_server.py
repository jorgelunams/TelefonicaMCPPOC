# DO NOT print or log to stdout! Only MCP protocol output is allowed.
# For debugging, print to stderr like this:
# import sys; print('Debug info', file=sys.stderr)

from mcp.server.fastmcp import FastMCP
import json

# Instantiate an MCP server instance with a name
mcp = FastMCP("KnwoledgeBaseServer")

# Load customers from a .txt file (JSON with signal quality details)
def load_customers_dict(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        customers_dict = {}
        if "datos" in data and "signalQualityIssuesDetail" in data["datos"]:
            for entry in data["datos"]["signalQualityIssuesDetail"].get("detailSignalPlane", []):
                if "imsi" in entry:
                    customers_dict[str(entry["imsi"])] = entry
    return customers_dict

# Load the customers dictionary at startup
CUSTOMERS_FILE = "customers.txt"
CUSTOMERS_DICT = load_customers_dict(CUSTOMERS_FILE)
 
@mcp.tool()
def get_customer_by_imsi(imsi: str) -> dict:
    """Retrieve customer information by IMSI."""
    customer = CUSTOMERS_DICT.get(str(imsi))
    if customer:
        return customer
    else:
        return {"error": f"Customer with IMSI {imsi} not found."}
    

if __name__ == "__main__":
    # This server will be launched automatically by the MCP stdio agent
    # You don't need to run this file directly - it will be spawned as a subprocess
    mcp.run(transport="stdio")
 