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
        
        # Generate proper UUID for session ID (industry standard)
        session_id = input_data.get("session_id") or str(uuid4())
        
        print(f"🔧 WORKFLOW DEBUG: Generated session_id={session_id} for conversation={conversation_id}")
        
        # IMPORTANT: Pre-create tramite session to ensure persistence with retry logic
        session_created = False
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                from agents.tools.conversation_state_tool import manage_conversation_state
                print(f"🔧 WORKFLOW DEBUG: Pre-creating tramite session (attempt {attempt + 1}/{max_retries})...")
                
                session_result = manage_conversation_state.invoke({
                    "action": "create",
                    "session_id": session_id,
                    "conversation_id": conversation_id,
                    "data": {"tramite_type": "SAT_RFC_INSCRIPCION_PF"}
                })
                
                session_created = session_result.get('success', False)
                print(f"🔧 WORKFLOW DEBUG: Session creation result: {session_created}")
                
                if session_created:
                    print(f"✅ WORKFLOW DEBUG: Session {session_id} created/verified successfully")
                    break
                else:
                    print(f"❌ WORKFLOW DEBUG: Session creation failed: {session_result.get('errors', [])}")
                    
            except Exception as e:
                print(f"⚠️ WORKFLOW DEBUG: Failed to pre-create session (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    print(f"💀 WORKFLOW DEBUG: All retry attempts failed. Session tools may auto-create if needed.")
        
        # Verify session exists by attempting to get state
        if session_created:
            try:
                verify_result = manage_conversation_state.invoke({
                    "action": "get_state",
                    "session_id": session_id,
                    "conversation_id": conversation_id
                })
                if verify_result.get('success'):
                    print(f"🔍 WORKFLOW DEBUG: Session verification successful")
                else:
                    print(f"⚠️ WORKFLOW DEBUG: Session verification failed: {verify_result.get('errors', [])}")
            except Exception as e:
                print(f"⚠️ WORKFLOW DEBUG: Failed to verify session: {e}")
        
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
        
        # Get current session state to provide context to the agent
        current_session_info = ""
        try:
            if session_created:
                verify_result = manage_conversation_state.invoke({
                    "action": "get_state",
                    "session_id": session_id,
                    "conversation_id": conversation_id
                })
                if verify_result.get('success'):
                    session_data = verify_result.get('data', {})
                    current_session_info = f"""
ESTADO ACTUAL DE LA SESIÓN:
- Tipo de trámite: {session_data.get('tramite_type', 'SAT_RFC_INSCRIPCION_PF')}
- Fase actual: {session_data.get('current_phase', 'WELCOME')}
- Progreso: {session_data.get('completion_percentage', 0)}%
- Perfil de usuario: {'Parcial' if session_data.get('user_profile') else 'Vacío'}
"""
        except Exception as e:
            print(f"⚠️ WORKFLOW DEBUG: Could not get session state for context: {e}")

        # Add session context to the agent's system prompt for tool usage
        system_prompt_with_context = f"""
{messages[0]['content'] if messages and messages[0]['role'] == 'system' else ''}

INFORMACIÓN DE SESIÓN CRÍTICA:
- session_id: {session_id}
- conversation_id: {conversation_id}
{current_session_info}

INSTRUCCIONES OBLIGATORIAS PARA HERRAMIENTAS:
1. SIEMPRE usa session_id="{session_id}" en manage_conversation_state
2. SIEMPRE usa conversation_id="{conversation_id}" en manage_conversation_state  
3. NUNCA inventes IDs diferentes
4. Si necesitas información del usuario, primero llama: manage_conversation_state(action="get_state", session_id="{session_id}", conversation_id="{conversation_id}")
5. Para guardar información nueva, usa: manage_conversation_state(action="update_profile", session_id="{session_id}", conversation_id="{conversation_id}", data=...)

IMPORTANTE: Estos IDs son exactos y deben usarse literalmente en todas las llamadas a herramientas.
"""
        
        if messages and messages[0]['role'] == 'system':
            messages[0]['content'] = system_prompt_with_context
        
        try:
            # Execute ReAct agent with detailed logging
            print(f"🤖 AGENT DEBUG: Starting ReAct execution for conversation {conversation_id}")
            print(f"📝 AGENT DEBUG: Messages in input: {len(enhanced_input['messages'])}")
            
            result = await base_agent.ainvoke(enhanced_input)
            
            print(f"✅ AGENT DEBUG: ReAct completed. Result keys: {result.keys() if isinstance(result, dict) else 'Not dict'}")
            
            if "messages" in result:
                print(f"📨 AGENT DEBUG: Found {len(result['messages'])} messages in result")
                for i, msg in enumerate(result["messages"]):
                    msg_type = str(type(msg).__name__)
                    content_preview = getattr(msg, 'content', str(msg))[:100] if hasattr(msg, 'content') else str(msg)[:100]
                    print(f"📨 AGENT DEBUG: Message {i}: {msg_type} - {content_preview}...")
                    
                    # Log tool calls and reasoning
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            print(f"🔧 TOOL CALL: {tool_call.get('name', 'unknown')} with args: {tool_call.get('args', {})}")
                    
                    # Log additional message data for debugging
                    if hasattr(msg, 'additional_kwargs'):
                        print(f"📎 AGENT DEBUG: Additional data: {msg.additional_kwargs}")
            
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
                            print(f"💬 AGENT DEBUG: Extracted final response: {assistant_response[:200]}...")
                            break
                    # Handle dictionary messages as fallback
                    elif isinstance(msg, dict) and msg.get("role") in ["ai", "assistant"]:
                        assistant_response = msg.get("content", "")
                        print(f"💬 AGENT DEBUG: Extracted dict response: {assistant_response[:200]}...")
                        break
            
            if not assistant_response:
                assistant_response = "Hola, soy tu consultor especializado en trámites del SAT. ¿En qué puedo ayudarte hoy?"
                print(f"⚠️ AGENT DEBUG: Using fallback response")
            
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