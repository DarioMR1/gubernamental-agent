from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from dependencies import get_chat_workflow
from data.database import get_database
from data.repositories import ConversationRepository, MessageRepository
from api.schemas.requests import ChatRequest, CreateConversationRequest
from api.schemas.responses import (
    ChatResponse, ConversationResponse, ConversationDetailResponse, ErrorResponse
)

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
        
        # Execute workflow
        result = await workflow.ainvoke({
            "conversation_id": conversation_id,
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
        conversation_repo = ConversationRepository(db)
        
        conversation = conversation_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        db.delete(conversation)
        db.commit()
        
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))