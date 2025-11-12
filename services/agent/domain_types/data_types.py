from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from .validation_types import ValidationStatus, RequirementStatus, ConfidenceLevel
from .tramite_types import DocumentType, IdentifierType, TramiteType, TramiteModality


@dataclass
class ValidatedIdentifier:
    """Validated official identifier (CURP, RFC, etc.)"""
    identifier_type: IdentifierType
    value: str
    is_valid: bool
    validation_score: float
    extracted_data: Dict[str, Any]
    validation_errors: List[str]
    validated_at: datetime


@dataclass
class ValidatedDocument:
    """Validated government document"""
    document_type: DocumentType
    file_data: Optional[bytes]
    file_name: Optional[str]
    extracted_data: Dict[str, Any]
    validation_score: float
    confidence_level: ConfidenceLevel
    validation_errors: List[str]
    expiry_date: Optional[date]
    is_valid: bool
    validated_at: datetime


@dataclass
class Address:
    """Address information"""
    street: Optional[str] = None
    exterior_number: Optional[str] = None
    interior_number: Optional[str] = None
    neighborhood: Optional[str] = None
    postal_code: Optional[str] = None
    municipality: Optional[str] = None
    state: Optional[str] = None
    country: str = "México"
    is_fiscal_address: bool = False


@dataclass
class ContactInfo:
    """Contact information"""
    email: Optional[str] = None
    phone: Optional[str] = None
    alternative_phone: Optional[str] = None


@dataclass
class UserProfile:
    """Complete user profile for tramite"""
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mother_last_name: Optional[str] = None
    birth_date: Optional[date] = None
    nationality: str = "mexicana"
    curp: Optional[ValidatedIdentifier] = None
    rfc: Optional[ValidatedIdentifier] = None
    address: Optional[Address] = None
    contact_info: Optional[ContactInfo] = None
    is_minor: bool = False
    has_legal_representative: bool = False


@dataclass
class Requirement:
    """Individual requirement for a tramite"""
    id: str
    name: str
    description: str
    status: RequirementStatus
    is_mandatory: bool
    validation_notes: List[str]
    help_text: Optional[str] = None


@dataclass
class NextStep:
    """Next steps for completing the tramite"""
    step_number: int
    title: str
    description: str
    estimated_time: Optional[timedelta] = None
    url: Optional[str] = None


@dataclass
class TramiteChecklist:
    """Complete checklist for a tramite"""
    tramite_type: TramiteType
    requirements: List[Requirement]
    completion_percentage: float
    next_steps: List[NextStep]
    estimated_total_time: timedelta
    preferred_modality: TramiteModality
    warnings: List[str]
    generated_at: datetime


@dataclass
class ConversationState:
    """State of the tramite conversation"""
    session_id: str
    tramite_type: Optional[TramiteType]
    user_profile: UserProfile
    validated_documents: List[ValidatedDocument]
    conversation_phase: str
    checklist: Optional[TramiteChecklist]
    session_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class ValidationResult:
    """Result of any validation operation"""
    is_valid: bool
    status: ValidationStatus
    confidence_score: float
    confidence_level: ConfidenceLevel
    errors: List[str]
    warnings: List[str]
    extracted_data: Dict[str, Any]
    suggestions: List[str]
    validated_at: datetime