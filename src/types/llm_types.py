"""LLM-related type definitions for the governmental agent."""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


class LLMProvider(Enum):
    """Supported LLM providers."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class IntentType(Enum):
    """Types of user intents that can be identified."""
    
    DOWNLOAD_DOCUMENT = "download_document"
    FILL_FORM = "fill_form"
    SEARCH_INFORMATION = "search_information"
    SUBMIT_APPLICATION = "submit_application"
    CHECK_STATUS = "check_status"
    UPDATE_INFORMATION = "update_information"
    GENERATE_REPORT = "generate_report"
    AUTHENTICATE = "authenticate"
    NAVIGATE_PORTAL = "navigate_portal"


@dataclass
class Entity:
    """Named entity extracted from user instruction."""
    
    type: str
    value: str
    confidence: float
    start_pos: int
    end_pos: int


@dataclass
class Intent:
    """User intent identified from instruction."""
    
    type: IntentType
    confidence: float
    parameters: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ParsedInstruction:
    """Result of parsing user instruction."""
    
    original_text: str
    intent: Intent
    entities: List[Entity]
    portal_identified: Optional[str] = None
    document_types: List[str] = None
    confidence: float = 0.0
    parsed_at: datetime = None
    
    def __post_init__(self) -> None:
        if self.document_types is None:
            self.document_types = []
        if self.parsed_at is None:
            self.parsed_at = datetime.now()
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a specific type."""
        return [entity for entity in self.entities if entity.type == entity_type]
    
    def get_entity_value(self, entity_type: str) -> Optional[str]:
        """Get the value of the first entity of a specific type."""
        entities = self.get_entities_by_type(entity_type)
        return entities[0].value if entities else None


@dataclass
class LLMRequest:
    """Request to an LLM provider."""
    
    prompt: str
    model: str
    temperature: float = 0.1
    max_tokens: int = 1000
    system_prompt: Optional[str] = None
    additional_params: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        if self.additional_params is None:
            self.additional_params = {}


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    
    content: str
    model: str
    tokens_used: int
    cost_estimate: Optional[float] = None
    finish_reason: Optional[str] = None
    response_time_ms: int = 0
    timestamp: datetime = None
    
    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PortalKnowledge:
    """Knowledge about a specific government portal."""
    
    name: str
    base_url: str
    login_url: Optional[str] = None
    common_selectors: Dict[str, str] = None
    document_types: List[str] = None
    typical_flows: List[str] = None
    authentication_method: str = "form"
    special_instructions: List[str] = None
    
    def __post_init__(self) -> None:
        if self.common_selectors is None:
            self.common_selectors = {}
        if self.document_types is None:
            self.document_types = []
        if self.typical_flows is None:
            self.typical_flows = []
        if self.special_instructions is None:
            self.special_instructions = []