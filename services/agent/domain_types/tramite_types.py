from enum import Enum


class TramiteType(str, Enum):
    """Types of government procedures supported"""
    SAT_RFC_INSCRIPCION_PF = "SAT_RFC_INSCRIPCION_PF"
    SAT_RFC_ACTUALIZACION_PF = "SAT_RFC_ACTUALIZACION_PF"
    SAT_EFIRMA_NUEVA = "SAT_EFIRMA_NUEVA"
    SAT_EFIRMA_RENOVACION = "SAT_EFIRMA_RENOVACION"
    SAT_CONSTANCIA_SITUACION_FISCAL = "SAT_CONSTANCIA_SITUACION_FISCAL"


class DocumentType(str, Enum):
    """Types of documents for validation"""
    INE_FRONT = "ine_front"
    INE_BACK = "ine_back"
    PASSPORT = "passport"
    COMPROBANTE_DOMICILIO = "comprobante_domicilio"
    CURP_DOCUMENT = "curp_document"
    RFC_DOCUMENT = "rfc_document" 
    BIRTH_CERTIFICATE = "birth_certificate"
    NATURALIZATION_CARD = "naturalization_card"
    MIGRATION_DOCUMENT = "migration_document"


class IdentifierType(str, Enum):
    """Types of official identifiers for validation"""
    CURP = "curp"
    RFC_PERSONA_FISICA = "rfc_persona_fisica"
    RFC_PERSONA_MORAL = "rfc_persona_moral"
    NSS = "nss"
    PASSPORT_NUMBER = "passport_number"
    
    
class ActivityType(str, Enum):
    """Types of economic activities"""
    SALARY_ONLY = "salary_only"
    BUSINESS_ACTIVITY = "business_activity"  
    PROFESSIONAL_SERVICES = "professional_services"
    RENTAL_INCOME = "rental_income"
    MIXED_ACTIVITIES = "mixed_activities"
    NO_ACTIVITY = "no_activity"


class TaxRegime(str, Enum):
    """SAT tax regimes"""
    SUELDOS_SALARIOS = "sueldos_salarios"
    ACTIVIDADES_EMPRESARIALES = "actividades_empresariales"
    ACTIVIDADES_PROFESIONALES = "actividades_profesionales"
    ARRENDAMIENTO = "arrendamiento"
    REGIMEN_INCORPORACION_FISCAL = "regimen_incorporacion_fiscal"
    PERSONAS_FISICAS_SIN_ACTIVIDAD = "personas_fisicas_sin_actividad"


class TramiteModality(str, Enum):
    """Modalities for executing procedures"""
    ONLINE = "online"
    PRESENCIAL = "presencial"
    AMBAS = "ambas"


class ConversationPhase(str, Enum):
    """Phases of the tramite conversation"""
    WELCOME = "welcome"
    IDENTIFICATION = "identification"  
    ELIGIBILITY_CHECK = "eligibility_check"
    CURP_VALIDATION = "curp_validation"
    DOCUMENT_COLLECTION = "document_collection"
    PROFILE_COMPLETION = "profile_completion"
    ACTIVITY_DECLARATION = "activity_declaration"
    TAX_REGIME_SELECTION = "tax_regime_selection"
    FINAL_REVIEW = "final_review"
    READY_FOR_EXECUTION = "ready_for_execution"
    COMPLETED = "completed"