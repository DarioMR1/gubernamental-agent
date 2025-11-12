from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import uuid4
from data.models import Conversation, Message


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(self, title: Optional[str] = None) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            id=str(uuid4()),
            title=title
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
    
    def get_conversations(self, limit: int = 20) -> List[Conversation]:
        """Get list of recent conversations"""
        return self.db.query(Conversation).order_by(
            desc(Conversation.updated_at)
        ).limit(limit).all()


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_message(
        self, 
        conversation_id: str, 
        role: str, 
        content: str
    ) -> Message:
        """Create a new message"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_conversation_messages(
        self, 
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get messages for a conversation"""
        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_recent_messages(
        self, 
        conversation_id: str, 
        limit: int = 10
    ) -> List[Message]:
        """Get recent messages for context"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at)).limit(limit).all()