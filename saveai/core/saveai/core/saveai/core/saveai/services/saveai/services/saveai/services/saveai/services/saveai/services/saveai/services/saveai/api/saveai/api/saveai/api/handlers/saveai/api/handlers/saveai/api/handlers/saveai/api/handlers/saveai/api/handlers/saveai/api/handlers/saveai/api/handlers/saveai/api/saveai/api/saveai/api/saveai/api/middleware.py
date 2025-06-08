"""
API Middleware and Error Handlers
Version: 1.0.0
Created: 2025-06-08 18:09:48
Author: anandhu723
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException
from typing import Callable, Dict, Any
import time
from datetime import datetime
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses"""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        start_time = time.time()
        
        # Generate request ID
        request_id = f"req_{int(start_time)}_{request.client.host}"
        
        # Log request
        logger.info(
            f"Request {request_id}: {request.method} {request.url}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response {request_id}: {response.status_code} "
                f"(Processed in {process_time:.3f}s)"
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            logger.error(
                f"Error {request_id}: {str(e)}"
            )
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for API rate limiting"""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.rate_limits = {
            "standard": 100,  # requests per minute
            "premium": 1000   # requests per minute
        }
        self.request_history = {}
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        # Get client IP
        client_ip = request.client.host
        
        # Get user tier from auth token (simplified)
        user_tier = "standard"  # This should be determined from auth token
        
        # Check rate limit
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old requests
        self.request_history = {
            ip: requests for ip, requests in self.request_history.items()
            if requests[-1] > minute_ago
        }
        
        # Get request count
        requests = self.request_history.get(client_ip, [])
        requests = [t for t in requests if t > minute_ago]
        
        # Check if limit exceeded
        if len(requests) >= self.rate_limits[user_tier]:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {self.rate_limits[user_tier]} requests per minute"
                }
            )
        
        # Update request history
        requests.append(current_time)
        self.request_history[client_ip] = requests
        
        return await call_next(request)

async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(exc.detail),
            "path": str(request.url),
            "code": f"HTTP_{exc.status_code}"
        }
    )

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Validation Error",
            "detail": exc.errors(),
            "path": str(request.url),
            "code": "VALIDATION_ERROR"
        }
    )

async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle generic exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Internal Server Error",
            "detail": str(exc) if app.debug else "An unexpected error occurred",
            "path": str(request.url),
            "code": "INTERNAL_ERROR"
        }
    )

def setup_middleware(app: FastAPI) -> None:
    """Configure middleware and error handlers"""
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure as needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Add custom middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    # Add exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # Add startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        logger.info("API Starting up...")
        
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("API Shutting down...")
