#!/usr/bin/env python3
"""Development server for Governmental Agent."""

import asyncio
import os
import sys
from pathlib import Path

# Add current directory to Python path to make src a package
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Now we can import from src as a package
import uvicorn


def main():
    """Run development server."""
    # Set development environment
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    
    # Import here to avoid circular imports
    from src.api.main import create_application
    
    # Create FastAPI application
    app = create_application()
    
    # Run with uvicorn (without reload for now)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug"
    )


if __name__ == "__main__":
    main()