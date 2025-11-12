from langchain.tools import tool
from typing import Dict, Any
from datetime import datetime
from domain_types.tramite_types import TramiteType


@tool("explain_requirement")
def explain_requirement(
    tramite_type: str,
    requirement: str,
    user_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Provides detailed explanation of why specific requirements are needed for tramites.
    
    Args:
        tramite_type: Type of tramite (SAT_RFC_INSCRIPCION_PF, etc.)
        requirement: Specific requirement to explain (curp, identificacion, domicilio, etc.)
        user_context: User-specific context for personalized explanations
        
    Returns:
        Dict with detailed explanation, legal basis, and practical guidance
    """
    
    result = {
        "success": False,
        "tramite_type": tramite_type,
        "requirement": requirement,
        "explanation": "",
        "legal_basis": "",
        "practical_guidance": [],
        "common_errors": [],
        "alternatives": [],
        "estimated_time": "",
        "related_requirements": [],
        "generated_at": datetime.now().isoformat(),
        "errors": []
    }
    
    try:
        if tramite_type == TramiteType.SAT_RFC_INSCRIPCION_PF.value:
            explanation_data = _explain_rfc_inscripcion_requirement(requirement, user_context)
        else:
            explanation_data = _explain_generic_requirement(tramite_type, requirement, user_context)
            
        result.update(explanation_data)
        result["success"] = True
        
    except Exception as e:
        result["errors"].append(f"Error generating explanation: {str(e)}")
        
    return result


def _explain_rfc_inscripcion_requirement(requirement: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Explain requirements for RFC Inscripción Persona Física"""
    
    explanations = {
        "overview": {
            "explanation": "El RFC (Registro Federal de Contribuyentes) es tu clave única como contribuyente ante el SAT. Es obligatorio para trabajar formalmente, emitir facturas, abrir cuentas bancarias y realizar actividades económicas que generen ingresos en México.",
            "legal_basis": "Código Fiscal de la Federación, artículo 27",
            "practical_guidance": [
                "Te identifica únicamente ante el sistema fiscal mexicano",
                "Permite a tu empleador retenerte impuestos correctamente",
                "Es requisito para abrir cuentas bancarias empresariales",
                "Necesario para emitir comprobantes fiscales (facturas)"
            ],
            "common_errors": [
                "Pensar que solo necesitas RFC si tienes un negocio",
                "Creer que con CURP es suficiente para trabajar"
            ],
            "alternatives": [],
            "estimated_time": "15-30 minutos en línea, 1-2 horas presencial",
            "related_requirements": ["curp", "identificacion", "domicilio", "actividad_economica"]
        },
        
        "curp": {
            "explanation": "La CURP (Clave Única de Registro de Población) es tu identificador único en México. El SAT la usa para verificar tu identidad, extraer datos básicos como fecha de nacimiento y entidad federativa, y asegurar que no duplices registros.",
            "legal_basis": "Ley General de Población, artículo 85",
            "practical_guidance": [
                "Debe tener exactamente 18 caracteres",
                "Formato: AAAA######XAAAAA## (letras y números específicos)",
                "Los datos extraídos deben coincidir con tu identificación oficial",
                "Si no tienes CURP, puedes tramitarla en gob.mx/curp"
            ],
            "common_errors": [
                "Escribir la CURP con espacios o guiones",
                "Usar minúsculas en lugar de mayúsculas",
                "Confundir letras similares (O con 0, I con 1)",
                "Usar una CURP que no coincide con tu nombre real"
            ],
            "alternatives": [
                "Si no tienes CURP, primero debes tramitarla en RENAPO"
            ],
            "estimated_time": "2 minutos para validar, 1-2 horas si necesitas tramitar CURP nueva",
            "related_requirements": ["identificacion", "datos_personales"]
        },
        
        "identificacion": {
            "explanation": "La identificación oficial vigente (INE, pasaporte, cédula profesional) comprueba que realmente eres quien dices ser. El SAT necesita verificar que el nombre, foto y datos coincidan con los de tu CURP.",
            "legal_basis": "Código Fiscal de la Federación, artículo 27, fracción III",
            "practical_guidance": [
                "Debe estar vigente (no vencida)",
                "La foto debe ser clara y reciente",
                "El nombre debe coincidir exactamente con tu CURP",
                "Para trámite en línea no necesitas presentarla físicamente"
            ],
            "common_errors": [
                "Usar identificación vencida",
                "Foto borrosa o con reflejos que impiden leer datos",
                "Discrepancia entre nombre en INE y CURP",
                "Presentar solo un lado del INE (se necesitan ambos lados para presencial)"
            ],
            "alternatives": [
                "INE o credencial para votar (más común)",
                "Pasaporte mexicano vigente",
                "Cédula profesional vigente",
                "Credencial del INAPAM (adultos mayores)"
            ],
            "estimated_time": "5 minutos para verificar vigencia y legibilidad",
            "related_requirements": ["curp", "datos_personales"]
        },
        
        "domicilio": {
            "explanation": "Tu domicilio fiscal es la dirección oficial donde el SAT te localizará para notificaciones, requerimientos y correspondencia fiscal. Debe ser real y verificable, ya que determina tu oficina del SAT de referencia.",
            "legal_basis": "Código Fiscal de la Federación, artículo 10",
            "practical_guidance": [
                "Debe incluir calle, número, colonia, CP, municipio y estado",
                "El código postal debe ser válido y existir en el catálogo del SAT",
                "Preferiblemente donde realmente vives o trabajas",
                "Para modalidad presencial: comprobante no mayor a 3 meses"
            ],
            "common_errors": [
                "Código postal incorrecto o inexistente",
                "Dirección incompleta (falta colonia, municipio, etc.)",
                "Usar domicilio temporal o que no es verificable",
                "Comprobante muy antiguo (mayor a 90 días)"
            ],
            "alternatives": [
                "Comprobante de luz, agua, gas, teléfono fijo",
                "Estado de cuenta bancario",
                "Contrato de arrendamiento",
                "Si vives con familiares: carta de residencia + comprobante del familiar"
            ],
            "estimated_time": "5-10 minutos para capturar, 15 minutos si necesitas conseguir comprobante",
            "related_requirements": ["comprobante_domicilio"]
        },
        
        "actividad_economica": {
            "explanation": "El SAT necesita saber qué tipo de ingresos obtendrás para asignarte el régimen fiscal correcto y determinar tus obligaciones (declaraciones, retenciones, facturación). Esto no es opcional - todos los contribuyentes deben declarar su actividad.",
            "legal_basis": "Código Fiscal de la Federación, artículos 16 y 27",
            "practical_guidance": [
                "Sé honesto sobre tus actividades reales o planeadas",
                "Puedes tener múltiples actividades (salario + negocio propio)",
                "Si solo trabajarás por salario, declara 'Sueldos y Salarios'",
                "Si planeas negocio propio, considera RIF o Actividades Empresariales"
            ],
            "common_errors": [
                "No declarar actividades adicionales al salario",
                "Elegir régimen incorrecto para tus ingresos esperados",
                "Pensar que puedes 'cambiar después' sin consecuencias",
                "No entender las obligaciones de cada régimen"
            ],
            "alternatives": [
                "Sueldos y Salarios (solo empleado)",
                "Actividades Empresariales (negocio propio)",
                "Régimen de Incorporación Fiscal (negocio pequeño)",
                "Arrendamiento (rentas)",
                "Actividades Profesionales (servicios profesionales)"
            ],
            "estimated_time": "5-10 minutos para decidir régimen",
            "related_requirements": ["regimen_fiscal"]
        },
        
        "contacto": {
            "explanation": "El SAT necesita tu correo electrónico para enviarte notificaciones oficiales, comprobantes de trámites, avisos de vencimientos y comunicaciones importantes. Es obligatorio y debe ser un correo que revises regularmente.",
            "legal_basis": "Código Fiscal de la Federación, artículo 17-K",
            "practical_guidance": [
                "Usa un correo personal que consultes frecuentemente",
                "Evita correos corporativos que podrías perder",
                "Asegúrate de que esté bien escrito (sin errores de tipeo)",
                "El SAT enviará un correo de confirmación"
            ],
            "common_errors": [
                "Usar correo temporal o que no revisas",
                "Errores de tipeo en la dirección de correo",
                "Usar correo del trabajo que podrías perder",
                "No confirmar el correo cuando el SAT lo solicita"
            ],
            "alternatives": [
                "No hay alternativas - el correo es obligatorio",
                "Puedes cambiarlo después desde tu portal del SAT"
            ],
            "estimated_time": "2 minutos",
            "related_requirements": ["datos_personales"]
        }
    }
    
    if requirement in explanations:
        return explanations[requirement]
    else:
        return {
            "explanation": f"Requisito '{requirement}' para inscripción al RFC",
            "legal_basis": "Código Fiscal de la Federación",
            "practical_guidance": ["Consulta la página oficial del SAT para más detalles"],
            "common_errors": [],
            "alternatives": [],
            "estimated_time": "Consultar con el SAT",
            "related_requirements": []
        }


def _explain_generic_requirement(tramite_type: str, requirement: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Explain requirements for other tramite types"""
    
    return {
        "explanation": f"Requisito '{requirement}' necesario para el trámite {tramite_type}",
        "legal_basis": "Normativa aplicable del SAT",
        "practical_guidance": [
            "Consulta la página oficial del SAT para requisitos específicos",
            f"Busca información detallada sobre {tramite_type}"
        ],
        "common_errors": [
            "No verificar requisitos actualizados en sat.gob.mx"
        ],
        "alternatives": [
            "Contactar directamente al SAT para orientación específica"
        ],
        "estimated_time": "Consultar con especialista",
        "related_requirements": []
    }