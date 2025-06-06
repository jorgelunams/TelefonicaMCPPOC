import azure.functions as func
import logging
import json
import sys
import subprocess

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('HTTP trigger function processed a request.')
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            "Invalid JSON in request body.", status_code=400
        )
    
    question = req_body.get("question")
    if not question:
        return func.HttpResponse(
            "Missing 'question' in request body.", status_code=400
        )

    # Call customer_care_agent_client.py and pass the question as an argument
    try:
        result = subprocess.run(
            [sys.executable, "customer_care_agent_client.py", question],
            capture_output=True, text=True, check=True
        )
        answer = result.stdout.strip()
    except Exception as e:
        return func.HttpResponse(
            f"Error calling customer_care_agent_client.py: {str(e)}", status_code=500
        )

    return func.HttpResponse(
        json.dumps({"answer": answer}),
        mimetype="application/json"
    )
