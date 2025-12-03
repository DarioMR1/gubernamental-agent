#!/usr/bin/env python3
import os
import sys
import warnings

import uvicorn
from fastapi import FastAPI

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from google.adk.cli.fast_api import get_fast_api_app
except ImportError as e:
    print(f"Error importing Google ADK: {e}")
    print("Make sure you have installed the google-adk package")
    sys.exit(1)

# Suprimir advertencias experimentales de Google ADK
warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*", category=UserWarning)

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"Agent directory: {AGENT_DIR}")

# Session DB URL (SQLite local database)
SESSION_DB_URL = "sqlite:///sessions.db"

# Example allowed origins for CORS  
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:3000", "http://localhost:5173", "*"]

# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = True

try:
    # Call the function to get the FastAPI app instance
    app: FastAPI = get_fast_api_app(
        agents_dir=AGENT_DIR,
        session_service_uri=SESSION_DB_URL,
        allow_origins=ALLOWED_ORIGINS,
        web=SERVE_WEB_INTERFACE
    )
    print("✅ FastAPI app created successfully")
except Exception as e:
    print(f"❌ Error creating FastAPI app: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8081 (to avoid conflict with Juntoss Engine on 8080)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8081)))