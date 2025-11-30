import os
import warnings
import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

# Suprimir advertencias experimentales de Google ADK
warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*", category=UserWarning)

# Configurar proyecto explícitamente
os.environ["GOOGLE_CLOUD_PROJECT"] = "semovi-licencias-agent"

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# SQLite database for sessions
SESSION_DB_URL = f"sqlite:///{os.path.join(AGENT_DIR, 'sessions.db')}"

# CORS allowed origins
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:3000", "http://localhost:5173", "*"]

# Create FastAPI app using ADK
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_DB_URL,
    allow_origins=ALLOWED_ORIGINS,
    web=True,  # Enable web interface
)

if __name__ == "__main__":
    # Use PORT environment variable, defaulting to 8081
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8081)))