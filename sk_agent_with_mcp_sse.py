#!/usr/bin/env python3
# Semantic Kernel agent with MCP SSE plugin integration

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.mcp import MCPSsePlugin
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelArguments

async def main():
    # Load environment variables from .env file
    current_dir = Path(__file__).parent
    env_path = current_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    
    print("Setting up the Math Assistant with SSE-based MCP calculator...")
    
    # Initialize the kernel
    kernel = Kernel()
    
    # Add an Azure OpenAI service with function calling enabled
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_key = os.getenv("AZURE_OPENAI_KEY")
    if not all([endpoint, deployment, api_key]):
        print("Error: AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT must be set in your .env file.")
        return

    service = AzureChatCompletion(
        endpoint=endpoint,
        api_key=api_key,
        deployment_name=deployment
    )
    kernel.add_service(service)

    # Create the completion service request settings
    settings = AzureChatPromptExecutionSettings()
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
    
    # Configure and use the MCP plugin using SSE via async context manager
    # Note: This assumes the SSE server is already running at this URL
    async with MCPSsePlugin(
        name="CalcServerSSE",
        url="http://localhost:8000/sse"  # URL where the MCP SSE server is listening
    ) as mcp_plugin:
        # Register the MCP plugin with the kernel after connecting
        try:
            kernel.add_plugin(mcp_plugin, plugin_name="calculator")
        except Exception as e:
            print(f"Error: Could not register the MCP plugin: {str(e)}")
            print("\nMake sure the MCP SSE server is running at http://localhost:8000")
            print("Run this command in another terminal: python 04_mcp_server_sse.py")
            return
        
        # Create a chat history with system instructions
        history = ChatHistory()
        history.add_system_message(
            "You are a math assistant. Use the calculator tools when needed to solve math problems. "
            "You have access to add_numbers, subtract_numbers, multiply_numbers, and divide_numbers functions."
        )
        
        # Define a simple chat function
        chat_function = kernel.add_function(
            plugin_name="chat",
            function_name="respond", 
            prompt="{{$chat_history}}"
        )
        
        print("\n┌────────────────────────────────────────────┐")
        print("│ Math Assistant ready with SSE Calculator   │")
        print("└────────────────────────────────────────────┘")
        print("Type 'exit' to end the conversation.")
        print("\nExample questions:")
        print("- What is the sum of 3 and 5?")
        print("- Can you multiply 6 by 7?")
        print("- If I have 20 apples and give away 8, how many do I have left?")
        
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
                print("Make sure the MCP SSE server is running at http://localhost:8000")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting the Math Assistant. Goodbye!")
    except ConnectionRefusedError:
        print("\nError: Could not connect to the MCP SSE server.")
        print("Make sure the server is running: python 04_mcp_server_sse.py")
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("The application has encountered a problem and needs to close.")
