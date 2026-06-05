"""
Health Check Endpoint for Casper Backend

This module provides a health check endpoint for monitoring the backend service.
"""

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
import httpx
import time
from typing import Dict, Any
from datetime import datetime

app = FastAPI(title="Casper Backend Health API")


class HealthStatus:
    """Represents the health status of a service or dependency."""
    
    def __init__(self, healthy: bool = True, message: str = "", latency: float = 0.0):
        self.healthy = healthy
        self.message = message
        self.latency = latency
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "healthy": self.healthy,
            "message": self.message,
            "latency": f"{self.latency:.2f}s"
        }


def check_openai_health(api_key: str) -> HealthStatus:
    """Check OpenAI API health."""
    if not api_key:
        return HealthStatus(healthy=False, message="OpenAI API key not configured")
    
    start_time = time.time()
    try:
        # Make a lightweight API call
        client = httpx.Client(timeout=5.0)
        response = client.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        latency = time.time() - start_time
        
        if response.status_code == 200:
            return HealthStatus(healthy=True, message="OK", latency=latency)
        else:
            return HealthStatus(healthy=False, message=f"API returned {response.status_code}", latency=latency)
    except Exception as e:
        return HealthStatus(healthy=False, message=str(e), latency=time.time() - start_time)


def check_anthropic_health(api_key: str) -> HealthStatus:
    """Check Anthropic API health."""
    if not api_key:
        return HealthStatus(healthy=False, message="Anthropic API key not configured")
    
    start_time = time.time()
    try:
        client = httpx.Client(timeout=5.0)
        response = client.get(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
        )
        latency = time.time() - start_time
        
        # Anthropic returns 401 if key is invalid, but we just want to check connectivity
        if response.status_code in [200, 401, 403]:
            return HealthStatus(healthy=True, message="OK", latency=latency)
        else:
            return HealthStatus(healthy=False, message=f"API returned {response.status_code}", latency=latency)
    except Exception as e:
        return HealthStatus(healthy=False, message=str(e), latency=time.time() - start_time)


@app.get("/health")
async def health_check():
    """
    Health check endpoint that returns the status of the backend service
    and its dependencies.
    """
    import os
    
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Check dependencies
    openai_status = check_openai_health(openai_key)
    anthropic_status = check_anthropic_health(anthropic_key)
    
    # Overall status is healthy if all critical dependencies are healthy
    all_healthy = all([
        openai_status.healthy,
        anthropic_status.healthy
    ])
    
    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "dependencies": {
                "openai": openai_status.to_dict(),
                "anthropic": anthropic_status.to_dict()
            }
        }
    )


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
