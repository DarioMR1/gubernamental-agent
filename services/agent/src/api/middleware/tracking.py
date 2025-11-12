"""Request tracking middleware."""

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking API requests with unique identifiers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request tracking to each API call."""
        
        # Generate or extract request ID
        request_id = self._get_or_create_request_id(request)
        
        # Store request ID in request state for access by other middleware
        request.state.request_id = request_id
        
        # Process the request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    def _get_or_create_request_id(self, request: Request) -> str:
        """Get existing request ID or create a new one.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Request ID string
        """
        # Check if request ID is provided in headers (for request tracing)
        request_id = request.headers.get("X-Request-ID")
        
        if request_id:
            # Validate the provided request ID
            try:
                # Ensure it's a valid UUID format
                uuid.UUID(request_id)
                return request_id
            except ValueError:
                # Invalid format, generate new one
                pass
        
        # Generate new request ID
        return str(uuid.uuid4())
    
    @staticmethod
    def get_request_id(request: Request) -> str:
        """Utility method to get request ID from request state.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Request ID or empty string if not found
        """
        return getattr(request.state, "request_id", "")