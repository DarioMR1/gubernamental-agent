import os
import warnings

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

# Suprimir advertencias experimentales de Google ADK
warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*", category=UserWarning)

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Example session DB URL (e.g., SQLite)
SESSION_DB_URL = "postgresql://postgres.dsfcdqkmwxsrtmuagbcy:vVvkBoQLRFcX4chI@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
# Example allowed origins for CORS  
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:3000", "http://localhost:5173", "*"]
# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = True

# Call the function to get the FastAPI app instance
# Ensure the agent directory name ('capital_agent') matches your agent folder
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_DB_URL,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

# Custom endpoint to update session state with new auth token
@app.patch("/apps/{app_name}/users/{user_id}/sessions/{session_id}/state")
async def update_session_state(
    app_name: str, 
    user_id: str, 
    session_id: str,
    state_update: dict
):
    """
    Custom endpoint to update session state directly.
    This is used to sync refreshed auth tokens from the frontend.
    """
    from google.adk.sessions.database_session_service import DatabaseSessionService
    from google.adk.events import Event, EventActions
    import time
    
    try:
        # Create session service instance with the same DB URL
        session_service = DatabaseSessionService(db_url=SESSION_DB_URL)
        
        # Get the current session
        session = await session_service.get_session(
            app_name=app_name, 
            user_id=user_id, 
            session_id=session_id
        )
        
        if not session:
            return {"error": "Session not found"}, 404
        
        # Create a system event with state_delta to update the session
        # This is the proper way to update session state in ADK
        event = Event(
            invocation_id=f"state_update_{int(time.time())}",
            author="system",
            timestamp=time.time(),
            actions=EventActions(
                state_delta=state_update  # The state changes to apply
            )
        )
        
        # Append the event to the session
        await session_service.append_event(session=session, event=event)
        
        # Get the updated session to return
        updated_session = await session_service.get_session(
            app_name=app_name, 
            user_id=user_id, 
            session_id=session_id
        )
        
        return {
            "success": True,
            "message": "Session state updated successfully",
            "session_id": session_id,
            "updated_state": updated_session.state if updated_session else None
        }
        
    except Exception as e:
        return {
            "error": f"Failed to update session state: {str(e)}"
        }, 500

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8081 (to avoid conflict with Juntoss Engine on 8080)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8081)))