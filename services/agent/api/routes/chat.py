from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Any, Dict, Union
import json
import asyncio
from datetime import datetime
from uuid import UUID
from dependencies import get_chat_workflow
from data.database import get_database
from data.repositories import ConversationRepository, MessageRepository
from api.schemas.requests import ChatRequest, CreateConversationRequest
from api.schemas.responses import (
    ChatResponse, ConversationResponse, ConversationDetailResponse, ErrorResponse
)

# Import LangChain types for better serialization handling
try:
    from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
    try:
        from pydantic import BaseModel as LangChainBaseModel
    except ImportError:
        from langchain_core.pydantic_v1 import BaseModel as LangChainBaseModel
except ImportError:
    # Fallback imports
    try:
        from langchain.schema.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
        from pydantic import BaseModel as LangChainBaseModel
    except ImportError:
        BaseMessage = None
        SystemMessage = None
        HumanMessage = None  
        AIMessage = None
        LangChainBaseModel = None

router = APIRouter()


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    db: Session = Depends(get_database)
):
    """Create a new conversation"""
    try:
        conversation_repo = ConversationRepository(db)
        conversation = conversation_repo.create_conversation(title=request.title)
        return conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    limit: int = 20,
    db: Session = Depends(get_database)
):
    """Get list of conversations"""
    try:
        conversation_repo = ConversationRepository(db)
        conversations = conversation_repo.get_conversations(limit=limit)
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_database)
):
    """Get conversation details with messages"""
    try:
        conversation_repo = ConversationRepository(db)
        message_repo = MessageRepository(db)
        
        conversation = conversation_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = message_repo.get_conversation_messages(conversation_id)
        
        return ConversationDetailResponse(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=messages
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: str,
    request: ChatRequest,
    workflow=Depends(get_chat_workflow),
    db: Session = Depends(get_database)
):
    """Send message to conversation"""
    try:
        conversation_repo = ConversationRepository(db)
        message_repo = MessageRepository(db)
        
        # Verify conversation exists
        conversation = conversation_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get existing messages for context
        existing_messages = message_repo.get_recent_messages(
            conversation_id, 
            limit=20
        )
        
        # Format messages for LangGraph state
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(existing_messages)  # Reverse to chronological order
        ]
        
        # Generate consistent session_id based on conversation_id
        session_id = f"session_{conversation_id}"
        
        # Execute workflow
        result = await workflow({
            "conversation_id": conversation_id,
            "session_id": session_id,
            "user_message": request.message,
            "existing_messages": formatted_messages
        })
        
        # Save messages to database
        messages_to_save = result["messages_to_save"]
        for message_data in messages_to_save:
            message_repo.create_message(
                conversation_id=conversation_id,
                role=message_data["role"],
                content=message_data["content"]
            )
        
        # Check if title was updated
        title_update_result = result.get("title_update_result", "")
        title_updated = "Título actualizado exitosamente" in title_update_result
        new_title = None
        
        if title_updated:
            # Extract title from result message
            if ": " in title_update_result:
                new_title = title_update_result.split(": ", 1)[1]
        
        return ChatResponse(
            response=result["assistant_response"],
            conversation_id=conversation_id,
            title_updated=title_updated,
            new_title=new_title
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_database)
):
    """Delete a conversation"""
    try:
        from data.models import (
            TramiteSession, UserProfile, ContactInfo, Address, 
            ValidatedIdentifier, ValidatedDocument, ChecklistItem
        )
        conversation_repo = ConversationRepository(db)
        
        conversation = conversation_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get all tramite sessions for this conversation
        tramite_sessions = db.query(TramiteSession).filter(
            TramiteSession.conversation_id == conversation_id
        ).all()
        
        # Delete all related data in the correct order (child to parent)
        for session in tramite_sessions:
            session_id = session.id
            
            # Delete user profile related data
            user_profile = db.query(UserProfile).filter(
                UserProfile.tramite_session_id == session_id
            ).first()
            
            if user_profile:
                profile_id = user_profile.id
                
                # Delete contact info, address, and validated identifiers
                db.query(ContactInfo).filter(ContactInfo.user_profile_id == profile_id).delete()
                db.query(Address).filter(Address.user_profile_id == profile_id).delete()
                db.query(ValidatedIdentifier).filter(ValidatedIdentifier.user_profile_id == profile_id).delete()
                
                # Delete user profile
                db.delete(user_profile)
            
            # Delete other session-related data
            db.query(ValidatedDocument).filter(ValidatedDocument.tramite_session_id == session_id).delete()
            db.query(ChecklistItem).filter(ChecklistItem.tramite_session_id == session_id).delete()
            
            # Finally delete the session
            db.delete(session)
        
        # Now delete the conversation (messages will be deleted automatically due to cascade)
        db.delete(conversation)
        db.commit()
        
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/stream")
async def stream_message(
    conversation_id: str,
    request: ChatRequest,
    workflow=Depends(get_chat_workflow),
    db: Session = Depends(get_database)
):
    """Stream agent reasoning and tool calls for debug mode"""
    
    async def generate_debug_stream():
        try:
            conversation_repo = ConversationRepository(db)
            message_repo = MessageRepository(db)
            
            # Verify conversation exists
            conversation = conversation_repo.get_conversation(conversation_id)
            if not conversation:
                yield f"data: {json.dumps({'error': 'Conversation not found'})}\n\n"
                return
            
            # Get existing messages for context
            existing_messages = message_repo.get_recent_messages(
                conversation_id, 
                limit=20
            )
            
            # Format messages for LangGraph state
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(existing_messages)  # Reverse to chronological order
            ]
            
            # Generate session ID
            session_id = f"session_{conversation_id}"
            
            # Prepare input for agent
            input_data = {
                "conversation_id": conversation_id,
                "session_id": session_id,
                "user_message": request.message,
                "existing_messages": formatted_messages
            }
            
            # Send initial debug event
            yield f"data: {json.dumps({'event': 'debug_start', 'data': {'conversation_id': conversation_id, 'session_id': session_id}})}\n\n"
            
            messages_to_save = []
            assistant_response = ""
            
            # Get the raw agent instead of the wrapper to use astream_events
            from agents.workflows.chat_agent import create_government_tramites_agent
            from agents.prompts.chat_prompts import GOVERNMENT_TRAMITES_SYSTEM_PROMPT
            
            base_agent = create_government_tramites_agent()
            
            # Prepare messages with system prompt
            messages = []
            messages.append({"role": "system", "content": GOVERNMENT_TRAMITES_SYSTEM_PROMPT})
            
            # Add conversation history
            for msg in formatted_messages[-10:]:  # Limit to last 10
                messages.append(msg)
            
            # Add current user message
            messages.append({"role": "user", "content": request.message})
            
            enhanced_input = {
                "messages": messages,
                "conversation_id": conversation_id,
                "session_id": session_id,
                "existing_messages": formatted_messages
            }
            
            # Stream agent events using astream_events v2
            async for event in base_agent.astream_events(enhanced_input, version="v2"):
                event_kind = event["event"]
                event_name = event.get("name", "")
                event_data = event.get("data", {})
                
                # Safely serialize event_data for debugging (convert LangChain objects)
                def make_serializable(obj: Any, max_depth: int = 5) -> Any:
                    """Convert LangChain objects and other complex types to JSON-serializable format"""
                    if max_depth <= 0:
                        return "<max_depth_reached>"
                    
                    # Handle None
                    if obj is None:
                        return None
                    
                    # Handle primitive types
                    if isinstance(obj, (str, int, float, bool)):
                        return obj
                    
                    # Handle datetime objects
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    
                    # Handle UUID objects
                    if isinstance(obj, UUID):
                        return str(obj)
                    
                    # Handle LangChain message objects (BaseMessage subclasses)
                    if BaseMessage and isinstance(obj, BaseMessage):
                        try:
                            result = {
                                'type': type(obj).__name__,
                                'content': getattr(obj, 'content', ''),
                            }
                            
                            # Add role mapping for common message types
                            if hasattr(obj, 'type'):
                                result['role'] = obj.type
                            else:
                                # Infer role from class name
                                class_name = type(obj).__name__.lower()
                                if 'system' in class_name:
                                    result['role'] = 'system'
                                elif 'human' in class_name or 'user' in class_name:
                                    result['role'] = 'user'
                                elif 'ai' in class_name or 'assistant' in class_name:
                                    result['role'] = 'assistant'
                                else:
                                    result['role'] = 'unknown'
                            
                            # Include additional kwargs if present
                            if hasattr(obj, 'additional_kwargs') and obj.additional_kwargs:
                                result['additional_kwargs'] = make_serializable(obj.additional_kwargs, max_depth - 1)
                            
                            # Include tool calls if present
                            if hasattr(obj, 'tool_calls') and obj.tool_calls:
                                result['tool_calls'] = make_serializable(obj.tool_calls, max_depth - 1)
                            
                            return result
                        except Exception as e:
                            return {'type': type(obj).__name__, 'content': str(obj), 'serialization_error': str(e)}
                    
                    # Handle objects with 'content' attribute (legacy support)
                    elif hasattr(obj, 'content'):
                        try:
                            return {
                                'type': type(obj).__name__,
                                'content': str(getattr(obj, 'content', '')),
                                'role': getattr(obj, 'type', 'unknown') if hasattr(obj, 'type') else type(obj).__name__.lower().replace('message', '')
                            }
                        except Exception as e:
                            return {'type': type(obj).__name__, 'content_error': str(e)}
                    
                    # Handle Pydantic objects (including LangChain models)
                    elif hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
                        try:
                            return make_serializable(obj.dict(), max_depth - 1)
                        except Exception as e:
                            # If dict() fails, try to get basic attributes
                            try:
                                if hasattr(obj, '__dict__'):
                                    return make_serializable(obj.__dict__, max_depth - 1)
                                else:
                                    return str(obj)
                            except:
                                return f"<pydantic_error: {str(e)}>"
                    
                    # Handle dictionaries
                    elif isinstance(obj, dict):
                        try:
                            return {str(k): make_serializable(v, max_depth - 1) for k, v in obj.items()}
                        except Exception as e:
                            return f"<dict_error: {str(e)}>"
                    
                    # Handle lists and tuples
                    elif isinstance(obj, (list, tuple)):
                        try:
                            return [make_serializable(item, max_depth - 1) for item in obj]
                        except Exception as e:
                            return f"<list_error: {str(e)}>"
                    
                    # Handle sets
                    elif isinstance(obj, set):
                        try:
                            return [make_serializable(item, max_depth - 1) for item in obj]
                        except Exception as e:
                            return f"<set_error: {str(e)}>"
                    
                    # Handle objects with __dict__
                    elif hasattr(obj, '__dict__'):
                        try:
                            return {
                                'type': type(obj).__name__,
                                'attributes': make_serializable(obj.__dict__, max_depth - 1)
                            }
                        except Exception as e:
                            return f"<object_error: {type(obj).__name__} - {str(e)}>"
                    
                    # Final fallback - convert to string
                    else:
                        try:
                            return str(obj)
                        except Exception as e:
                            return f"<str_error: {str(e)}>"
                
                serializable_data = make_serializable(event_data)
                
                # Send raw event for debugging
                try:
                    yield f"data: {json.dumps({'event': 'raw_event', 'data': {'kind': event_kind, 'name': event_name, 'raw': serializable_data}})}\n\n"
                except Exception as serialize_error:
                    # Fallback if serialization still fails
                    yield f"data: {json.dumps({'event': 'raw_event', 'data': {'kind': event_kind, 'name': event_name, 'raw': f'Serialization error: {str(serialize_error)}'}})}\n\n"
                
                # Process specific event types
                if event_kind == "on_chat_model_start":
                    yield f"data: {json.dumps({'event': 'reasoning_start', 'data': {'name': event_name}})}\n\n"
                    
                elif event_kind == "on_chat_model_stream":
                    # Handle different chunk formats
                    chunk = event_data.get("chunk", {})
                    content = ""
                    
                    if hasattr(chunk, 'content'):
                        content = chunk.content
                    elif isinstance(chunk, dict) and 'content' in chunk:
                        content = chunk['content']
                    elif isinstance(chunk, str):
                        content = chunk
                    
                    if content:
                        assistant_response += content
                        yield f"data: {json.dumps({'event': 'reasoning_token', 'data': {'content': content}})}\n\n"
                        
                elif event_kind == "on_chat_model_end":
                    yield f"data: {json.dumps({'event': 'reasoning_end', 'data': {'name': event_name}})}\n\n"
                    
                elif event_kind == "on_tool_start":
                    tool_input = make_serializable(event_data.get("input", {}))
                    yield f"data: {json.dumps({'event': 'tool_call_start', 'data': {'tool': event_name, 'input': tool_input}})}\n\n"
                    
                elif event_kind == "on_tool_end":
                    tool_output = make_serializable(event_data.get("output", {}))
                    yield f"data: {json.dumps({'event': 'tool_call_end', 'data': {'tool': event_name, 'output': tool_output}})}\n\n"
                    
                elif event_kind == "on_chain_start":
                    if event_name == "Agent":
                        chain_input = make_serializable(event_data.get('input', {}))
                        yield f"data: {json.dumps({'event': 'agent_start', 'data': {'input': chain_input}})}\n\n"
                        
                elif event_kind == "on_chain_end":
                    if event_name == "Agent":
                        chain_output = make_serializable(event_data.get('output', {}))
                        yield f"data: {json.dumps({'event': 'agent_end', 'data': {'output': chain_output}})}\n\n"
                        
                        # Try to extract final response from agent output
                        try:
                            output = event_data.get('output', {})
                            if isinstance(output, dict) and 'messages' in output:
                                # Look for the final AI message
                                messages = output['messages']
                                for msg in reversed(messages):
                                    if hasattr(msg, 'content'):
                                        # Check if this is an AI/Assistant message
                                        if (hasattr(msg, 'type') and msg.type in ['ai', 'assistant']) or \
                                           type(msg).__name__ in ['AIMessage', 'AssistantMessage']:
                                            if msg.content and not assistant_response:
                                                assistant_response = msg.content
                                            break
                        except Exception as e:
                            print(f"Warning: Could not extract final response from agent output: {e}")
                        
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
            
            # Extract final response from agent result if not captured from streaming
            if not assistant_response or assistant_response.strip() == "":
                print("Warning: No assistant response captured from streaming, using fallback")
                assistant_response = "Hola, soy tu consultor especializado en trámites del SAT. ¿En qué puedo ayudarte hoy?"
            
            # Prepare messages to save
            messages_to_save = [
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": assistant_response}
            ]
            
            # Save messages to database
            for message_data in messages_to_save:
                message_repo.create_message(
                    conversation_id=conversation_id,
                    role=message_data["role"],
                    content=message_data["content"]
                )
            
            # Send final response
            yield f"data: {json.dumps({'event': 'final_response', 'data': {'response': assistant_response, 'conversation_id': conversation_id}})}\n\n"
            yield f"data: {json.dumps({'event': 'debug_end'})}\n\n"
            
        except Exception as e:
            error_msg = f"Error in debug streaming: {str(e)}"
            yield f"data: {json.dumps({'event': 'error', 'data': {'message': error_msg}})}\n\n"
    
    return StreamingResponse(
        generate_debug_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )