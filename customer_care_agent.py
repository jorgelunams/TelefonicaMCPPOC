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

async def main():
    # Load environment variables from .env file
    current_dir = pathlib.Path(__file__).parent
    env_path = current_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    
    # Find the correct paths to the MCP server scripts
    mcp_calculator_path = current_dir / "mcp_calculator_server.py"
    mcp_weather_path = current_dir / "mcp_weather_server.py"

    # Make sure the server scripts exist
    if not mcp_calculator_path.exists():
        print(f"Error: MCP calculator server script not found at {mcp_calculator_path}")
        sys.exit(1)
    if not mcp_weather_path.exists():
        print(f"Error: MCP weather server script not found at {mcp_weather_path}")
        sys.exit(1)

    print("Setting up the Math and Weather Assistant with MCP plugins...")

    # Initialize the kernel
    kernel = Kernel()

    # Add an Azure OpenAI service with all required elements from .env
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_key = os.getenv("AZURE_OPENAI_KEY")
    if not all([endpoint, deployment, api_key]):
        print("Error: AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT must be set in your .env file.")
        sys.exit(1)
    service = AzureChatCompletion(
        endpoint=endpoint,
        api_key=api_key,
        deployment_name=deployment
    )
    kernel.add_service(service)

    # Create the completion service request settings
    settings = AzureChatPromptExecutionSettings()
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    # Configure and use the MCP plugins for calculator and weather using async context managers
    async with MCPStdioPlugin(
        name="CalcServer",
        command="python",
        args=[str(mcp_calculator_path)]
    ) as calc_plugin, MCPStdioPlugin(
        name="WeatherServer",
        command="python",
        args=[str(mcp_weather_path)]
    ) as weather_plugin:
        # Register the MCP plugins with the kernel
        try:
            kernel.add_plugin(calc_plugin, plugin_name="calculator")
            kernel.add_plugin(weather_plugin, plugin_name="weather")
        except Exception as e:
            print(f"Error: Could not register the MCP plugins: {str(e)}")
            sys.exit(1)

        # Create a chat history with system instructions
        history = ChatHistory()
        history.add_system_message(
            "You are an assistant. Use the calculator tools when needed to solve math problems, "
            "and use the weather tools to answer weather questions. "
            "You have access to add_numbers, subtract_numbers, multiply_numbers, divide_numbers, and get_weather functions. "
            "If a user asks about the weather in Boston, use the get_weather tool for 'x boston'. "
            "If a user asks a math question, use the calculator tools."
        )

        # Define a simple chat function
        chat_function = kernel.add_function(
            plugin_name="chat",
            function_name="respond",
            prompt="{{$chat_history}}"
        )

        print("\n┌────────────────────────────────────────────────────────────┐")
        print("│ Math & Weather Assistant ready with MCP Calculator/Weather │")
        print("└────────────────────────────────────────────────────────────┘")
        print("Type 'exit' to end the conversation.")
        print("\nExample questions:")
        print("- What is the sum of 3 and 5?")
        print("- Can you multiply 6 by 7?")
        print("- If I have 20 apples and give away 8, how many do I have left?")
        print("- What is the weather in Boston?")
        print("- What is the weather in x Boston?")

        while True:
            user_input = input("\nUser:> ")
            if user_input.lower() == "exit":
                break

            # Add the user message to history
            history.add_user_message(user_input)

            # Prepare arguments with history and settings
            arguments = KernelArguments(
                chat_history=history,
                settings=settings
            )

            try:
                # Stream the response
                print("Assistant:> ", end="", flush=True)

                response_chunks = []
                async for message in kernel.invoke_stream(
                    chat_function,
                    arguments=arguments
                ):
                    chunk = message[0]
                    if isinstance(chunk, StreamingChatMessageContent) and chunk.role == AuthorRole.ASSISTANT:
                        print(str(chunk), end="", flush=True)
                        response_chunks.append(chunk)

                print()  # New line after response

                # Add the full response to history
                full_response = "".join(str(chunk) for chunk in response_chunks)
                history.add_assistant_message(full_response)

            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Please try another question.")

async def ask_agent(question: str) -> str:
    """
    Call the Math & Weather Assistant with a user question and return the response as a string.
    """
    current_dir = pathlib.Path(__file__).parent
    env_path = current_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    mcp_calculator_path = current_dir / "mcp_calculator_server.py"
    mcp_weather_path = current_dir / "mcp_weather_server.py"
    if not mcp_calculator_path.exists():
        return f"Error: MCP calculator server script not found at {mcp_calculator_path}"
    if not mcp_weather_path.exists():
        return f"Error: MCP weather server script not found at {mcp_weather_path}"
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
    ) as weather_plugin:
        try:
            kernel.add_plugin(calc_plugin, plugin_name="calculator")
            kernel.add_plugin(weather_plugin, plugin_name="weather")
        except Exception as e:
            return f"Error: Could not register the MCP plugins: {str(e)}"
        history = ChatHistory()
        history.add_system_message(
            "You are an assistant. Use the calculator tools when needed to solve math problems, "
            "and use the weather tools to answer weather questions. "
            "You have access to add_numbers, subtract_numbers, multiply_numbers, divide_numbers, and get_weather functions. "
            "If a user asks about the weather in Boston, use the get_weather tool for 'x boston'. "
            "If a user asks a math question, use the calculator tools."
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
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting the Math Assistant. Goodbye!")
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("The application has encountered a problem and needs to close.")
