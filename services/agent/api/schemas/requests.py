from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message content")


class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200, description="Optional conversation title")