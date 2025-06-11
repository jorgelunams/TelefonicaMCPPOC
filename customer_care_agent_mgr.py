import os  
import asyncio  
import json
import types
import pathlib
from pydantic import BaseModel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.mcp import MCPStdioPlugin
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory 
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelArguments
from semantic_kernel.agents import ChatCompletionAgent, Agent
from dotenv import load_dotenv

# Semantic Kernel agent with MCP stdio plugin integration

# Your existing ArticleAnalysis model  
class ArticleAnalysis(BaseModel):  
    themes: list[str] = []  
    sentiments: list[str] = []  
    entities: list[str] = []  
    customer_care_response: str = ""  

async def agent_care(question: str) -> str:
    """Implementation of the agent care functionality"""
    # Load environment variables from .env file
    current_dir = pathlib.Path(__file__).parent
    env_path = current_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    
    # Find the correct paths to the MCP server scripts
    mcp_internet_path = current_dir / "mcp_internet_extarct_server.py"
    mcp_knowledge_base_path = current_dir / "customer_care_knowledge_base_server.py"

    # Make sure the server scripts exist
    if not mcp_internet_path.exists():
        return f"Error: MCP internet server script not found at {mcp_internet_path}"
    if not mcp_knowledge_base_path.exists():
        return f"Error: MCP knowledge base server script not found at {mcp_knowledge_base_path}"

    kernel = Kernel()
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_key = os.getenv("AZURE_OPENAI_KEY")
    if not all([endpoint, deployment, api_key]):
        return "Error: AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT must be set in your .env file."
    
    service = AzureChatCompletion(
        endpoint=endpoint,
        api_key=api_key,
        deployment_name=deployment
    )
    kernel.add_service(service)
    settings = AzureChatPromptExecutionSettings()
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
    
    async with MCPStdioPlugin(
        name="InternetServer",
        command="python",
        args=[str(mcp_internet_path)]
    ) as internet_plugin, MCPStdioPlugin(
        name="KnowledgeBaseServer",
        command="python",
        args=[str(mcp_knowledge_base_path)]
    ) as kb_plugin:
        try:
            kernel.add_plugin(internet_plugin, plugin_name="internet_extract")
            kernel.add_plugin(kb_plugin, plugin_name="knowledge_base")
        except Exception as e:
            return f"Error: Could not register the MCP plugins: {str(e)}"
        
        try:
            history = ChatHistory()
            history.add_system_message("No inventes nada y no uses información que no esté en las herramientas. "
                "Eres un agente de atención al cliente en Chile, listo para responder todo tipo de preguntas de los clientes. "  
                "Puedes ayudar con información del cliente, verificar el estado de sus cuentas y determinar si un dispositivo es compatible con eSIM. "  
                "Para responder preguntas sobre información del cliente, utilizas las herramientas de atención al cliente, "
                "que recuperan datos del cliente pasando el ID del cliente al servicio de atención al cliente. "  
                "Si el usuario no proporciona el ID del cliente, debes solicitarlo amablemente y explicar por qué lo necesitas. "
                "Por ejemplo: 'Para poder proporcionarle información detallada sobre su cuenta, ¿podría facilitarme su número de ID de cliente?' "
                "Si se te da el nombre del cliente, solamente busca un método para traer el nombre del cliente y no uses el ID. "  
                "Para verificar si un dispositivo es compatible con eSIM, utiliza la herramienta de servidor de internet que extrae datos sobre la compatibilidad de dispositivos. "  
                "Los datos deben ser extraídos de los siguientes URLs: "  
                "urlApple = https://esimblow.com/es/dispositivos/dispositivos-apple-esim/ y "  
                "urlSamsung = https://www.samsung.com/latin/support/mobile-devices/galaxy-esim-and-supported-network-carriers/?msockid=1803ea69355c6f270dc0ffb034346ee2. "  
                "Una vez que hayas obtenido la información, proporciona una respuesta clara al cliente sobre la compatibilidad con eSIM. "  
                "Siempre proporciona respuestas claras y útiles, y explica qué herramienta utilizaste si es relevante. "  
                "Contesta siempre en un formato HTML, con un título y párrafos claros. Usa colores, títulos, espacios, listas y fuentes adecuadas. "  
                "No uses azul en el título porque mi background es negro. No comiences con ```html o termines con ```; manténlo simple. "  
                "Siempre usa background negro y no uses colores claros para el font; usa gold en títulos ya que el background que tengo es negro. "  
                "Si el cliente quiere saber si su dispositivo móvil es compatible con eSIM, solo contesta 'sí' o 'no' y explica de dónde sacaste la información. "
                "Importante revisa la lista que recibiste del web site de Apple o Samsung y con cuidado ve si el modelo exacto del dispositivo se encuentra en la lista. No basta con que diga iPhone o Samsung, debe ser el modelo específico. "
                "NO inventes nada, es muy importante tener la respuesta correcta. Si no encuentras la información exacta, indícalo claramente."
            )
            history.add_user_message(question)
            chat_function = kernel.add_function(
                plugin_name="chat",
                function_name="respond",
                prompt="{{$chat_history}}"
            )
            arguments = KernelArguments(
                chat_history=history,
                settings=settings
            )
            try:
                response_chunks = []
                async for message in kernel.invoke_stream(
                    chat_function,
                    arguments=arguments
                ):
                    chunk = message[0]
                    if isinstance(chunk, StreamingChatMessageContent) and chunk.role == AuthorRole.ASSISTANT:
                        response_chunks.append(str(chunk))
                return "".join(response_chunks)
            except Exception as e:
                return f"Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"

# Define a new agent that calls the agent_care function  
class AgentCare(Agent):  
    def __init__(self):  
        super().__init__(name="AgentCare", instructions="Agente que maneja consultas de atención al cliente.")  

    async def invoke(self, question: str) -> str:
        # This is the main method that processes the input question
        return await agent_care(question)

    async def get_response(self, *args, **kwargs):
        raise NotImplementedError("get_response is not implemented for AgentCare.")

    async def invoke_stream(self, *args, **kwargs):
        raise NotImplementedError("invoke_stream is not implemented for AgentCare.")

# New ManagerAgent class
class ManagerAgent(ChatCompletionAgent):
    def __init__(self, service=None):
        instructions = (
            "You are a manager agent that helps select the appropriate agent for customer inquiries. "
            "Your task is to analyze each question and determine which of these agents should handle it:\n"
            "1. SentimentAnalysisAgent - For analyzing call emotions and customer satisfaction\n"
            "2. RatePlansExpertAgent - For rate plans, pricing, and service costs information\n" 
            "3. AgentCare - For general queries and service issues like devices, sim cards, etc\n\n"
            "Response format: A JSON object with:\n"
            "Do not change the question. Kepp it as is.\n"
            '{"agent": "AgentName", "question": "processed question"}\n\n'
            "Example:\n"
            '{"agent": "RatePlansExpertAgent", "question": "What are the available mobile plans and their prices?"}\n\n'
            "ALWAYS return a valid JSON response."
        )
        super().__init__(service=service, instructions=instructions, name="ManagerAgent")

def get_agents() -> list[Agent]:  
    """Return a list of agents that will participate in the concurrent orchestration."""  
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")  
    api_key = os.getenv("AZURE_OPENAI_KEY")  
    if not all([endpoint, deployment, api_key]):  
        raise RuntimeError("Missing environment variables: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_KEY")  
  
    service = AzureChatCompletion(  
        endpoint=endpoint,  
        api_key=api_key,  
        deployment_name=deployment,  
    )  
  
    # Specialized analysis agents
    sentiment_agent = ChatCompletionAgent(  
        name="SentimentAnalysisAgent",  
        instructions=(
            "Eres un analista experto en emociones y sentimientos de llamadas de clientes de Telefónica. Tu tarea es:\n"
            "1. Analizar detalladamente el sentimiento del cliente durante la llamada\n"
            "2. Identificar puntos específicos donde la emoción cambia\n"
            "3. Clasificar el nivel de satisfacción en una escala de 1-5\n"
            "4. Detectar palabras clave que indican frustración o satisfacción\n"
            "5. Sugerir acciones específicas basadas en el análisis emocional"
        ),
        service=service,  
    )  
    
    rate_plans_agent = ChatCompletionAgent(  
        name="RatePlansExpertAgent",  
        instructions=(
            "Eres el experto en planes tarifarios y precios de servicios de Telefónica Chile. Tus responsabilidades son:\n"
            "1. Proporcionar información detallada sobre todos los planes tarifarios disponibles\n"
            "2. Explicar precios y costos de servicios móviles, fijos e internet\n"
            "3. Detallar promociones y ofertas vigentes\n"
            "4. Comparar diferentes planes y recomendar el más adecuado según las necesidades del cliente\n"
            "5. Aclarar condiciones, términos y beneficios incluidos en cada plan\n"
            "6. Explicar procesos de cambio de plan y costos asociados\n"
            "Formatea tus respuestas en HTML claro y estructurado, usando colores compatibles con fondo negro.\n"
            "IMPORTANTE: Enfócate exclusivamente en planes tarifarios y precios de Telefónica Chile."
        ),
        service=service,  
    )  
  
    # Add the customer care agent  
    agent_care = AgentCare()  
  
    return [sentiment_agent, rate_plans_agent, agent_care]  
  
async def process_question(question: str, imsi: str = None) -> str:
    """
    Process a single question using the appropriate specialized agent.
    
    Args:
        question (str): The question or text to process
        imsi (str, optional): The IMSI of the customer
        
    Returns:
        str: The response from the selected agent
        
    Raises:
        RuntimeError: If required environment variables are missing
        Exception: If there's an error processing the question
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")  
    api_key = os.getenv("AZURE_OPENAI_KEY")  
    if not all([endpoint, deployment, api_key]):  
        raise RuntimeError("Missing environment variables: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_KEY")  
  
    service = AzureChatCompletion(  
        endpoint=endpoint,  
        api_key=api_key,  
        deployment_name=deployment,  
    )  
      
    # Get the list of available agents
    all_agents = get_agents()
    
    # Create a dictionary of agents by name
    agents = {
        agent.name: agent for agent in all_agents
    }
    
    # Initialize the manager agent
    manager_agent = ManagerAgent(service=service)

    # Prepare the question with IMSI if provided
    if imsi:
        enhanced_question = f"Este es el IMSI del cliente: {imsi}. Su pregunta es: '{question}'"
    else:
        enhanced_question = question

    try:
        # Ask the manager agent which agent to use
        response_chunks = []
        async for message in manager_agent.invoke(enhanced_question):
            response_chunks.append(str(message))
        manager_response = "".join(response_chunks)
        
        result = json.loads(manager_response)
        agent_name = result.get("agent")
        processed_question = enhanced_question
        
        if agent_name not in agents:
            raise ValueError(f"Unknown agent suggested: {agent_name}")
            
        selected_agent = agents[agent_name]
        
        # Handle streaming (async generator) vs coroutine agents
        invoke_result = selected_agent.invoke(processed_question)
        if isinstance(invoke_result, types.AsyncGeneratorType):
            answer_chunks = []
            async for message in invoke_result:
                answer_chunks.append(str(message))
            answer = "".join(answer_chunks)
        else:
            answer = await invoke_result
            
        return answer
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse manager response: {e}\n{manager_response}")
    except Exception as e:
        raise Exception(f"Error processing question: {str(e)}")

async def main():
    """Direct call to test the agent system with specific question and IMSI."""
    question = "puede mi celular usar el eSIM"
    imsi = "730029988243961"
    
    print(f"\nProcesando pregunta: '{question}' con IMSI: {imsi}")
    
    try:
        answer = await process_question(question, imsi)
        print(f"\nRespuesta:\n{answer}")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":  
    asyncio.run(main())