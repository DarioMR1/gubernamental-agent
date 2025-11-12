"""Logging middleware for API requests."""

import time
import logging
from typing import Callable
import json

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ...monitoring import StructuredLogger


logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured logging of API requests and responses."""
    
    def __init__(self, app, exclude_paths: set = None):
        """Initialize logging middleware.
        
        Args:
            app: FastAPI application instance
            exclude_paths: Set of paths to exclude from logging
        """
        super().__init__(app)
        
        self.exclude_paths = exclude_paths or {
            "/health",
            "/health/",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
        
        # Initialize structured logger
        self.structured_logger = StructuredLogger()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with structured logging."""
        
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Get request ID from state (set by RequestTrackingMiddleware)
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Extract request information
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
            "content_type": request.headers.get("Content-Type", ""),
            "content_length": request.headers.get("Content-Length", "0")
        }
        
        # Log request start
        self.structured_logger.log_api_request_start(
            method=request.method,
            path=request.url.path,
            request_id=request_id,
            client_ip=request_info["client_ip"],
            user_agent=request_info["user_agent"]
        )
        
        # Process request and capture response
        response = None
        error = None
        
        try:
            response = await call_next(request)
            
        except Exception as e:
            error = e
            logger.exception(f"Request processing failed: {e}")
            
            # Create error response
            from fastapi import HTTPException
            from starlette.responses import JSONResponse
            
            if isinstance(e, HTTPException):
                response = JSONResponse(
                    status_code=e.status_code,
                    content={"error": {"code": "http_error", "message": str(e.detail)}}
                )
            else:
                response = JSONResponse(
                    status_code=500,
                    content={"error": {"code": "internal_error", "message": "Internal server error"}}
                )
        
        # Calculate timing
        processing_time = time.time() - start_time
        
        # Extract response information
        response_info = {
            "status_code": response.status_code if response else 500,
            "response_size": response.headers.get("Content-Length", "0") if response else "0",
            "processing_time_ms": round(processing_time * 1000, 2)
        }
        
        # Log request completion
        if error:
            self.structured_logger.log_api_request_error(
                method=request.method,
                path=request.url.path,
                status_code=response_info["status_code"],
                processing_time=processing_time,
                request_id=request_id,
                error=str(error)
            )
        else:
            self.structured_logger.log_api_request_success(
                method=request.method,
                path=request.url.path,
                status_code=response_info["status_code"],
                processing_time=processing_time,
                request_id=request_id
            )
        
        # Add response headers for observability
        if response:
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time"] = str(response_info["processing_time_ms"])
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client IP address
        """
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _should_log_request_body(self, request: Request) -> bool:
        """Determine if request body should be logged.
        
        Args:
            request: FastAPI request object
            
        Returns:
            True if body should be logged
        """
        # Don't log file uploads or large payloads
        content_type = request.headers.get("Content-Type", "")
        content_length = int(request.headers.get("Content-Length", "0"))
        
        # Skip binary content
        if "multipart/form-data" in content_type or "application/octet-stream" in content_type:
            return False
        
        # Skip large payloads (>1MB)
        if content_length > 1024 * 1024:
            return False
        
        return True
    
    def _should_log_response_body(self, response: Response) -> bool:
        """Determine if response body should be logged.
        
        Args:
            response: FastAPI response object
            
        Returns:
            True if body should be logged
        """
        # Only log JSON responses
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            return False
        
        # Don't log large responses
        content_length = int(response.headers.get("Content-Length", "0"))
        if content_length > 1024 * 10:  # 10KB limit
            return False
        
        return True