'''
This acts as the main entry point for your client requests.
'''


import time
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_gateway")

app = FastAPI(title="API Gateway")
START_TIME = time.time()

# 1. Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_req_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_req_time
    logger.info(f"Gateway | {request.method} {request.url.path} | Status: {response.status_code} | {process_time:.4f}s")
    return response

# 2. Global Error Handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Gateway Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Gateway Error", "details": str(exc)}
    )

# 3. Health Endpoint
@app.get("/health")
async def health_check():
    uptime = time.time() - START_TIME
    return {
        "service": "API Gateway",
        "status": "healthy",
        "uptime_seconds": round(uptime, 2),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }