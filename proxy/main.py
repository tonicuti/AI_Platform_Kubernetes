'''
This service handles the actual communication with external Large Language Models 
(like OpenAI, Anthropic, or Gemini).
'''

import time
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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