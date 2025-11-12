from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date


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
    title_updated: bool = False
    new_title: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[str] = None


class TramiteSessionResponse(BaseModel):
    session_id: str
    conversation_id: str
    tramite_type: str
    current_phase: str
    completion_percentage: float
    is_completed: bool
    created_at: datetime


class TramiteSessionDetailResponse(TramiteSessionResponse):
    user_profile: Optional[Dict[str, Any]] = None
    validated_documents: List[Dict[str, Any]] = []
    checklist: List[Dict[str, Any]] = []
    updated_at: Optional[datetime] = None


class ValidationResponse(BaseModel):
    is_valid: bool
    confidence_score: float
    confidence_level: str
    extracted_data: Dict[str, Any] = {}
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []


class ProfileResponse(BaseModel):
    updated_fields: List[str]
    success: bool
    message: str


class RequirementResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str
    is_mandatory: bool
    validation_notes: List[str] = []
    help_text: Optional[str] = None


class NextStepResponse(BaseModel):
    step_number: int
    title: str
    description: str
    estimated_time: Optional[str] = None
    url: Optional[str] = None


class ChecklistResponse(BaseModel):
    checklist: List[RequirementResponse]
    completion_percentage: float
    next_steps: List[NextStepResponse]
    preferred_modality: str
    warnings: List[str] = []
    estimated_time: str
    generated_at: str


class DocumentUploadResponse(BaseModel):
    document_id: str
    document_type: str
    upload_status: str
    file_size: int
    validation_result: Optional[ValidationResponse] = None


class ExplanationResponse(BaseModel):
    tramite_type: str
    requirement: str
    explanation: str
    legal_basis: str
    practical_guidance: List[str] = []
    common_errors: List[str] = []
    alternatives: List[str] = []
    estimated_time: str
    related_requirements: List[str] = []


class TramiteSummaryResponse(BaseModel):
    session_id: str
    tramite_type: str
    completion_percentage: float
    ready_for_execution: bool
    modality: str
    summary_data: Dict[str, Any]
    next_steps: List[NextStepResponse]
    warnings: List[str] = []
    estimated_completion_time: str