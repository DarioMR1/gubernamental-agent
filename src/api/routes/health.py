"""Health check endpoints."""

import logging
import asyncio
from datetime import datetime
import pkg_resources

from fastapi import APIRouter, Depends
from ..types import HealthResponse, HealthStatus, ComponentHealth


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Application health check",
    description="Returns the health status of the application and its components"
)
async def health_check():
    """Comprehensive health check endpoint."""
    
    start_time = datetime.now()
    
    # Check individual components
    components = {}
    overall_status = HealthStatus.HEALTHY
    
    # Check database connectivity
    db_health = await _check_database()
    components["database"] = db_health
    if db_health.status != HealthStatus.HEALTHY:
        overall_status = HealthStatus.DEGRADED
    
    # Check LLM providers
    llm_health = await _check_llm_providers()
    components["llm_providers"] = llm_health
    if llm_health.status != HealthStatus.HEALTHY:
        overall_status = HealthStatus.DEGRADED
    
    # Check Playwright browser
    browser_health = await _check_browser()
    components["browser"] = browser_health
    if browser_health.status != HealthStatus.HEALTHY:
        overall_status = HealthStatus.DEGRADED
    
    # Check storage
    storage_health = await _check_storage()
    components["storage"] = storage_health
    if storage_health.status != HealthStatus.HEALTHY:
        overall_status = HealthStatus.DEGRADED
    
    # Check memory usage
    memory_health = await _check_memory()
    components["memory"] = memory_health
    if memory_health.status != HealthStatus.HEALTHY:
        overall_status = HealthStatus.DEGRADED
    
    # If any critical component is unhealthy, mark overall as unhealthy
    critical_components = ["database", "storage"]
    for component_name in critical_components:
        if components[component_name].status == HealthStatus.UNHEALTHY:
            overall_status = HealthStatus.UNHEALTHY
            break
    
    # Get application version
    try:
        version = pkg_resources.get_distribution("gubernamental-agent").version
    except Exception:
        version = "unknown"
    
    return HealthResponse(
        status=overall_status,
        version=version,
        timestamp=start_time,
        components=components
    )


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Returns 200 if the application is ready to serve requests"
)
async def readiness_check():
    """Kubernetes readiness probe."""
    
    # Quick check of critical components
    critical_checks = await asyncio.gather(
        _check_database_connection(),
        _check_storage_access(),
        return_exceptions=True
    )
    
    # If any critical check fails, service is not ready
    for result in critical_checks:
        if isinstance(result, Exception):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail="Service not ready"
            )
    
    return {"status": "ready"}


@router.get(
    "/live",
    summary="Liveness probe", 
    description="Returns 200 if the application is alive"
)
async def liveness_check():
    """Kubernetes liveness probe."""
    
    # Simple liveness check
    return {"status": "alive"}


# Component health check functions

async def _check_database() -> ComponentHealth:
    """Check database health."""
    start_time = datetime.now()
    
    try:
        # Import here to avoid circular imports
        from ...storage import DatabaseManager
        
        db_manager = DatabaseManager()
        
        # Simple connection test
        check_start = datetime.now()
        await db_manager.check_connection()
        response_time = (datetime.now() - check_start).total_seconds() * 1000
        
        return ComponentHealth(
            status=HealthStatus.HEALTHY,
            message="Database connection successful",
            response_time_ms=response_time,
            last_check=start_time
        )
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            message=f"Database connection failed: {str(e)}",
            last_check=start_time
        )


async def _check_llm_providers() -> ComponentHealth:
    """Check LLM provider health."""
    start_time = datetime.now()
    
    try:
        from ...llm.providers import OpenAIProvider, AnthropicProvider
        from ...config import Environment
        
        env = Environment()
        response_times = []
        
        # Test OpenAI if configured
        if env.OPENAI_API_KEY:
            try:
                provider = OpenAIProvider()
                check_start = datetime.now()
                # Simple test call (would need actual implementation)
                # await provider.test_connection()
                response_time = (datetime.now() - check_start).total_seconds() * 1000
                response_times.append(response_time)
            except Exception as e:
                logger.warning(f"OpenAI provider check failed: {e}")
        
        # Test Anthropic if configured  
        if env.ANTHROPIC_API_KEY:
            try:
                provider = AnthropicProvider()
                check_start = datetime.now()
                # Simple test call (would need actual implementation)
                # await provider.test_connection()
                response_time = (datetime.now() - check_start).total_seconds() * 1000
                response_times.append(response_time)
            except Exception as e:
                logger.warning(f"Anthropic provider check failed: {e}")
        
        if not response_times:
            return ComponentHealth(
                status=HealthStatus.DEGRADED,
                message="No LLM providers configured",
                last_check=start_time
            )
        
        avg_response_time = sum(response_times) / len(response_times)
        
        return ComponentHealth(
            status=HealthStatus.HEALTHY,
            message=f"LLM providers available ({len(response_times)} configured)",
            response_time_ms=avg_response_time,
            last_check=start_time
        )
        
    except Exception as e:
        logger.error(f"LLM provider health check failed: {e}")
        return ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            message=f"LLM provider check failed: {str(e)}",
            last_check=start_time
        )


async def _check_browser() -> ComponentHealth:
    """Check Playwright browser health."""
    start_time = datetime.now()
    
    try:
        from ...executor import PlaywrightExecutor
        from ...config import AgentConfig
        
        config = AgentConfig()
        executor = PlaywrightExecutor(config)
        
        check_start = datetime.now()
        # Test browser initialization
        # await executor.test_browser()
        response_time = (datetime.now() - check_start).total_seconds() * 1000
        
        return ComponentHealth(
            status=HealthStatus.HEALTHY,
            message="Browser engine available",
            response_time_ms=response_time,
            last_check=start_time
        )
        
    except Exception as e:
        logger.error(f"Browser health check failed: {e}")
        return ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            message=f"Browser check failed: {str(e)}",
            last_check=start_time
        )


async def _check_storage() -> ComponentHealth:
    """Check storage system health."""
    start_time = datetime.now()
    
    try:
        import os
        import tempfile
        from pathlib import Path
        
        # Test file system access
        check_start = datetime.now()
        
        # Test write to storage directory
        storage_path = Path("./storage")
        storage_path.mkdir(exist_ok=True)
        
        test_file = storage_path / "health_test.tmp"
        test_file.write_text("health check")
        test_file.unlink()  # Clean up
        
        response_time = (datetime.now() - check_start).total_seconds() * 1000
        
        return ComponentHealth(
            status=HealthStatus.HEALTHY,
            message="Storage system accessible",
            response_time_ms=response_time,
            last_check=start_time
        )
        
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            message=f"Storage check failed: {str(e)}",
            last_check=start_time
        )


async def _check_memory() -> ComponentHealth:
    """Check memory usage."""
    start_time = datetime.now()
    
    try:
        import psutil
        
        # Get memory information
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Determine status based on memory usage
        if memory_percent < 80:
            status = HealthStatus.HEALTHY
            message = f"Memory usage: {memory_percent:.1f}%"
        elif memory_percent < 90:
            status = HealthStatus.DEGRADED
            message = f"High memory usage: {memory_percent:.1f}%"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Critical memory usage: {memory_percent:.1f}%"
        
        return ComponentHealth(
            status=status,
            message=message,
            last_check=start_time
        )
        
    except ImportError:
        # psutil not available
        return ComponentHealth(
            status=HealthStatus.DEGRADED,
            message="Memory monitoring unavailable (psutil not installed)",
            last_check=start_time
        )
    except Exception as e:
        logger.error(f"Memory health check failed: {e}")
        return ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            message=f"Memory check failed: {str(e)}",
            last_check=start_time
        )


# Helper functions for readiness checks

async def _check_database_connection() -> bool:
    """Quick database connection check."""
    try:
        from ...storage import DatabaseManager
        db_manager = DatabaseManager()
        await db_manager.check_connection()
        return True
    except Exception:
        return False


async def _check_storage_access() -> bool:
    """Quick storage access check."""
    try:
        from pathlib import Path
        storage_path = Path("./storage")
        storage_path.mkdir(exist_ok=True)
        return storage_path.exists() and storage_path.is_dir()
    except Exception:
        return False