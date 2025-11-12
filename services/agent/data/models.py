from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float, Date, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional

# Use timezone-aware datetime
def utc_now():
    return datetime.now()

Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationship
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    tramite_sessions = relationship("TramiteSession", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    
    # Relationship
    conversation = relationship("Conversation", back_populates="messages")


class TramiteSession(Base):
    __tablename__ = "tramite_sessions"
    
    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    tramite_type = Column(String(50), nullable=False)  # TramiteType enum
    current_phase = Column(String(50), nullable=False)  # ConversationPhase enum
    completion_percentage = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    preferred_modality = Column(String(20), nullable=True)  # TramiteModality enum
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="tramite_sessions")
    user_profile = relationship("UserProfile", back_populates="tramite_session", uselist=False)
    validated_documents = relationship("ValidatedDocument", back_populates="tramite_session")
    checklist_items = relationship("ChecklistItem", back_populates="tramite_session")


class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    tramite_session_id = Column(String, ForeignKey("tramite_sessions.id"), nullable=False)
    full_name = Column(String(200), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    mother_last_name = Column(String(100), nullable=True)
    birth_date = Column(Date, nullable=True)
    nationality = Column(String(50), default="mexicana")
    is_minor = Column(Boolean, default=False)
    has_legal_representative = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    tramite_session = relationship("TramiteSession", back_populates="user_profile")
    contact_info = relationship("ContactInfo", back_populates="user_profile", uselist=False)
    address = relationship("Address", back_populates="user_profile", uselist=False)
    validated_identifiers = relationship("ValidatedIdentifier", back_populates="user_profile")


class ContactInfo(Base):
    __tablename__ = "contact_info"
    
    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    alternative_phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationship
    user_profile = relationship("UserProfile", back_populates="contact_info")


class Address(Base):
    __tablename__ = "addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    street = Column(String(200), nullable=True)
    exterior_number = Column(String(20), nullable=True)
    interior_number = Column(String(20), nullable=True)
    neighborhood = Column(String(100), nullable=True)
    postal_code = Column(String(10), nullable=True)
    municipality = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), default="México")
    is_fiscal_address = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationship
    user_profile = relationship("UserProfile", back_populates="address")


class ValidatedIdentifier(Base):
    __tablename__ = "validated_identifiers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    identifier_type = Column(String(50), nullable=False)  # IdentifierType enum
    value = Column(String(50), nullable=False)
    is_valid = Column(Boolean, nullable=False)
    validation_score = Column(Float, nullable=False)
    extracted_data = Column(JSON, nullable=True)
    validation_errors = Column(JSON, nullable=True)
    validated_at = Column(DateTime, default=utc_now)
    
    # Relationship
    user_profile = relationship("UserProfile", back_populates="validated_identifiers")


class ValidatedDocument(Base):
    __tablename__ = "validated_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    tramite_session_id = Column(String, ForeignKey("tramite_sessions.id"), nullable=False)
    document_type = Column(String(50), nullable=False)  # DocumentType enum
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    validation_score = Column(Float, nullable=False)
    confidence_level = Column(String(20), nullable=False)  # ConfidenceLevel enum
    validation_errors = Column(JSON, nullable=True)
    expiry_date = Column(Date, nullable=True)
    is_valid = Column(Boolean, nullable=False)
    validated_at = Column(DateTime, default=utc_now)
    
    # Relationship
    tramite_session = relationship("TramiteSession", back_populates="validated_documents")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    tramite_session_id = Column(String, ForeignKey("tramite_sessions.id"), nullable=False)
    requirement_id = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False)  # RequirementStatus enum
    is_mandatory = Column(Boolean, default=True)
    validation_notes = Column(JSON, nullable=True)
    help_text = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationship
    tramite_session = relationship("TramiteSession", back_populates="checklist_items")