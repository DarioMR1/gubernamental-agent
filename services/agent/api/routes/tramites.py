from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from dependencies import get_chat_workflow
from data.database import get_database
from data.repositories import ConversationRepository, MessageRepository
from data.models import TramiteSession, UserProfile, ValidatedDocument, ChecklistItem
from api.schemas.requests import (
    CreateTramiteSessionRequest, 
    ValidateCurpRequest,
    ValidateDocumentRequest,
    UpdateProfileRequest,
    UpdateAddressRequest
)
from api.schemas.responses import (
    TramiteSessionResponse,
    ValidationResponse,
    ChecklistResponse,
    ProfileResponse,
    TramiteSessionDetailResponse,
    ErrorResponse
)
from domain_types.tramite_types import TramiteType, DocumentType
from config import settings

router = APIRouter()


@router.post("/sessions", response_model=TramiteSessionResponse)
async def create_tramite_session(
    request: CreateTramiteSessionRequest,
    db: Session = Depends(get_database)
):
    """Create a new tramite session"""
    try:
        # Create conversation first if needed
        conversation_repo = ConversationRepository(db)
        
        if request.conversation_id:
            conversation = conversation_repo.get_conversation(request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            conversation = conversation_repo.create_conversation(
                title=f"Trámite: {request.tramite_type}"
            )
        
        # Check if tramite session already exists
        existing_session = db.query(TramiteSession).filter(
            TramiteSession.conversation_id == conversation.id,
            TramiteSession.tramite_type == request.tramite_type
        ).first()
        
        if existing_session:
            return TramiteSessionResponse(
                session_id=existing_session.id,
                conversation_id=existing_session.conversation_id,
                tramite_type=existing_session.tramite_type,
                current_phase=existing_session.current_phase,
                completion_percentage=existing_session.completion_percentage,
                is_completed=existing_session.is_completed,
                created_at=existing_session.created_at
            )
        
        # Create new tramite session
        from uuid import uuid4
        session_id = f"tramite_{uuid4().hex[:12]}"
        
        new_session = TramiteSession(
            id=session_id,
            conversation_id=conversation.id,
            tramite_type=request.tramite_type,
            current_phase="welcome"
        )
        
        db.add(new_session)
        
        # Create empty user profile
        user_profile = UserProfile(
            tramite_session_id=session_id,
            nationality="mexicana"
        )
        
        db.add(user_profile)
        db.commit()
        
        return TramiteSessionResponse(
            session_id=session_id,
            conversation_id=conversation.id,
            tramite_type=request.tramite_type,
            current_phase=new_session.current_phase,
            completion_percentage=0.0,
            is_completed=False,
            created_at=new_session.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=TramiteSessionDetailResponse)
async def get_tramite_session(
    session_id: str,
    db: Session = Depends(get_database)
):
    """Get tramite session details"""
    try:
        session = db.query(TramiteSession).filter(
            TramiteSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Tramite session not found")
        
        # Get user profile
        profile_data = None
        if session.user_profile:
            profile = session.user_profile
            profile_data = {
                "full_name": profile.full_name,
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "birth_date": profile.birth_date,
                "nationality": profile.nationality,
                "contact_info": {
                    "email": profile.contact_info.email if profile.contact_info else None,
                    "phone": profile.contact_info.phone if profile.contact_info else None
                } if profile.contact_info else None,
                "address": {
                    "street": profile.address.street if profile.address else None,
                    "postal_code": profile.address.postal_code if profile.address else None,
                    "municipality": profile.address.municipality if profile.address else None,
                    "state": profile.address.state if profile.address else None
                } if profile.address else None
            }
        
        # Get validated documents
        documents = []
        for doc in session.validated_documents:
            documents.append({
                "document_type": doc.document_type,
                "is_valid": doc.is_valid,
                "confidence_level": doc.confidence_level,
                "validated_at": doc.validated_at
            })
        
        # Get checklist items
        checklist = []
        for item in session.checklist_items:
            checklist.append({
                "requirement_id": item.requirement_id,
                "name": item.name,
                "status": item.status,
                "is_mandatory": item.is_mandatory
            })
        
        return TramiteSessionDetailResponse(
            session_id=session.id,
            conversation_id=session.conversation_id,
            tramite_type=session.tramite_type,
            current_phase=session.current_phase,
            completion_percentage=session.completion_percentage,
            is_completed=session.is_completed,
            user_profile=profile_data,
            validated_documents=documents,
            checklist=checklist,
            created_at=session.created_at,
            updated_at=session.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/validate-curp", response_model=ValidationResponse)
async def validate_curp(
    session_id: str,
    request: ValidateCurpRequest,
    workflow=Depends(get_chat_workflow),
    db: Session = Depends(get_database)
):
    """Validate CURP for tramite session"""
    try:
        # Check if session exists
        session = db.query(TramiteSession).filter(
            TramiteSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Tramite session not found")
        
        # Use agent tools to validate CURP
        from agents.tools.identifier_validation_tool import validate_official_identifier
        
        validation_result = validate_official_identifier(
            identifier_type="curp",
            value=request.curp,
            session_id=session_id
        )
        
        # Update user profile if CURP is valid
        if validation_result.get("is_valid") and session.user_profile:
            extracted_data = validation_result.get("extracted_data", {})
            profile = session.user_profile
            
            # Extract name components if available
            if "apellido_paterno" in extracted_data and "apellido_materno" in extracted_data:
                profile.last_name = extracted_data["apellido_paterno"]
                profile.mother_last_name = extracted_data["apellido_materno"]
            
            # Extract birth date if available
            if "fecha_nacimiento_parsed" in extracted_data:
                from datetime import datetime
                profile.birth_date = datetime.fromisoformat(extracted_data["fecha_nacimiento_parsed"]).date()
            
            db.commit()
        
        return ValidationResponse(
            is_valid=validation_result.get("is_valid", False),
            confidence_score=validation_result.get("confidence_score", 0.0),
            confidence_level=validation_result.get("confidence_level", "very_low"),
            extracted_data=validation_result.get("extracted_data", {}),
            errors=validation_result.get("errors", []),
            warnings=validation_result.get("warnings", []),
            suggestions=validation_result.get("suggestions", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/validate-document", response_model=ValidationResponse)
async def validate_document(
    session_id: str,
    document_type: DocumentType,
    file: UploadFile = File(...),
    db: Session = Depends(get_database)
):
    """Validate uploaded document for tramite session"""
    try:
        # Check if session exists
        session = db.query(TramiteSession).filter(
            TramiteSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Tramite session not found")
        
        # Validate file format
        if file.content_type not in settings.supported_document_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Supported: {settings.supported_document_formats}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Check file size
        if len(file_content) > settings.max_document_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_document_size_mb}MB"
            )
        
        # Use agent tools to validate document
        from agents.tools.document_validation_tool import validate_government_document
        
        # Convert file content to base64 for processing
        import base64
        file_data_b64 = base64.b64encode(file_content).decode()
        
        validation_result = validate_government_document(
            document_type=document_type.value,
            file_data=file_data_b64,
            session_id=session_id,
            tramite_context={"file_name": file.filename, "content_type": file.content_type}
        )
        
        return ValidationResponse(
            is_valid=validation_result.get("is_valid", False),
            confidence_score=validation_result.get("confidence_score", 0.0),
            confidence_level=validation_result.get("confidence_level", "very_low"),
            extracted_data=validation_result.get("extracted_data", {}),
            errors=validation_result.get("errors", []),
            warnings=validation_result.get("warnings", []),
            suggestions=validation_result.get("suggestions", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/update-profile", response_model=ProfileResponse)
async def update_profile(
    session_id: str,
    request: UpdateProfileRequest,
    db: Session = Depends(get_database)
):
    """Update user profile for tramite session"""
    try:
        # Use agent tools to update profile
        from agents.tools.conversation_state_tool import manage_conversation_state
        
        # Get session to find conversation_id
        session = db.query(TramiteSession).filter(
            TramiteSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Tramite session not found")
        
        profile_data = {}
        if request.full_name:
            profile_data["full_name"] = request.full_name
        if request.first_name:
            profile_data["first_name"] = request.first_name
        if request.last_name:
            profile_data["last_name"] = request.last_name
        if request.mother_last_name:
            profile_data["mother_last_name"] = request.mother_last_name
        if request.birth_date:
            profile_data["birth_date"] = request.birth_date
        if request.email:
            profile_data["contact_info"] = {"email": request.email}
        if request.phone:
            profile_data.setdefault("contact_info", {})["phone"] = request.phone
        
        result = manage_conversation_state(
            action="update_profile",
            session_id=session_id,
            conversation_id=session.conversation_id,
            data={"profile_data": profile_data}
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("errors", ["Update failed"]))
        
        return ProfileResponse(
            updated_fields=result.get("data", {}).get("updated_fields", []),
            success=True,
            message="Profile updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/checklist", response_model=ChecklistResponse)
async def get_tramite_checklist(
    session_id: str,
    db: Session = Depends(get_database)
):
    """Generate checklist for tramite session"""
    try:
        # Get session
        session = db.query(TramiteSession).filter(
            TramiteSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Tramite session not found")
        
        # Use agent tools to generate checklist
        from agents.tools.tramite_checklist_tool import generate_tramite_checklist
        
        # Get current documents
        current_documents = []
        for doc in session.validated_documents:
            current_documents.append({
                "document_type": doc.document_type,
                "is_valid": doc.is_valid,
                "validation_score": doc.validation_score
            })
        
        result = generate_tramite_checklist(
            tramite_type=session.tramite_type,
            session_id=session_id,
            current_documents=current_documents
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("errors", ["Checklist generation failed"]))
        
        return ChecklistResponse(
            checklist=result.get("checklist", []),
            completion_percentage=result.get("completion_percentage", 0.0),
            next_steps=result.get("next_steps", []),
            preferred_modality=result.get("preferred_modality", "online"),
            warnings=result.get("warnings", []),
            estimated_time=result.get("estimated_time", ""),
            generated_at=result.get("generated_at", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_tramite_session(
    session_id: str,
    db: Session = Depends(get_database)
):
    """Delete a tramite session"""
    try:
        session = db.query(TramiteSession).filter(
            TramiteSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Tramite session not found")
        
        db.delete(session)
        db.commit()
        
        return {"message": "Tramite session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))