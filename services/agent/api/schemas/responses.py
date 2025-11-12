from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[str] = None