from langchain.tools import tool
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from data.database import get_database
from data.models import TramiteSession, ChecklistItem
from domain_types.tramite_types import TramiteType, TramiteModality
from domain_types.validation_types import RequirementStatus


@tool("generate_tramite_checklist")
def generate_tramite_checklist(
    tramite_type: str,
    session_id: str,
    current_documents: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generates contextual checklist for specific tramite type using real database storage.
    
    Args:
        tramite_type: Type of tramite (SAT_RFC_INSCRIPCION_PF, etc.)
        session_id: Tramite session ID  
        current_documents: List of currently validated documents
        
    Returns:
        Dict with checklist, completion status, and next steps
    """
    
    # Debug logging
    print(f"📋 CHECKLIST DEBUG: generate_tramite_checklist called")
    print(f"📋 CHECKLIST DEBUG: tramite_type={tramite_type}, session_id={session_id}")
    print(f"📋 CHECKLIST DEBUG: current_documents={current_documents}")
    
    result = {
        "success": False,
        "tramite_type": tramite_type,
        "session_id": session_id,
        "checklist": [],
        "completion_percentage": 0.0,
        "next_steps": [],
        "preferred_modality": TramiteModality.ONLINE.value,
        "warnings": [],
        "estimated_time": "15-30 minutes",
        "generated_at": datetime.now().isoformat(),
        "errors": []
    }
    
    db: Session = next(get_database())
    
    try:
        # Get session data
        session = db.query(TramiteSession).filter(
            TramiteSession.id == session_id
        ).first()
        
        if not session:
            result["errors"].append(f"Session {session_id} not found")
            return result
        
        # Generate checklist based on tramite type
        if tramite_type == TramiteType.SAT_RFC_INSCRIPCION_PF.value:
            checklist_data = _generate_rfc_inscripcion_checklist(session, current_documents)
        else:
            checklist_data = _generate_generic_checklist(tramite_type, session, current_documents)
        
        result.update(checklist_data)
        
        # Store checklist items in database
        _store_checklist_items(session_id, result["checklist"], db)
        
        # Update session completion percentage
        session.completion_percentage = result["completion_percentage"]
        if result["completion_percentage"] >= 100:
            session.is_completed = True
        session.updated_at = datetime.utcnow()
        
        db.commit()
        result["success"] = True
        
    except Exception as e:
        print(f"❌ CHECKLIST ERROR: generate_tramite_checklist failed: {str(e)}")
        print(f"❌ CHECKLIST ERROR: Exception type: {type(e)}")
        db.rollback()
        result["errors"].append(f"Checklist generation error: {str(e)}")
    finally:
        db.close()
    
    print(f"📋 CHECKLIST DEBUG: Returning result: {result}")
    return result


def _generate_rfc_inscripcion_checklist(session, current_documents: List = None) -> Dict[str, Any]:
    """Generate checklist for RFC Inscripción Persona Física"""
    
    checklist = []
    warnings = []
    next_steps = []
    
    # Get user profile data
    user_profile = session.user_profile if session else None
    validated_docs = session.validated_documents if session else []
    validated_identifiers = user_profile.validated_identifiers if user_profile else []
    
    # 1. CURP Validation
    curp_requirement = {
        "id": "curp_validation",
        "name": "CURP válida",
        "description": "Clave Única de Registro de Población de 18 caracteres",
        "status": RequirementStatus.PENDING.value,
        "is_mandatory": True,
        "validation_notes": [],
        "help_text": "Tu CURP la puedes obtener en gob.mx/curp"
    }
    
    # Check if CURP is validated
    curp_validated = any(
        id_val.identifier_type == "curp" and id_val.is_valid 
        for id_val in validated_identifiers
    )
    
    if curp_validated:
        curp_requirement["status"] = RequirementStatus.COMPLETED.value
        curp_requirement["validation_notes"].append("CURP validada correctamente")
    elif user_profile and user_profile.full_name:
        curp_requirement["status"] = RequirementStatus.PENDING.value
        curp_requirement["validation_notes"].append("Esperando validación de CURP")
    
    checklist.append(curp_requirement)
    
    # 2. Personal Data
    personal_data_requirement = {
        "id": "personal_data",
        "name": "Datos personales completos",
        "description": "Nombre completo, fecha de nacimiento, nacionalidad",
        "status": RequirementStatus.PENDING.value,
        "is_mandatory": True,
        "validation_notes": [],
        "help_text": "Los datos deben coincidir exactamente con tu CURP"
    }
    
    if user_profile:
        missing_fields = []
        if not user_profile.full_name:
            missing_fields.append("nombre completo")
        if not user_profile.birth_date:
            missing_fields.append("fecha de nacimiento")
            
        if not missing_fields:
            personal_data_requirement["status"] = RequirementStatus.COMPLETED.value
            personal_data_requirement["validation_notes"].append("Datos personales completos")
        else:
            personal_data_requirement["validation_notes"].append(f"Faltan: {', '.join(missing_fields)}")
    
    checklist.append(personal_data_requirement)
    
    # 3. Contact Information
    contact_requirement = {
        "id": "contact_info",
        "name": "Información de contacto",
        "description": "Correo electrónico válido (requerido por el SAT)",
        "status": RequirementStatus.PENDING.value,
        "is_mandatory": True,
        "validation_notes": [],
        "help_text": "El SAT enviará notificaciones a este correo"
    }
    
    if user_profile and user_profile.contact_info and user_profile.contact_info.email:
        contact_requirement["status"] = RequirementStatus.COMPLETED.value
        contact_requirement["validation_notes"].append("Correo electrónico registrado")
    else:
        contact_requirement["validation_notes"].append("Se requiere correo electrónico")
    
    checklist.append(contact_requirement)
    
    # 4. Fiscal Address
    address_requirement = {
        "id": "fiscal_address",
        "name": "Domicilio fiscal",
        "description": "Dirección completa con código postal válido",
        "status": RequirementStatus.PENDING.value,
        "is_mandatory": True,
        "validation_notes": [],
        "help_text": "Será tu domicilio fiscal ante el SAT"
    }
    
    if user_profile and user_profile.address:
        address = user_profile.address
        missing_address_fields = []
        
        if not address.street:
            missing_address_fields.append("calle")
        if not address.postal_code:
            missing_address_fields.append("código postal")
        if not address.municipality:
            missing_address_fields.append("municipio")
        if not address.state:
            missing_address_fields.append("estado")
            
        if not missing_address_fields:
            address_requirement["status"] = RequirementStatus.COMPLETED.value
            address_requirement["validation_notes"].append("Domicilio completo")
        else:
            address_requirement["validation_notes"].append(f"Faltan: {', '.join(missing_address_fields)}")
    
    checklist.append(address_requirement)
    
    # 5. Economic Activity Declaration
    activity_requirement = {
        "id": "economic_activity",
        "name": "Declaración de actividad económica",
        "description": "Tipo de ingresos que obtendrás (salario, negocio propio, etc.)",
        "status": RequirementStatus.PENDING.value,
        "is_mandatory": True,
        "validation_notes": ["Determina tu régimen fiscal"],
        "help_text": "Esto define qué obligaciones fiscales tendrás"
    }
    
    # Check if economic activity has been declared in session
    # Since economic activity is stored when conversation_state_tool processes it,
    # we'll check for its presence in the validated data or checklist items
    if session and session.checklist_items:
        # Check if economic activity was previously marked as completed
        for existing_item in session.checklist_items:
            if existing_item.requirement_id == "economic_activity" and existing_item.status == RequirementStatus.COMPLETED.value:
                activity_requirement["status"] = RequirementStatus.COMPLETED.value
                activity_requirement["validation_notes"] = ["Actividad económica registrada"]
                break
    
    checklist.append(activity_requirement)
    
    # Calculate completion percentage
    completed_items = [item for item in checklist if item["status"] == RequirementStatus.COMPLETED.value]
    completion_percentage = (len(completed_items) / len(checklist)) * 100
    
    # Generate next steps based on current status
    if completion_percentage < 20:
        next_steps.append({
            "step_number": 1,
            "title": "Validar tu CURP",
            "description": "Proporciona tu CURP de 18 caracteres para validar tu identidad",
            "estimated_time": "2 minutos"
        })
    elif completion_percentage < 40:
        next_steps.append({
            "step_number": 2,
            "title": "Completar datos personales",
            "description": "Confirma tu nombre completo y fecha de nacimiento",
            "estimated_time": "3 minutos"
        })
    elif completion_percentage < 60:
        next_steps.append({
            "step_number": 3,
            "title": "Agregar información de contacto",
            "description": "Proporciona tu correo electrónico para notificaciones del SAT",
            "estimated_time": "2 minutos"
        })
    elif completion_percentage < 80:
        next_steps.append({
            "step_number": 4,
            "title": "Registrar domicilio fiscal",
            "description": "Captura tu dirección completa con código postal",
            "estimated_time": "5 minutos"
        })
    elif completion_percentage < 100:
        next_steps.append({
            "step_number": 5,
            "title": "Declarar actividad económica",
            "description": "Indica qué tipo de actividad económica realizarás",
            "estimated_time": "5 minutos"
        })
    else:
        next_steps.append({
            "step_number": 6,
            "title": "Ejecutar trámite en línea",
            "description": "Ve a sat.gob.mx para completar tu inscripción al RFC",
            "estimated_time": "10-15 minutos",
            "url": "https://www.sat.gob.mx/aplicacion/operacion/31274/inscribete-al-rfc"
        })
    
    # Determine preferred modality
    preferred_modality = TramiteModality.ONLINE.value
    
    # Check for conditions that require presential mode
    if user_profile:
        if user_profile.is_minor:
            preferred_modality = TramiteModality.PRESENCIAL.value
            warnings.append("Al ser menor de edad, el trámite debe hacerse presencialmente con tutor")
        elif user_profile.nationality != "mexicana":
            preferred_modality = TramiteModality.PRESENCIAL.value  
            warnings.append("Se requieren documentos migratorios adicionales para extranjeros")
    
    # Estimate total time
    if preferred_modality == TramiteModality.ONLINE.value:
        estimated_time = "15-30 minutos en línea"
    else:
        estimated_time = "1-2 horas (incluye cita presencial)"
    
    return {
        "checklist": checklist,
        "completion_percentage": completion_percentage,
        "next_steps": next_steps,
        "preferred_modality": preferred_modality,
        "warnings": warnings,
        "estimated_time": estimated_time
    }


def _generate_generic_checklist(tramite_type: str, session, current_documents: List = None) -> Dict[str, Any]:
    """Generate generic checklist for unsupported tramite types"""
    
    checklist = [
        {
            "id": "basic_requirements",
            "name": "Requisitos básicos",
            "description": f"Verificar requisitos para {tramite_type}",
            "status": RequirementStatus.PENDING.value,
            "is_mandatory": True,
            "validation_notes": ["Consultar página oficial del SAT"],
            "help_text": f"Revisa los requisitos específicos para {tramite_type}"
        }
    ]
    
    return {
        "checklist": checklist,
        "completion_percentage": 0.0,
        "next_steps": [
            {
                "step_number": 1,
                "title": "Consultar requisitos",
                "description": f"Revisar requisitos específicos para {tramite_type}",
                "estimated_time": "10 minutos"
            }
        ],
        "preferred_modality": TramiteModality.PRESENCIAL.value,
        "warnings": [f"Tipo de trámite {tramite_type} requiere consulta especializada"],
        "estimated_time": "Consultar con el SAT"
    }


def _store_checklist_items(session_id: str, checklist: List[Dict], db: Session):
    """Store checklist items in database"""
    
    try:
        # Delete existing checklist items for this session
        db.query(ChecklistItem).filter(
            ChecklistItem.tramite_session_id == session_id
        ).delete()
        
        # Add new checklist items
        for index, item in enumerate(checklist):
            checklist_item = ChecklistItem(
                tramite_session_id=session_id,
                requirement_id=item["id"],
                name=item["name"],
                description=item["description"],
                status=item["status"],
                is_mandatory=item["is_mandatory"],
                validation_notes=item["validation_notes"],
                help_text=item.get("help_text"),
                order_index=index
            )
            db.add(checklist_item)
            
    except Exception as e:
        raise Exception(f"Error storing checklist items: {str(e)}")