#!/usr/bin/env python3
"""Development server runner script."""

import sys
import argparse
import uvicorn
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.config import Environment


def main():
    """Main entry point for running the server."""
    
    parser = argparse.ArgumentParser(description="Run the Governmental Agent API server")
    parser.add_argument(
        "--env", 
        choices=["development", "staging", "production"],
        default="development",
        help="Environment to run in (default: development)"
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Host to bind to (overrides environment config)"
    )
    parser.add_argument(
        "--port", 
        type=int,
        default=None,
        help="Port to bind to (overrides environment config)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=None,
        help="Enable auto-reload on code changes (development only)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes (production only)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Log level (overrides environment config)"
    )
    
    args = parser.parse_args()
    
    # Load environment configuration
    try:
        env = Environment()
        print(f"🔧 Loading configuration for environment: {args.env}")
        
        # Override environment if specified
        if args.env != "development":
            env.environment = args.env
        
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        sys.exit(1)
    
    # Validate configuration
    try:
        env.validate_api_key()
        env.ensure_directories_exist()
        print("✅ Configuration validated successfully")
        
    except Exception as e:
        print(f"⚠️  Configuration warning: {e}")
        if args.env == "production":
            sys.exit(1)
    
    # Configure server parameters
    host = args.host or env.api_host
    port = args.port or env.api_port
    log_level = (args.log_level or env.log_level).lower()
    
    # Development vs Production configuration
    if env.environment == "development":
        reload = args.reload if args.reload is not None else True
        workers = 1  # Always 1 worker in development
        
        print(f"🚀 Starting development server...")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Auto-reload: {reload}")
        print(f"   Docs: http://{host}:{port}/docs")
        
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True,
            use_colors=True,
            reload_dirs=[str(project_root / "src")]
        )
        
    elif env.environment in ["staging", "production"]:
        workers = args.workers or env.api_workers
        
        print(f"🏭 Starting {env.environment} server...")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Workers: {workers}")
        print(f"   Log level: {log_level}")
        
        # Production server with multiple workers
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            workers=workers,
            log_level=log_level,
            access_log=True,
            server_header=False,
            date_header=False
        )
    
    else:
        print(f"❌ Unknown environment: {env.environment}")
        sys.exit(1)


if __name__ == "__main__":
    main()