import asyncio
import os
import pathlib
from dotenv import load_dotenv 
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion  
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelArguments 

async def main():
    # Load environment variables from .env file
    current_dir = pathlib.Path(__file__).parent
    env_path = current_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    
    # Initialize the kernel - the orchestration layer for our agent
    kernel = Kernel()
    
    # Add an Azure OpenAI service
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_key = os.getenv("AZURE_OPENAI_KEY")
    if not all([endpoint, deployment, api_key]):
        raise ValueError("AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, and AZURE_OPENAI_KEY environment variables must be set in your .env file.")

    print(f"Using endpoint: {endpoint}, deployment: {deployment}, key: {api_key[:5]}...")

    model_id = "gpt-4o"  # Choose your model
    service = AzureChatCompletion(
        endpoint=endpoint,
        api_key=api_key,
        deployment_name=deployment,
        ai_model_id=model_id
    )
    kernel.add_service(service)
    
    # Create a chat history with system instructions
    history = ChatHistory()
    history.add_system_message("You are a helpful assistant specialized in explaining concepts.")
    
    # Define a simple streaming chat function
    print("Starting chat. Type 'exit' to end the conversation.")
    
    while True:
        user_input = input("User:> ")
        if user_input.lower() == "exit":
            break
            
        # Add the user message to history
        history.add_user_message(user_input)
        
        # Create streaming arguments
        arguments = KernelArguments(chat_history=history)
        
        # Create a simple chat function (this could also be loaded from a prompt template)
        chat_function = kernel.add_function(
            plugin_name="chat",
            function_name="respond", 
            prompt="{{$chat_history}}"
        )
        
        # Stream the response
        print("Assistant:> ", end="", flush=True)
        
        response_chunks = []
        async for message in kernel.invoke_stream(
            chat_function,
            arguments=arguments,
        ):
            chunk = message[0]
            if isinstance(chunk, StreamingChatMessageContent) and chunk.role == AuthorRole.ASSISTANT:
                print(str(chunk), end="", flush=True)
                response_chunks.append(chunk)
                
        print()  # New line after response
        
        # Add the full response to history
        full_response = "".join(str(chunk) for chunk in response_chunks)
        history.add_assistant_message(full_response)

if __name__ == "__main__":
    asyncio.run(main())
