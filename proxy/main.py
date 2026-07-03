'''
This service handles the actual communication with external Large Language Models 
(like OpenAI, Anthropic, or Gemini).
'''

import time
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langfuse import Langfuse
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_proxy")

app = FastAPI(title="LLM Proxy")
START_TIME = time.time()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_req_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_req_time
    logger.info(f"Proxy | {request.method} {request.url.path} | Status: {response.status_code} | {process_time:.4f}s")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Proxy Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Proxy Error", "details": str(exc)}
    )

@app.get("/health")
async def health_check():
    uptime = time.time() - START_TIME
    return {
        "service": "LLM Proxy",
        "status": "healthy",
        "uptime_seconds": round(uptime, 2),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
# Initialize Langfuse. In Kubernetes, pass these in via your Helm chart's environment variables!
langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-..."),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-..."),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com") 
)

class PromptRequest(BaseModel):
    user_id: str
    prompt: str

@app.post("/generate")
async def generate_response(request: PromptRequest):
    # 1. Start a Langfuse Trace as soon as the request comes in
    trace = langfuse.trace(
        name="Router-to-LLM-Generation",
        user_id=request.user_id,
        input=request.prompt
    )

    # 2. Simulate calling your actual LLM (e.g., OpenAI, local LLM)
    # response = openai.ChatCompletion.create(...)
    mock_output = f"The AI says: {request.prompt} is a great topic."
    prompt_tokens = 15
    completion_tokens = 30

    # 3. Update the trace with the final output and the token cost
    trace.update(
        output=mock_output,
        usage={
            "promptTokens": prompt_tokens, 
            "completionTokens": completion_tokens
        }
    )

    return {"response": mock_output}