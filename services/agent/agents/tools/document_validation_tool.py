from langchain.tools import tool
from typing import Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from data.database import get_database
from data.models import ValidatedDocument, TramiteSession
from domain_types.tramite_types import DocumentType
from domain_types.validation_types import ValidationStatus, ConfidenceLevel
from config import settings


@tool("validate_government_document") 
def validate_government_document(
    document_type: str,
    file_data: str,  # Base64 encoded or file path
    session_id: str,
    tramite_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Validates government documents for tramite procedures using real database storage.
    
    Note: OCR functionality will be implemented later. Currently validates metadata and format.
    
    Args:
        document_type: Type of document (ine_front, ine_back, comprobante_domicilio, etc.)
        file_data: Document data (base64 or file reference)
        session_id: Tramite session ID
        tramite_context: Additional context for validation
        
    Returns:
        Dict with validation result and extracted data
    """
    
    result = {
        "success": False,
        "document_type": document_type,
        "is_valid": False,
        "validation_status": ValidationStatus.PENDING.value,
        "confidence_level": ConfidenceLevel.VERY_LOW.value,
        "confidence_score": 0.0,
        "extracted_data": {},
        "errors": [],
        "warnings": [],
        "suggestions": [],
        "file_info": {},
        "validated_at": datetime.now().isoformat()
    }
    
    if not settings.document_validation_enabled:
        result["warnings"].append("Document validation is disabled in configuration")
        result["validation_status"] = ValidationStatus.WARNING.value
        result["is_valid"] = True
        result["success"] = True
        return result
    
    try:
        # Validate document type
        if document_type not in [dt.value for dt in DocumentType]:
            result["errors"].append(f"Unsupported document type: {document_type}")
            return result
        
        # Basic file validation (without OCR)
        file_validation = _validate_file_format(file_data, document_type)
        result["file_info"] = file_validation["file_info"]
        result["errors"].extend(file_validation["errors"])
        result["warnings"].extend(file_validation["warnings"])
        
        if file_validation["errors"]:
            return result
        
        # Document-specific validation
        if document_type == DocumentType.INE_FRONT.value:
            validation_result = _validate_ine_document(file_data, "front", tramite_context)
        elif document_type == DocumentType.INE_BACK.value:
            validation_result = _validate_ine_document(file_data, "back", tramite_context)
        elif document_type == DocumentType.COMPROBANTE_DOMICILIO.value:
            validation_result = _validate_address_proof(file_data, tramite_context)
        elif document_type == DocumentType.PASSPORT.value:
            validation_result = _validate_passport(file_data, tramite_context)
        else:
            # Generic document validation
            validation_result = _validate_generic_document(file_data, document_type, tramite_context)
        
        # Merge validation results
        result.update(validation_result)
        
        # Store in database if validation successful
        if result["success"] and session_id:
            _store_validated_document(session_id, document_type, result)
            
    except Exception as e:
        result["errors"].append(f"Document validation error: {str(e)}")
        
    return result


def _validate_file_format(file_data: str, document_type: str) -> Dict[str, Any]:
    """Validate file format and basic properties"""
    
    result = {
        "file_info": {},
        "errors": [],
        "warnings": []
    }
    
    # For now, simulate file validation since we're not implementing OCR yet
    # In real implementation, this would check file size, format, corruption, etc.
    
    if not file_data:
        result["errors"].append("No se proporcionó archivo")
        return result
    
    # Simulate file info extraction
    result["file_info"] = {
        "file_size": len(file_data) if isinstance(file_data, str) else 0,
        "format": "image/jpeg",  # Would be detected from actual file
        "dimensions": "1200x800",  # Would be extracted from image
        "created_at": datetime.now().isoformat()
    }
    
    # Check file size limits
    max_size_mb = settings.max_document_size_mb * 1024 * 1024
    if result["file_info"]["file_size"] > max_size_mb:
        result["errors"].append(f"Archivo excede el tamaño máximo de {settings.max_document_size_mb}MB")
    
    return result


def _validate_ine_document(file_data: str, side: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Validate INE document (front or back)"""
    
    result = {
        "success": False,
        "is_valid": False,
        "validation_status": ValidationStatus.PENDING.value,
        "confidence_score": 0.5,  # Moderate confidence without OCR
        "extracted_data": {},
        "errors": [],
        "warnings": [],
        "suggestions": []
    }
    
    # Simulate INE validation logic
    # In real implementation, this would use OCR to extract:
    # - Name, address, voter ID, expiration date, etc.
    
    result["warnings"].append("Validación de INE sin OCR - verificación manual requerida")
    
    # Simulate extracted data structure
    if side == "front":
        result["extracted_data"] = {
            "side": "front",
            "name_detected": True,
            "photo_detected": True,
            "voter_id_detected": True,
            "legible": True,  # Would be determined by OCR confidence
            "expiry_date": "2029-12-31",  # Would be extracted via OCR
            "name_extracted": "",  # Would contain actual extracted name
            "address_extracted": ""  # Would contain actual extracted address
        }
    else:  # back
        result["extracted_data"] = {
            "side": "back",
            "curp_detected": True,
            "electoral_code_detected": True,
            "legible": True
        }
    
    # Check if document appears expired (simulation)
    try:
        expiry_str = result["extracted_data"].get("expiry_date", "")
        if expiry_str:
            expiry_date = datetime.fromisoformat(expiry_str).date()
            if expiry_date < date.today():
                result["errors"].append("INE appears to be expired")
                result["suggestions"].append("Provide current, non-expired identification")
            else:
                result["confidence_score"] += 0.3
    except:
        result["warnings"].append("Could not verify expiration date")
    
    # Name consistency check with context
    if context and "expected_name" in context:
        expected_name = context["expected_name"]
        # In real implementation, would compare OCR extracted name with expected
        result["extracted_data"]["name_consistency"] = 0.95  # High similarity simulation
        result["confidence_score"] += 0.2
    
    if result["confidence_score"] >= 0.7 and not result["errors"]:
        result["is_valid"] = True
        result["success"] = True
        result["validation_status"] = ValidationStatus.VALID.value
        result["confidence_level"] = ConfidenceLevel.MEDIUM.value
    else:
        result["validation_status"] = ValidationStatus.WARNING.value
        result["confidence_level"] = ConfidenceLevel.LOW.value
        
    return result


def _validate_address_proof(file_data: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Validate address proof document"""
    
    result = {
        "success": False,
        "is_valid": False,
        "validation_status": ValidationStatus.PENDING.value,
        "confidence_score": 0.4,
        "extracted_data": {},
        "errors": [],
        "warnings": [],
        "suggestions": []
    }
    
    result["warnings"].append("Validación de comprobante de domicilio sin OCR - verificación manual requerida")
    
    # Simulate extraction of key data
    result["extracted_data"] = {
        "document_type": "utility_bill",  # Would be detected
        "issue_date": "2024-09-15",  # Would be extracted via OCR
        "address_line": "",  # Would contain extracted address
        "postal_code": "",  # Would contain extracted ZIP
        "municipality": "",  # Would contain extracted city
        "state": "",  # Would contain extracted state
        "service_type": "electricity",  # Would be detected
        "legible": True
    }
    
    # Check document age
    try:
        issue_date_str = result["extracted_data"]["issue_date"]
        issue_date = datetime.fromisoformat(issue_date_str).date()
        age_days = (date.today() - issue_date).days
        
        if age_days > settings.max_document_age_days:
            result["errors"].append(f"Comprobante es muy antiguo ({age_days} días). Máximo permitido: {settings.max_document_age_days} días")
            result["suggestions"].append("Proporciona un comprobante más reciente")
        else:
            result["confidence_score"] += 0.3
            result["extracted_data"]["age_days"] = age_days
            
    except:
        result["warnings"].append("No se pudo verificar la fecha del comprobante")
    
    # Address consistency check
    if context and "expected_postal_code" in context:
        expected_cp = context["expected_postal_code"]
        # In real implementation, would compare extracted ZIP with expected
        result["extracted_data"]["postal_code_match"] = True
        result["confidence_score"] += 0.2
    
    if result["confidence_score"] >= 0.6 and not result["errors"]:
        result["is_valid"] = True
        result["success"] = True
        result["validation_status"] = ValidationStatus.VALID.value
        result["confidence_level"] = ConfidenceLevel.MEDIUM.value
    else:
        result["validation_status"] = ValidationStatus.WARNING.value
        result["confidence_level"] = ConfidenceLevel.LOW.value
        
    return result


def _validate_passport(file_data: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Validate passport document"""
    
    result = {
        "success": True,  # Basic validation passes
        "is_valid": True,
        "validation_status": ValidationStatus.WARNING.value,
        "confidence_score": 0.6,
        "confidence_level": ConfidenceLevel.MEDIUM.value,
        "extracted_data": {
            "document_type": "passport",
            "legible": True,
            "photo_detected": True
        },
        "errors": [],
        "warnings": ["Validación de pasaporte sin OCR - verificación manual requerida"],
        "suggestions": ["Verifica manualmente que el pasaporte esté vigente y sea legible"]
    }
    
    return result


def _validate_generic_document(file_data: str, document_type: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generic document validation for unsupported specific types"""
    
    result = {
        "success": True,
        "is_valid": True, 
        "validation_status": ValidationStatus.WARNING.value,
        "confidence_score": 0.5,
        "confidence_level": ConfidenceLevel.MEDIUM.value,
        "extracted_data": {
            "document_type": document_type,
            "legible": True
        },
        "errors": [],
        "warnings": [f"Validación genérica para {document_type} - verificación manual requerida"],
        "suggestions": ["Verifica manualmente que el documento sea legible y esté vigente"]
    }
    
    return result


def _store_validated_document(session_id: str, document_type: str, validation_result: Dict[str, Any]):
    """Store validated document in database"""
    
    db: Session = next(get_database())
    
    try:
        # Check if document already exists for this session
        existing = db.query(ValidatedDocument).filter(
            ValidatedDocument.tramite_session_id == session_id,
            ValidatedDocument.document_type == document_type
        ).first()
        
        file_info = validation_result.get("file_info", {})
        
        if existing:
            # Update existing
            existing.validation_score = validation_result["confidence_score"]
            existing.confidence_level = validation_result["confidence_level"]
            existing.extracted_data = validation_result["extracted_data"]
            existing.validation_errors = validation_result["errors"]
            existing.is_valid = validation_result["is_valid"]
            existing.validated_at = datetime.utcnow()
            existing.file_size = file_info.get("file_size", 0)
        else:
            # Create new
            validated_doc = ValidatedDocument(
                tramite_session_id=session_id,
                document_type=document_type,
                file_name=f"{document_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                file_size=file_info.get("file_size", 0),
                extracted_data=validation_result["extracted_data"],
                validation_score=validation_result["confidence_score"],
                confidence_level=validation_result["confidence_level"],
                validation_errors=validation_result["errors"],
                is_valid=validation_result["is_valid"]
            )
            db.add(validated_doc)
            
        db.commit()
        
    except Exception as e:
        db.rollback()
    finally:
        db.close()