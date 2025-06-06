import azure.functions as func
import datetime
import json
import logging
import asyncio
import nest_asyncio
from customer_care_agent_client import agent_care

app = func.FunctionApp()

# Enable CORS for all origins
app.http_cors = {
    "allowed_origins": ["*"],
    "allowed_methods": ["*"],
    "allowed_headers": ["*"]
}

nest_asyncio.apply()

@app.route(route="customer_care_func/{pregunta}", auth_level=func.AuthLevel.ANONYMOUS)
def customer_care_func(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Get the question from the URL path parameter
    pregunta = req.route_params.get('pregunta')
    if not pregunta:
        return func.HttpResponse(
            "Missing 'pregunta' in URL path.", status_code=400
        )

    # Call agent_care from customer_care_agent_client.py and pass the question as an argument
    try:
        answer = asyncio.get_event_loop().run_until_complete(agent_care(pregunta))
        if answer is None:
            answer = ""
    except Exception as e:
        return func.HttpResponse(
            f"Error calling agent_care(): {str(e)}", status_code=500, mimetype="text/html"
        )

    # Si la respuesta ya es HTML, devuélvela tal cual
    if answer.strip().startswith("<!DOCTYPE html>") or answer.strip().startswith("<html"):
        return func.HttpResponse(
            answer,
            mimetype="text/html"
        )

    # Si no es HTML, envuélvela en un HTML simple
    html = f"""
    <html>
        <head><title>Respuesta del Agente</title></head>
        <body>
            <h2>Respuesta:</h2>
            <div style='white-space: pre-wrap; font-family: monospace;'>{answer}</div>
        </body>
    </html>
    """
    return func.HttpResponse(
        html,
        mimetype="text/html"
    )