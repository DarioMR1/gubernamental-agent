from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
from agents.tools import (
    manage_conversation_state,
    validate_official_identifier,
    validate_government_document, 
    generate_tramite_checklist,
    explain_requirement
)
from agents.prompts.chat_prompts import GOVERNMENT_TRAMITES_SYSTEM_PROMPT
from config import settings
from uuid import uuid4


def create_government_tramites_agent():
    """Create ReAct agent for government procedures"""
    
    # Initialize LLM
    llm = ChatOpenAI(
        model=settings.model_name,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        openai_api_key=settings.openai_api_key
    )
    
    # Define specialized tools for government procedures
    government_tools = [
        manage_conversation_state,
        validate_official_identifier,
        validate_government_document,
        generate_tramite_checklist,
        explain_requirement
    ]
    
    # Create ReAct agent with specialized tools
    # The system prompt should be passed through messages, not as a parameter
    agent = create_react_agent(
        model=llm,
        tools=government_tools
    )
    
    return agent


def create_enhanced_agent_with_state():
    """Create agent wrapper that manages conversation state"""
    
    base_agent = create_government_tramites_agent()
    
    async def enhanced_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced agent that handles state management"""
        
        conversation_id = input_data.get("conversation_id")
        user_message = input_data.get("user_message", "")
        existing_messages = input_data.get("existing_messages", [])
        
        # Generate unique session ID for tramite tracking
        session_id = input_data.get("session_id") or f"tramite_{uuid4().hex[:8]}"
        
        # Prepare input for ReAct agent with system prompt
        # Include system prompt and conversation history
        messages = []
        
        # Add system prompt as the first message
        messages.append({"role": "system", "content": GOVERNMENT_TRAMITES_SYSTEM_PROMPT})
        
        # Add conversation history
        for msg in existing_messages[-10:]:  # Limit history to last 10 messages
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        enhanced_input = {
            "messages": messages,
            # Context that tools can access
            "conversation_id": conversation_id,
            "session_id": session_id,
            "existing_messages": existing_messages
        }
        
        try:
            # Execute ReAct agent
            result = await base_agent.ainvoke(enhanced_input)
            
            # Extract assistant response from agent result
            assistant_response = ""
            if "messages" in result and result["messages"]:
                # Get the last AI message
                for msg in reversed(result["messages"]):
                    # Handle LangChain message objects
                    if hasattr(msg, 'content'):
                        # This is a LangChain message object (AIMessage, HumanMessage, etc.)
                        if hasattr(msg, 'type') and msg.type in ['ai', 'assistant'] or str(type(msg).__name__) == 'AIMessage':
                            assistant_response = msg.content
                            break
                    # Handle dictionary messages as fallback
                    elif isinstance(msg, dict) and msg.get("role") in ["ai", "assistant"]:
                        assistant_response = msg.get("content", "")
                        break
            
            if not assistant_response:
                assistant_response = "Hola, soy tu consultor especializado en trámites del SAT. ¿En qué puedo ayudarte hoy?"
            
            # Prepare messages to save
            messages_to_save = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_response}
            ]
            
            return {
                "conversation_id": conversation_id,
                "session_id": session_id,
                "user_message": user_message,
                "assistant_response": assistant_response,
                "messages_to_save": messages_to_save,
                "existing_messages": existing_messages,
                "conversation_history": existing_messages + messages_to_save,
                "title_update_result": "Conversación de trámites gubernamentales"
            }
            
        except Exception as e:
            # Log error for debugging
            print(f"Error in enhanced_agent: {str(e)}")
            
            # Fallback response
            error_response = "Disculpa, tuve un problema técnico. Como consultor de trámites del SAT, puedo ayudarte con la inscripción al RFC. ¿Podrías repetir tu consulta?"
            
            return {
                "conversation_id": conversation_id,
                "session_id": session_id,
                "user_message": user_message,
                "assistant_response": error_response,
                "messages_to_save": [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": error_response}
                ],
                "existing_messages": existing_messages,
                "conversation_history": existing_messages + [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": error_response}
                ],
                "title_update_result": ""
            }
    
    return enhanced_agent


# For backward compatibility with existing API
def create_chat_workflow():
    """Create chat workflow using ReAct agent (backward compatibility)"""
    return create_enhanced_agent_with_state()