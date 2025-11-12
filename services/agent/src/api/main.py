"""FastAPI main application for Governmental Agent API."""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..config import Environment
from .routes import sessions, health, workflows
from .middleware import (
    LoggingMiddleware,
    AuthMiddleware,
    ErrorHandlingMiddleware,
    RequestTrackingMiddleware
)
from .types import ErrorResponse


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Governmental Agent API")
    
    # Initialize any global resources here
    # e.g., database connections, ML models, etc.
    
    yield
    
    # Shutdown
    logger.info("Shutting down Governmental Agent API")
    
    # Clean up resources here


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Load environment configuration
    env = Environment()
    
    # Create FastAPI app
    app = FastAPI(
        title="Governmental Agent API",
        description="REST API for automating governmental portal tasks using AI agents",
        version="1.0.0",
        docs_url="/docs" if env.environment == "development" else None,
        redoc_url="/redoc" if env.environment == "development" else None,
        openapi_url="/openapi.json" if env.environment == "development" else None,
        lifespan=lifespan
    )
    
    # Configure middleware
    _configure_middleware(app, env)
    
    # Configure error handlers
    _configure_error_handlers(app)
    
    # Include routers
    _configure_routes(app)
    
    logger.info("FastAPI application configured successfully")
    return app


def _configure_middleware(app: FastAPI, env: Environment) -> None:
    """Configure application middleware."""
    
    # Security headers and trusted hosts
    if env.allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=env.allowed_hosts
        )
    
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=env.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Total-Count"]
    )
    
    # Custom middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestTrackingMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware)


def _configure_error_handlers(app: FastAPI) -> None:
    """Configure global error handlers."""
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, 
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        logger.warning(f"Validation error for {request.url}: {exc.errors()}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error={
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": {
                        "errors": exc.errors(),
                        "suggestion": "Check the request format and required fields"
                    },
                    "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
                }
            ).dict()
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, 
        exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions."""
        logger.error(f"HTTP error {exc.status_code} for {request.url}: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error={
                    "code": f"http_{exc.status_code}",
                    "message": exc.detail,
                    "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
                }
            ).dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.exception(f"Unexpected error for {request.url}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error={
                    "code": "internal_server_error",
                    "message": "An internal server error occurred",
                    "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
                }
            ).dict()
        )


def _configure_routes(app: FastAPI) -> None:
    """Configure API routes."""
    
    # Include route modules
    app.include_router(
        health.router,
        prefix="/health",
        tags=["Health"]
    )
    
    app.include_router(
        sessions.router,
        prefix="/v1/sessions", 
        tags=["Sessions"]
    )
    
    app.include_router(
        workflows.router,
        prefix="/v1/workflows",
        tags=["Workflows"] 
    )


# Create the application instance
app = create_application()


# Development server runner
def run_dev_server() -> None:
    """Run development server."""
    env = Environment()
    
    uvicorn.run(
        "src.api.main:app",
        host=env.api_host,
        port=env.api_port,
        reload=True,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    run_dev_server()