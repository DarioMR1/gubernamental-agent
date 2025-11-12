"""Authentication middleware."""

import logging
from typing import Callable, Optional

from fastapi import Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt

from ...config import Environment
from ..types import ErrorResponse


logger = logging.getLogger(__name__)

# Security scheme for Swagger docs
security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for API endpoints."""
    
    def __init__(self, app):
        """Initialize authentication middleware."""
        super().__init__(app)
        
        self.env = Environment()
        
        # Paths that don't require authentication
        self.public_paths = {
            "/health",
            "/health/",
            "/docs", 
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        }
        
        # Paths that require authentication
        self.protected_prefixes = {
            "/v1/sessions",
            "/v1/workflows"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check authentication for protected endpoints."""
        
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Skip authentication if not a protected path
        if not self._is_protected_path(request.url.path):
            return await call_next(request)
        
        # Validate authentication
        auth_result = await self._validate_authentication(request)
        
        if not auth_result["valid"]:
            return self._create_auth_error_response(auth_result["error"], auth_result["status_code"])
        
        # Store user information in request state
        request.state.user = auth_result["user"]
        request.state.authenticated = True
        
        return await call_next(request)
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required).
        
        Args:
            path: Request path
            
        Returns:
            True if path is public
        """
        return path in self.public_paths
    
    def _is_protected_path(self, path: str) -> bool:
        """Check if path requires authentication.
        
        Args:
            path: Request path
            
        Returns:
            True if path requires authentication
        """
        return any(path.startswith(prefix) for prefix in self.protected_prefixes)
    
    async def _validate_authentication(self, request: Request) -> dict:
        """Validate request authentication.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Dictionary with validation result
        """
        try:
            # Extract authorization header
            auth_header = request.headers.get("Authorization")
            
            if not auth_header:
                return {
                    "valid": False,
                    "error": "Missing authorization header",
                    "status_code": status.HTTP_401_UNAUTHORIZED
                }
            
            # Parse bearer token
            if not auth_header.startswith("Bearer "):
                return {
                    "valid": False,
                    "error": "Invalid authorization header format",
                    "status_code": status.HTTP_401_UNAUTHORIZED
                }
            
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Validate token
            user_info = await self._validate_token(token)
            
            if not user_info:
                return {
                    "valid": False,
                    "error": "Invalid or expired token",
                    "status_code": status.HTTP_401_UNAUTHORIZED
                }
            
            return {
                "valid": True,
                "user": user_info
            }
            
        except Exception as e:
            logger.exception("Authentication validation failed")
            return {
                "valid": False,
                "error": "Authentication validation failed",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    async def _validate_token(self, token: str) -> Optional[dict]:
        """Validate JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            User information if valid, None otherwise
        """
        try:
            # For development, allow bypass with special token
            if self.env.ENVIRONMENT == "development" and token == "dev-bypass-token":
                return {
                    "user_id": "dev-user",
                    "username": "developer",
                    "roles": ["admin"],
                    "permissions": ["*"]
                }
            
            # Decode JWT token
            if not self.env.JWT_SECRET:
                logger.warning("JWT_SECRET not configured, rejecting all tokens")
                return None
            
            payload = jwt.decode(
                token,
                self.env.JWT_SECRET,
                algorithms=["HS256"]
            )
            
            # Extract user information
            user_info = {
                "user_id": payload.get("user_id"),
                "username": payload.get("username"),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", []),
                "expires_at": payload.get("exp")
            }
            
            # Validate required fields
            if not user_info["user_id"] or not user_info["username"]:
                logger.warning("Token missing required user information")
                return None
            
            return user_info
            
        except jwt.ExpiredSignatureError:
            logger.info("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
        except Exception as e:
            logger.exception(f"Token validation failed: {e}")
            return None
    
    def _create_auth_error_response(self, error_message: str, status_code: int) -> JSONResponse:
        """Create authentication error response.
        
        Args:
            error_message: Error description
            status_code: HTTP status code
            
        Returns:
            JSONResponse with error details
        """
        error_response = ErrorResponse(
            error={
                "code": "authentication_failed",
                "message": error_message,
                "details": {
                    "suggestion": "Provide a valid Bearer token in the Authorization header"
                }
            }
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.dict(),
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )


# Utility functions for dependency injection

def get_current_user(request: Request) -> dict:
    """Get current authenticated user from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User information dictionary
        
    Raises:
        HTTPException: If user is not authenticated
    """
    from fastapi import HTTPException
    
    if not getattr(request.state, "authenticated", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return getattr(request.state, "user", {})


def require_permission(permission: str):
    """Decorator for endpoints that require specific permissions.
    
    Args:
        permission: Required permission string
        
    Returns:
        Dependency function
    """
    def permission_checker(request: Request) -> dict:
        user = get_current_user(request)
        user_permissions = user.get("permissions", [])
        
        # Check for wildcard permission
        if "*" in user_permissions:
            return user
        
        # Check for specific permission
        if permission not in user_permissions:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        
        return user
    
    return permission_checker


def require_role(role: str):
    """Decorator for endpoints that require specific roles.
    
    Args:
        role: Required role string
        
    Returns:
        Dependency function
    """
    def role_checker(request: Request) -> dict:
        user = get_current_user(request)
        user_roles = user.get("roles", [])
        
        # Check for admin role (has all permissions)
        if "admin" in user_roles:
            return user
        
        # Check for specific role
        if role not in user_roles:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        
        return user
    
    return role_checker