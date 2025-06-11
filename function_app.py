import azure.functions as func
import logging
import json
import nest_asyncio
from customer_care_agent_mgr import process_question

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('customer_care_func')

app = func.FunctionApp()

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

@app.route(route="api/customer-care/{imsi}/{pregunta}", auth_level=func.AuthLevel.ANONYMOUS, methods=['GET'])
async def customer_care_func(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function entry point for customer care service.
    Accepts GET requests with IMSI and question as part of the URL path.
    """
    logger.info('Function triggered with request: %s', req.url)
    
    try:
        # Get IMSI and question from route parameters
        imsi = req.route_params.get('imsi')
        question = req.route_params.get('pregunta')
        
        if not imsi:
            logger.error('Missing imsi parameter in URL path')
            return func.HttpResponse(
                json.dumps({"error": "Missing IMSI parameter in URL path"}),
                mimetype="application/json",
                status_code=400
            )
        
        if not question:
            logger.error('Missing pregunta parameter in URL path')
            return func.HttpResponse(
                json.dumps({"error": "Missing question parameter in URL path"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Process the question with IMSI
        logger.info('Processing question: %s with IMSI: %s', question, imsi)
        answer = await process_question(question, imsi)
        logger.info('Received answer of length: %d', len(str(answer)) if answer else 0)
        
        if answer is None:
            logger.warning('Received None answer from agent')
            return func.HttpResponse(
                json.dumps({"error": "No answer was generated"}),
                mimetype="application/json",
                status_code=500
            )
        
        # Return successful response
        return func.HttpResponse(
            json.dumps({"answer": answer}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logger.error('Error processing request: %s', str(e), exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )