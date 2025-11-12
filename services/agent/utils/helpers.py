from typing import List, Dict, Any
from datetime import datetime


def format_conversation_history(messages: List[Dict[str, Any]]) -> str:
    """Format conversation history for display"""
    if not messages:
        return "No previous messages."
    
    formatted = []
    for message in messages:
        role = message["role"].title()
        content = message["content"]
        formatted.append(f"{role}: {content}")
    
    return "\n".join(formatted)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def generate_conversation_title(first_message: str, max_length: int = 50) -> str:
    """Generate conversation title from first message"""
    title = truncate_text(first_message, max_length)
    return title or "New Conversation"