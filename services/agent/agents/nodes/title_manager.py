from typing import Dict, Any
from agents.tools.title_updater import update_conversation_title, analyze_and_update_title


async def update_title_intelligently(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Intelligently updates conversation title based on context and message content.
    
    This function:
    1. For new conversations: Creates initial title
    2. For existing conversations: Analyzes if title needs updating based on context
    """
    conversation_id = state.get("conversation_id")
    user_message = state.get("user_message")
    existing_messages = state.get("existing_messages", [])
    
    if not conversation_id or not user_message:
        state["title_update_result"] = "Title update skipped: missing data"
        return state
    
    try:
        # Create conversation context from recent messages
        context_messages = []
        if existing_messages:
            # Get last 4 messages for context (2 exchanges)
            recent_messages = existing_messages[-4:] if len(existing_messages) > 4 else existing_messages
            context_messages = [
                f"{msg['role'].title()}: {msg['content']}" 
                for msg in recent_messages
            ]
        
        conversation_context = "\n".join(context_messages) if context_messages else "Nueva conversación"
        
        # Use intelligent analysis tool
        result = analyze_and_update_title.invoke({
            "conversation_id": conversation_id,
            "user_message": user_message,
            "conversation_context": conversation_context
        })
        
        # Add the result to state for logging/debugging
        state["title_update_result"] = result
        
    except Exception as e:
        # Don't fail the whole conversation if title update fails
        state["title_update_result"] = f"Title analysis failed: {str(e)}"
    
    return state


# Keep the old function for backward compatibility
async def update_title_if_needed(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy function - delegates to intelligent title updater.
    """
    return await update_title_intelligently(state)