from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date
from domain_types.tramite_types import TramiteType, DocumentType


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message content")


class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200, description="Optional conversation title")


class CreateTramiteSessionRequest(BaseModel):
    tramite_type: TramiteType = Field(..., description="Type of government procedure")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID to link")
    
    @validator('tramite_type')
    def validate_tramite_type(cls, v):
        if v not in [tt.value for tt in TramiteType]:
            raise ValueError(f"Invalid tramite type. Must be one of: {[tt.value for tt in TramiteType]}")
        return v


class ValidateCurpRequest(BaseModel):
    curp: str = Field(..., min_length=18, max_length=18, description="CURP to validate (18 characters)")
    
    @validator('curp')
    def validate_curp_format(cls, v):
        v = v.upper().strip()
        if len(v) != 18:
            raise ValueError("CURP must be exactly 18 characters")
        if not v.isalnum():
            raise ValueError("CURP must contain only letters and numbers")
        return v


class ValidateDocumentRequest(BaseModel):
    document_type: DocumentType = Field(..., description="Type of document to validate")
    tramite_context: Optional[dict] = Field(None, description="Additional context for validation")


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, max_length=200, description="Complete full name")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name (apellido paterno)")
    mother_last_name: Optional[str] = Field(None, max_length=100, description="Mother's last name (apellido materno)")
    birth_date: Optional[date] = Field(None, description="Date of birth")
    nationality: Optional[str] = Field("mexicana", max_length=50, description="Nationality")
    email: Optional[str] = Field(None, description="Email address for SAT notifications")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    
    @validator('email')
    def validate_email(cls, v):
        if v is not None:
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, v):
                raise ValueError("Invalid email format")
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            # Basic phone validation (remove spaces and special chars for validation)
            clean_phone = ''.join(filter(str.isdigit, v))
            if len(clean_phone) < 10 or len(clean_phone) > 15:
                raise ValueError("Phone number must be between 10 and 15 digits")
        return v


class UpdateAddressRequest(BaseModel):
    street: Optional[str] = Field(None, max_length=200, description="Street address")
    exterior_number: Optional[str] = Field(None, max_length=20, description="Exterior number")
    interior_number: Optional[str] = Field(None, max_length=20, description="Interior number")
    neighborhood: Optional[str] = Field(None, max_length=100, description="Neighborhood (colonia)")
    postal_code: Optional[str] = Field(None, max_length=10, description="Postal code (código postal)")
    municipality: Optional[str] = Field(None, max_length=100, description="Municipality (municipio)")
    state: Optional[str] = Field(None, max_length=100, description="State (estado)")
    is_fiscal_address: bool = Field(True, description="Is this the fiscal address")
    
    @validator('postal_code')
    def validate_postal_code(cls, v):
        if v is not None:
            clean_cp = ''.join(filter(str.isdigit, v))
            if len(clean_cp) != 5:
                raise ValueError("Postal code must be exactly 5 digits")
            return clean_cp
        return v


class DeclareEconomicActivityRequest(BaseModel):
    activity_types: list[str] = Field(..., description="Types of economic activities")
    expected_annual_income: Optional[float] = Field(None, ge=0, description="Expected annual income in MXN")
    has_employees: bool = Field(False, description="Will have employees")
    will_issue_invoices: bool = Field(False, description="Will issue invoices/facturas")
    additional_notes: Optional[str] = Field(None, max_length=500, description="Additional notes about activities")