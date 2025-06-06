#!/usr/bin/env python3
# Semantic Kernel agent with MCP stdio plugin integration

import asyncio
import os
import sys
import pathlib
from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion 
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings  
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.mcp import MCPStdioPlugin
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelArguments

async def agent_care(question: str) -> str:
    # Load environment variables from .env file
    current_dir = pathlib.Path(__file__).parent
    env_path = current_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    
    # Find the correct paths to the MCP server scripts
    mcp_calculator_path = current_dir / "mcp_calculator_server.py"
    mcp_weather_path = current_dir / "mcp_weather_server.py"
    mcp_customer_care_path = current_dir / "customer_care_server.py"

    # Make sure the server scripts exist
    if not mcp_calculator_path.exists():
        return f"Error: MCP calculator server script not found at {mcp_calculator_path}"
    if not mcp_weather_path.exists():
        return f"Error: MCP weather server script not found at {mcp_weather_path}"
    if not mcp_customer_care_path.exists():
        return f"Error: MCP customer care server script not found at {mcp_customer_care_path}"

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
        name="CalcServer",
        command="python",
        args=[str(mcp_calculator_path)]
    ) as calc_plugin, MCPStdioPlugin(
        name="WeatherServer",
        command="python",
        args=[str(mcp_weather_path)]
    ) as weather_plugin, MCPStdioPlugin(
        name="CustomerCareServer",
        command="python",
        args=[str(mcp_customer_care_path)]
    ) as customer_plugin:
        try:
            kernel.add_plugin(calc_plugin, plugin_name="calculator")
            kernel.add_plugin(weather_plugin, plugin_name="weather")
            kernel.add_plugin(customer_plugin, plugin_name="customer_care")
        except Exception as e:
            return f"Error: Could not register the MCP plugins: {str(e)}"
        history = ChatHistory()
        history.add_system_message(
            "Eres un agente de atención al cliente listo para responder todo tipo de preguntas de los clientes o sobre los clientes. "  
            "Puedes ayudar con información del cliente, preguntas de matemáticas y actualizaciones del clima. "  
            "Para responder preguntas sobre información del cliente, utilizas las herramientas de atención al cliente, que recuperan datos del cliente pasando el ID del cliente al servicio de atención al cliente. "  
            "Por ejemplo, para obtener detalles sobre un cliente, utiliza la función get_customer_by_id y proporciona el ID del cliente. "  
            "También tienes acceso a herramientas de calculadora (add_numbers, subtract_numbers, multiply_numbers, divide_numbers) para preguntas de matemáticas, y herramientas del clima (get_weather) para preguntas sobre el clima. "  
            "Si un usuario pregunta sobre el clima en Boston, utiliza la herramienta get_weather para 'x boston'. "  
            "Si un usuario hace una pregunta de matemáticas, utiliza las herramientas de calculadora. "  
            "Si un usuario pregunta sobre un cliente por ID, utiliza las herramientas de atención al cliente para recuperar su información. "  
            "Si en la pregunta se te da el nombre del cliente solamente busca un metodo para traer el nombre cliente y no uses el ID. "
            "Siempre proporciona respuestas claras y útiles, y explica qué herramienta utilizaste si es relevante."
            "Contesta siempre en un formato HTML, con un título y párrafos claros. USa colores, titulos, espacios, listas fonts adecuados "
            " no uses azul en el titulo por que mi background es negro.  No comiences con ```html o termines con ``` keep it simple"
            " siempre usa background negro y no uses colores claros para el font usa gold en titulos ya que el background que tengo es negro."
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

if __name__ == "__main__":
    try:
        
            question = "Dame le temperatura en Boston"
            answer = asyncio.run(agent_care(question))
            print(answer)
       
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
