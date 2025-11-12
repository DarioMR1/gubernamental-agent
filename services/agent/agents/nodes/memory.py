from typing import Dict, Any, List
from config import settings


async def load_conversation_history(state: Dict[str, Any]) -> Dict[str, Any]:
    """Load conversation history from state"""
    conversation_id = state.get("conversation_id")
    existing_messages = state.get("existing_messages", [])
    
    # Limit conversation history to prevent token overflow
    max_history = settings.max_conversation_history
    
    if existing_messages:
        # Take the most recent messages
        recent_messages = existing_messages[-max_history:] if len(existing_messages) > max_history else existing_messages
        state["conversation_history"] = recent_messages
    else:
        state["conversation_history"] = []
    
    return state


async def save_conversation_turn(state: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare conversation turn for saving"""
    user_message = state["user_message"]
    assistant_response = state["assistant_response"]
    conversation_id = state.get("conversation_id")
    
    # Prepare messages to be saved
    new_messages = [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": assistant_response}
    ]
    
    state["messages_to_save"] = new_messages
    
    return state