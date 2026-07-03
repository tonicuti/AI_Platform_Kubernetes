'''
This acts as the main entry point for your client requests.
'''


import time
import logging
import httpx
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

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
    
    # Internal Kubernetes URLs for your services
    router_url = "http://router-service:3000/health"
    proxy_url = "http://proxy-service:3000/health"
    
    router_status = "unknown"
    proxy_status = "unknown"
    
    # Use an async HTTP client to ping downstream services
    async with httpx.AsyncClient(timeout=2.0) as client:
        # Check Router
        try:
            router_res = await client.get(router_url)
            if router_res.status_code == 200:
                router_status = "healthy"
            else:
                router_status = f"unhealthy (Status: {router_res.status_code})"
        except Exception:
            router_status = "unreachable"
            
        # Check LLM Proxy
        try:
            proxy_res = await client.get(proxy_url)
            if proxy_res.status_code == 200:
                proxy_status = "healthy"
            else:
                proxy_status = f"unhealthy (Status: {proxy_res.status_code})"
        except Exception:
            proxy_status = "unreachable"

    # Determine overall system status
    system_status = "healthy"
    if router_status != "healthy" or proxy_status != "healthy":
        system_status = "degraded"

    return {
        "service": "API Gateway",
        "status": system_status,
        "uptime_seconds": round(uptime, 2),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dependencies": {
            "router_service": router_status,
            "llm_proxy": proxy_status
        }
    }
    
    
# --- Observability Setup ---
# This automatically wraps your FastAPI app and creates a /metrics endpoint.
Instrumentator().instrument(app).expose(app)

@app.get("/")
def health_check():
    return {"status": "healthy"}

@app.get("/route-traffic")
def route_traffic():
    # Your routing logic here
    return {"message": "Traffic routed successfully!"}