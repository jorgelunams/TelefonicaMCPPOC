from mcp.server.fastmcp import FastMCP  
import requests  
from bs4 import BeautifulSoup  
  
# Instanciar una instancia del servidor MCP con un nombre  
mcp = FastMCP("TelefonicaDevices")  
  
@mcp.tool()  
def extract_dataFrom_URL(url): 
    """Return all data from a url on the web.."""
    response = requests.get(url)  
    if response.status_code == 200:  # Check if the request was successful  
    # Parse the HTML content with BeautifulSoup  
        soup = BeautifulSoup(response.text, 'html.parser')  
        
        # Extract all the text from the page  
        all_text = soup.get_text(separator="\n")  # Use newline as separator for better readability  
        
        # Store extracted lines in a list  
        extracted_lines = []  
        for line in all_text.split("\n"):  
            cleaned_line = line.strip()  # Remove extra spaces  
            if cleaned_line:  # Only include non-empty lines  
                extracted_lines.append(cleaned_line)  
        
        # Remove unused json_output variable
        return extracted_lines
    else:
        # Always return a JSON-serializable error object
        return {"error": f"Failed to fetch the webpage. Status code: {response.status_code}"}

if __name__ == "__main__":
    # This server will be launched automatically by the MCP stdio agent
    # You don't need to run this file directly - it will be spawned as a subprocess
    mcp.run(transport="stdio")
