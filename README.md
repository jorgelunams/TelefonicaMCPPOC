# Telefónica Customer Care Agent with MCP Integration

A sophisticated customer care system built with semantic kernel agents and Model Context Protocol (MCP) integration for Telefónica Chile.

## Features

- **Multi-Agent System**: Specialized agents for different customer inquiries
  - `SentimentAnalysisAgent`: Analyzes emotions and customer satisfaction
  - `RatePlansExpertAgent`: Handles rate plans, pricing, and service costs
  - `AgentCare`: General queries and service issues (eSIM compatibility, device info)

- **MCP Integration**: Uses Model Context Protocol for external data sources
  - Internet data extraction for device compatibility
  - Customer knowledge base integration

- **Azure Functions**: Deployed as serverless functions for scalability
- **IMSI Integration**: Customer identification via IMSI for personalized service

## Architecture

```
Customer Request → Azure Function → Manager Agent → Specialized Agent → Response
                                  ↓
                            MCP Plugins (Internet + Knowledge Base)
```

## API Endpoints

### Customer Care Function
```
GET /api/customer-care/{imsi}/{pregunta}
```

**Parameters:**
- `imsi`: Customer IMSI identifier
- `pregunta`: Customer question (URL encoded)

**Example:**
```
GET /api/customer-care/730029988243961/¿puede%20mi%20celular%20usar%20eSIM?
```

## Setup & Installation

### Prerequisites
- Python 3.12+
- Azure Functions Core Tools
- OpenAI API access (Azure OpenAI)

### Environment Variables
Create a `.env` file with:
```
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment
AZURE_OPENAI_KEY=your_api_key
```

### Installation
```bash
# Clone the repository
git clone https://github.com/jorgelunams/TelefonicaMCPPOC.git
cd TelefonicaMCPPOC

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Running Locally
```bash
# Start Azure Functions locally
func start

# Or run the agent directly
python customer_care_agent_mgr.py
```

## File Structure

- `function_app.py`: Azure Function entry point
- `customer_care_agent_mgr.py`: Main agent orchestration logic
- `customer_care_knowledge_base_server.py`: MCP knowledge base server
- `mcp_internet_extarct_server.py`: MCP internet data extraction server
- `customers.txt`: Sample customer data
- `requirements.txt`: Python dependencies

## Usage Examples

### Direct Agent Usage
```python
from customer_care_agent_mgr import process_question

# Process question with IMSI
answer = await process_question(
    question="¿puede mi celular usar eSIM?",
    imsi="730029988243961"
)
```

### HTTP API Usage
```bash
curl "http://localhost:7071/api/customer-care/730029988243961/¿puede%20mi%20celular%20usar%20eSIM?"
```

## Agent Capabilities

### eSIM Compatibility Check
- Extracts device compatibility data from Apple and Samsung websites
- Provides definitive yes/no answers with source information
- Supports iPhone and Samsung Galaxy devices

### Customer Information
- Retrieves customer data using IMSI
- Provides account status and service information
- Handles customer ID requests when needed

### Rate Plans & Pricing
- Detailed information about Telefónica Chile plans
- Price comparisons and recommendations
- Plan change processes and costs

## Development

### Adding New Agents
1. Create agent class in `customer_care_agent_mgr.py`
2. Add to the `get_agents()` function
3. Update `ManagerAgent` instructions

### MCP Server Development
- Extend existing MCP servers for new data sources
- Follow MCP protocol specifications
- Test with semantic kernel integration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is proprietary to Telefónica Chile.

## Contact

For questions or support, contact the development team.
