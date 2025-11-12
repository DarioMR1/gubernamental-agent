from enum import Enum


class ValidationStatus(str, Enum):
    """Status of validation results"""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    PENDING = "pending"
    ERROR = "error"


class RequirementStatus(str, Enum):
    """Status of individual requirements"""
    COMPLETED = "completed"
    PENDING = "pending"
    INVALID = "invalid"
    MISSING = "missing"
    WARNING = "warning"


class ConversationPhase(str, Enum):
    """Phases of the tramite conversation"""
    WELCOME = "welcome"
    TRAMITE_SELECTION = "tramite_selection"
    ELIGIBILITY_CHECK = "eligibility_check"
    PERSONAL_DATA_COLLECTION = "personal_data_collection"
    DOCUMENT_COLLECTION = "document_collection"
    DOCUMENT_VALIDATION = "document_validation"
    ACTIVITY_DECLARATION = "activity_declaration"
    REGIME_SELECTION = "regime_selection"
    CHECKLIST_GENERATION = "checklist_generation"
    FINAL_SUMMARY = "final_summary"
    COMPLETED = "completed"


class ValidationErrorType(str, Enum):
    """Types of validation errors"""
    FORMAT_ERROR = "format_error"
    LENGTH_ERROR = "length_error"
    INVALID_CHARACTER = "invalid_character"
    CHECKSUM_ERROR = "checksum_error"
    DATE_ERROR = "date_error"
    EXPIRED_DOCUMENT = "expired_document"
    UNREADABLE_DOCUMENT = "unreadable_document"
    MISSING_DATA = "missing_data"
    INCONSISTENT_DATA = "inconsistent_data"


class ConfidenceLevel(str, Enum):
    """Confidence levels for validation results"""
    HIGH = "high"      # > 0.9
    MEDIUM = "medium"  # 0.7 - 0.9
    LOW = "low"        # 0.5 - 0.7
    VERY_LOW = "very_low"  # < 0.5