from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any, Optional
from agents.nodes.conversation import generate_response
from agents.nodes.memory import load_conversation_history, save_conversation_turn
from agents.nodes.title_manager import update_title_if_needed


class ChatState(TypedDict):
    conversation_id: Optional[str]
    user_message: str
    assistant_response: str
    conversation_history: List[Dict[str, str]]
    existing_messages: List[Dict[str, str]]
    messages_to_save: List[Dict[str, str]]
    title_update_result: Optional[str]


def create_chat_workflow():
    """Create chat workflow graph"""
    workflow = StateGraph(ChatState)
    
    # Add nodes
    workflow.add_node("load_history", load_conversation_history)
    workflow.add_node("update_title", update_title_if_needed)
    workflow.add_node("generate", generate_response)
    workflow.add_node("save_turn", save_conversation_turn)
    
    # Define the flow
    workflow.set_entry_point("load_history")
    workflow.add_edge("load_history", "update_title")
    workflow.add_edge("update_title", "generate")
    workflow.add_edge("generate", "save_turn")
    workflow.add_edge("save_turn", END)
    
    return workflow