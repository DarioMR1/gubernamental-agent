import os
import sys
import asyncio
from typing import Any, Dict
import uuid

import vertexai
from absl import app, flags
from dotenv import load_dotenv
from vertexai.preview import reasoning_engines

from government_service_agent.agent import root_agent

FLAGS = flags.FLAGS
flags.DEFINE_string("user_id", "local_test_user", "User ID for session operations.")
flags.DEFINE_string("session_id", None, "Session ID for operations.")
flags.DEFINE_bool("create_session", False, "Creates a new local session.")
flags.DEFINE_bool("list_sessions", False, "Lists all local sessions for a user.")
flags.DEFINE_bool("get_session", False, "Gets a specific local session.")
flags.DEFINE_bool("send", False, "Sends a message to the local agent.")
flags.DEFINE_string(
    "message",
    "Necesito ayuda con el trámite de inscripción de RFC",
    "Message to send to the agent.",
)
flags.mark_bool_flags_as_mutual_exclusive(
    ["create_session", "list_sessions", "get_session", "send"]
)

# In-memory session storage for local testing
local_sessions: Dict[str, Dict[str, Any]] = {}


async def create_session_local(user_id: str) -> str:
    """Creates a new local session for the specified user."""
    session_id = str(uuid.uuid4())
    session_data = {
        "id": session_id,
        "user_id": user_id,
        "app_name": "Semovi Licencias Agent (Local)",
        "created_time": "local_testing",
        "last_update_time": "local_testing",
        "state": {}
    }
    
    if user_id not in local_sessions:
        local_sessions[user_id] = {}
    
    local_sessions[user_id][session_id] = session_data
    
    print("✅ Created local session:")
    print(f"  📋 Session ID: {session_id}")
    print(f"  👤 User ID: {user_id}")
    print(f"  🤖 App name: {session_data['app_name']}")
    print(f"\n💡 Use this session ID with --session_id when sending messages.")
    
    return session_id


def list_sessions_local(user_id: str) -> None:
    """Lists all local sessions for the specified user."""
    print(f"📋 Local sessions for user '{user_id}':")
    
    if user_id not in local_sessions or not local_sessions[user_id]:
        print("❌ No sessions found for this user.")
        return
        
    for session_id, session_data in local_sessions[user_id].items():
        print(f"  📋 Session ID: {session_id}")


def get_session_local(user_id: str, session_id: str) -> None:
    """Gets a specific local session."""
    print(f"Getting local session details for '{session_id}'...")
    
    if user_id not in local_sessions or session_id not in local_sessions[user_id]:
        print("❌ Session not found.")
        return
    
    session = local_sessions[user_id][session_id]
    print("📋 Local session details:")
    print(f"  ID: {session['id']}")
    print(f"  👤 User ID: {session['user_id']}")
    print(f"  🤖 App name: {session['app_name']}")
    print(f"  🕐 Created: {session['created_time']}")


async def send_message_local(user_id: str, session_id: str, message: str) -> None:
    """Sends a message to the local agent."""
    print(f"📤 Sending message to local session {session_id}:")
    print(f"💬 Message: {message}")
    print("\n🤖 Local Agent Response:")
    print("-" * 50)
    
    # Create a local AdkApp for testing
    local_app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=False,  # Disable for local testing
    )
    
    try:
        # Stream the response from the local agent
        async for event in local_app.async_stream_query(
            user_id=user_id,
            session_id=session_id,
            message=message,
        ):
            print(event)
    except Exception as e:
        print(f"❌ Error during local testing: {e}")
        print("💡 Make sure all dependencies are properly configured.")


def main(argv=None):
    """Main function that can be called directly or through app.run()."""
    # Parse flags first
    if argv is None:
        argv = flags.FLAGS(sys.argv)
    else:
        argv = flags.FLAGS(argv)

    load_dotenv()
    
    user_id = FLAGS.user_id
    
    print("🏠 Semovi Licencias Agent - Local Testing")
    print(f"👤 User ID: {user_id}")
    print()

    async def run_async_operations():
        if FLAGS.create_session:
            await create_session_local(user_id)
        elif FLAGS.list_sessions:
            list_sessions_local(user_id)
        elif FLAGS.get_session:
            if not FLAGS.session_id:
                print("❌ session_id is required for get_session")
                return
            get_session_local(user_id, FLAGS.session_id)
        elif FLAGS.send:
            if not FLAGS.session_id:
                print("❌ session_id is required for send")
                return
            await send_message_local(user_id, FLAGS.session_id, FLAGS.message)
        else:
            print("❌ Please specify one of: --create_session, --list_sessions, --get_session, or --send")

    # Run async operations
    asyncio.run(run_async_operations())


if __name__ == "__main__":
    app.run(main)