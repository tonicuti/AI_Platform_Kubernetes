'''
This service is responsible for determining where a request should go 
(e.g., picking the right LLM).
'''


import time
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("router_service")

app = FastAPI(title="Router Service")
START_TIME = time.time()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_req_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_req_time
    logger.info(f"Router | {request.method} {request.url.path} | Status: {response.status_code} | {process_time:.4f}s")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Router Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Router Error", "details": str(exc)}
    )

@app.get("/health")
async def health_check():
    uptime = time.time() - START_TIME
    return {
        "service": "Router Service",
        "status": "healthy",
        "uptime_seconds": round(uptime, 2),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }