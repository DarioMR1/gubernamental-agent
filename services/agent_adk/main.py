import os
import warnings

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

# Suprimir advertencias experimentales de Google ADK
warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*", category=UserWarning)

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Session DB URL (SQLite local database)
SESSION_DB_URL = "sqlite:///sessions.db"
# Example allowed origins for CORS  
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:3000", "http://localhost:5173", "*"]
# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = True

# Call the function to get the FastAPI app instance
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_DB_URL,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)


if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8081 (to avoid conflict with Juntoss Engine on 8080)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8081)))