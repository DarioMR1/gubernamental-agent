from langchain.tools import tool
from typing import Dict, Any
from datetime import datetime, date
import re
from sqlalchemy.orm import Session
from data.database import get_database
from data.models import ValidatedIdentifier, UserProfile
from domain_types.tramite_types import IdentifierType
from domain_types.validation_types import ValidationStatus, ConfidenceLevel
from config import settings


@tool("validate_official_identifier")
def validate_official_identifier(
    identifier_type: str,
    value: str,
    session_id: str = None
) -> Dict[str, Any]:
    """
    Validates official Mexican government identifiers (CURP, RFC) using real database storage.
    
    Args:
        identifier_type: Type of identifier ('curp', 'rfc_persona_fisica', etc.)
        value: The identifier value to validate
        session_id: Optional tramite session ID to store result
        
    Returns:
        Dict with validation result, extracted data, and confidence level
    """
    
    result = {
        "success": False,
        "identifier_type": identifier_type,
        "value": value,
        "is_valid": False,
        "validation_status": ValidationStatus.INVALID.value,
        "confidence_level": ConfidenceLevel.VERY_LOW.value,
        "confidence_score": 0.0,
        "extracted_data": {},
        "errors": [],
        "warnings": [],
        "suggestions": [],
        "validated_at": datetime.now().isoformat()
    }
    
    try:
        if identifier_type == IdentifierType.CURP.value:
            validation_result = _validate_curp(value)
        elif identifier_type == IdentifierType.RFC_PERSONA_FISICA.value:
            validation_result = _validate_rfc_persona_fisica(value)
        else:
            result["errors"].append(f"Unsupported identifier type: {identifier_type}")
            return result
            
        # Update result with validation outcome
        result.update(validation_result)
        
        # Store in database if session_id provided and validation is successful
        if session_id and result["is_valid"] and settings.curp_validation_enabled:
            _store_validated_identifier(session_id, identifier_type, value, result)
            
    except Exception as e:
        result["errors"].append(f"Validation error: {str(e)}")
        
    return result


def _validate_curp(curp: str) -> Dict[str, Any]:
    """Validate CURP format and extract data"""
    
    result = {
        "success": False,
        "is_valid": False,
        "validation_status": ValidationStatus.INVALID.value,
        "confidence_score": 0.0,
        "extracted_data": {},
        "errors": [],
        "warnings": [],
        "suggestions": []
    }
    
    # Basic format validation
    if not curp or not isinstance(curp, str):
        result["errors"].append("CURP no puede estar vacío")
        result["suggestions"].append("Proporciona un CURP válido de 18 caracteres")
        return result
        
    curp = curp.upper().strip()
    
    # Length validation
    if len(curp) != settings.curp_length_characters:
        result["errors"].append(f"CURP debe tener exactamente {settings.curp_length_characters} caracteres, tiene {len(curp)}")
        result["suggestions"].append("Verifica que no falten o sobren caracteres")
        return result
    
    # Format pattern validation
    curp_pattern = r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z][0-9]$'
    
    if not re.match(curp_pattern, curp):
        result["errors"].append("Formato de CURP inválido")
        result["suggestions"].append("CURP debe tener el formato: AAAA######XAAAAA##")
        return result
    
    confidence_score = 0.3  # Base score for format match
    
    # Extract data from CURP
    try:
        extracted_data = {
            "apellido_paterno": curp[0:2],
            "apellido_materno": curp[2],
            "nombre": curp[3],
            "fecha_nacimiento": curp[4:10],
            "sexo": "Hombre" if curp[10] == 'H' else "Mujer",
            "entidad_nacimiento": curp[11:13],
            "consonantes": curp[13:16],
            "digito_verificador": curp[17]
        }
        
        # Parse birth date
        year_str = curp[4:6]
        month_str = curp[6:8] 
        day_str = curp[8:10]
        
        # Determine full year (assuming CURP years 00-30 are 2000s, 31-99 are 1900s)
        year_int = int(year_str)
        if year_int <= 30:
            full_year = 2000 + year_int
        else:
            full_year = 1900 + year_int
            
        month_int = int(month_str)
        day_int = int(day_str)
        
        # Validate date ranges
        if month_int < 1 or month_int > 12:
            result["errors"].append("Mes de nacimiento inválido en CURP")
        elif day_int < 1 or day_int > 31:
            result["errors"].append("Día de nacimiento inválido en CURP")
        else:
            try:
                birth_date = date(full_year, month_int, day_int)
                extracted_data["fecha_nacimiento_parsed"] = birth_date.isoformat()
                extracted_data["edad_aproximada"] = (date.today() - birth_date).days // 365
                confidence_score += 0.3
            except ValueError:
                result["errors"].append("Fecha de nacimiento inválida en CURP")
        
        # Validate state code
        valid_states = {
            'AS': 'Aguascalientes', 'BC': 'Baja California', 'BS': 'Baja California Sur',
            'CC': 'Campeche', 'CL': 'Coahuila', 'CM': 'Colima', 'CS': 'Chiapas',
            'CH': 'Chihuahua', 'DF': 'Ciudad de México', 'DG': 'Durango',
            'GT': 'Guanajuato', 'GR': 'Guerrero', 'HG': 'Hidalgo', 'JC': 'Jalisco',
            'MC': 'México', 'MN': 'Michoacán', 'MS': 'Morelos', 'NT': 'Nayarit',
            'NL': 'Nuevo León', 'OC': 'Oaxaca', 'PL': 'Puebla', 'QT': 'Querétaro',
            'QR': 'Quintana Roo', 'SP': 'San Luis Potosí', 'SL': 'Sinaloa',
            'SR': 'Sonora', 'TC': 'Tabasco', 'TS': 'Tamaulipas', 'TL': 'Tlaxcala',
            'VZ': 'Veracruz', 'YN': 'Yucatán', 'ZS': 'Zacatecas', 'NE': 'Extranjero'
        }
        
        state_code = curp[11:13]
        if state_code in valid_states:
            extracted_data["entidad_nacimiento_nombre"] = valid_states[state_code]
            confidence_score += 0.2
        else:
            result["warnings"].append(f"Código de entidad '{state_code}' no reconocido")
            
        # Calculate final confidence
        if result["errors"]:
            confidence_score = max(0.1, confidence_score - 0.5)
        
        result["extracted_data"] = extracted_data
        result["confidence_score"] = min(1.0, confidence_score)
        
        if confidence_score >= 0.8:
            result["confidence_level"] = ConfidenceLevel.HIGH.value
            result["validation_status"] = ValidationStatus.VALID.value
            result["is_valid"] = True
            result["success"] = True
        elif confidence_score >= 0.5:
            result["confidence_level"] = ConfidenceLevel.MEDIUM.value
            result["validation_status"] = ValidationStatus.WARNING.value
            if not result["errors"]:
                result["is_valid"] = True
                result["success"] = True
        else:
            result["confidence_level"] = ConfidenceLevel.LOW.value
            
    except Exception as e:
        result["errors"].append(f"Error parsing CURP: {str(e)}")
        
    return result


def _validate_rfc_persona_fisica(rfc: str) -> Dict[str, Any]:
    """Validate RFC Persona Física format"""
    
    result = {
        "success": False,
        "is_valid": False,
        "validation_status": ValidationStatus.INVALID.value,
        "confidence_score": 0.0,
        "extracted_data": {},
        "errors": [],
        "warnings": [],
        "suggestions": []
    }
    
    if not rfc or not isinstance(rfc, str):
        result["errors"].append("RFC no puede estar vacío")
        return result
        
    rfc = rfc.upper().strip()
    
    # RFC Persona Física: 4 letters + 6 numbers + 3 alphanumeric
    if len(rfc) != 13:
        result["errors"].append("RFC Persona Física debe tener 13 caracteres")
        result["suggestions"].append("Formato: AAAA######AAA")
        return result
    
    rfc_pattern = r'^[A-Z]{4}[0-9]{6}[A-Z0-9]{3}$'
    
    if not re.match(rfc_pattern, rfc):
        result["errors"].append("Formato de RFC inválido")
        result["suggestions"].append("RFC debe tener el formato: AAAA######AAA")
        return result
    
    # Extract data
    extracted_data = {
        "apellido_paterno": rfc[0:2],
        "apellido_materno": rfc[2],
        "nombre": rfc[3],
        "fecha_registro": rfc[4:10],
        "homoclave": rfc[10:13]
    }
    
    result["extracted_data"] = extracted_data
    result["confidence_score"] = 0.8
    result["confidence_level"] = ConfidenceLevel.HIGH.value
    result["validation_status"] = ValidationStatus.VALID.value
    result["is_valid"] = True
    result["success"] = True
    
    return result


def _store_validated_identifier(session_id: str, identifier_type: str, value: str, validation_result: Dict[str, Any]):
    """Store validated identifier in database"""
    
    db: Session = next(get_database())
    
    try:
        # Get user profile for this session
        from data.models import TramiteSession
        session = db.query(TramiteSession).filter(TramiteSession.id == session_id).first()
        
        if not session or not session.user_profile:
            return
            
        user_profile = session.user_profile
        
        # Check if identifier already exists
        existing = db.query(ValidatedIdentifier).filter(
            ValidatedIdentifier.user_profile_id == user_profile.id,
            ValidatedIdentifier.identifier_type == identifier_type
        ).first()
        
        if existing:
            # Update existing
            existing.value = value
            existing.is_valid = validation_result["is_valid"]
            existing.validation_score = validation_result["confidence_score"]
            existing.extracted_data = validation_result["extracted_data"]
            existing.validation_errors = validation_result["errors"]
            existing.validated_at = datetime.utcnow()
        else:
            # Create new
            validated_identifier = ValidatedIdentifier(
                user_profile_id=user_profile.id,
                identifier_type=identifier_type,
                value=value,
                is_valid=validation_result["is_valid"],
                validation_score=validation_result["confidence_score"],
                extracted_data=validation_result["extracted_data"],
                validation_errors=validation_result["errors"]
            )
            db.add(validated_identifier)
            
        db.commit()
        
    except Exception as e:
        db.rollback()
    finally:
        db.close()