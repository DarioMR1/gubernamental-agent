"""Error handling middleware."""

import logging
from typing import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..types import ErrorResponse


logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for consistent error handling across the API."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors consistently across all endpoints."""
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            # Log the error with context
            request_id = getattr(request.state, "request_id", "unknown")
            
            logger.exception(
                f"Unhandled error in {request.method} {request.url.path} "
                f"(request_id: {request_id}): {str(e)}"
            )
            
            # Return standardized error response
            return self._create_error_response(e, request_id)
    
    def _create_error_response(self, error: Exception, request_id: str) -> JSONResponse:
        """Create a standardized error response.
        
        Args:
            error: The exception that occurred
            request_id: Request tracking ID
            
        Returns:
            JSONResponse with error details
        """
        # Determine error type and status code
        error_code, status_code, message = self._classify_error(error)
        
        # Create error response
        error_response = ErrorResponse(
            error={
                "code": error_code,
                "message": message,
                "request_id": request_id
            }
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.dict()
        )
    
    def _classify_error(self, error: Exception) -> tuple[str, int, str]:
        """Classify error and determine appropriate response.
        
        Args:
            error: The exception to classify
            
        Returns:
            Tuple of (error_code, status_code, message)
        """
        error_name = error.__class__.__name__
        
        # Known error types
        if "ValidationError" in error_name:
            return "validation_error", status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)
        
        elif "HTTPException" in error_name:
            status_code = getattr(error, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
            detail = getattr(error, "detail", str(error))
            return f"http_{status_code}", status_code, detail
        
        elif "DatabaseError" in error_name or "ConnectionError" in error_name:
            return "database_error", status.HTTP_503_SERVICE_UNAVAILABLE, "Database service unavailable"
        
        elif "TimeoutError" in error_name:
            return "timeout_error", status.HTTP_504_GATEWAY_TIMEOUT, "Request timeout"
        
        elif "PermissionError" in error_name or "Forbidden" in error_name:
            return "permission_denied", status.HTTP_403_FORBIDDEN, "Permission denied"
        
        elif "NotFound" in error_name or "DoesNotExist" in error_name:
            return "not_found", status.HTTP_404_NOT_FOUND, "Resource not found"
        
        elif "RateLimitExceeded" in error_name:
            return "rate_limit_exceeded", status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded"
        
        # Default to internal server error
        return "internal_server_error", status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error"