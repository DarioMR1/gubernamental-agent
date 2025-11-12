#!/usr/bin/env python3
"""Production server for Governmental Agent."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_path = current_dir / "src"
sys.path.insert(0, str(src_path))

import uvicorn
from src.api.main import create_application


def main():
    """Run server with environment configuration."""
    parser = argparse.ArgumentParser(description="Run Governmental Agent server")
    parser.add_argument(
        "--env",
        choices=["development", "staging", "production"],
        default="development",
        help="Environment to run in"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development only)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run server on"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind server to"
    )
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["ENVIRONMENT"] = args.env
    
    if args.env == "development":
        os.environ.setdefault("LOG_LEVEL", "DEBUG")
        log_level = "debug"
    elif args.env == "staging":
        os.environ.setdefault("LOG_LEVEL", "INFO")
        log_level = "info"
    else:  # production
        os.environ.setdefault("LOG_LEVEL", "INFO")
        log_level = "warning"
    
    # Create FastAPI application
    app = create_application()
    
    # Configure uvicorn options
    uvicorn_kwargs = {
        "host": args.host,
        "port": args.port,
        "log_level": log_level,
        "access_log": True,
    }
    
    # Only enable reload in development
    if args.env == "development" and args.reload:
        uvicorn_kwargs.update({
            "reload": True,
            "reload_dirs": ["src"]
        })
    
    print(f"🚀 Starting Governmental Agent server")
    print(f"   Environment: {args.env}")
    print(f"   Address: http://{args.host}:{args.port}")
    print(f"   API Docs: http://{args.host}:{args.port}/docs")
    
    # Run server
    uvicorn.run(app, **uvicorn_kwargs)


if __name__ == "__main__":
    main()