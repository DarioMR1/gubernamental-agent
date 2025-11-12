"""Instruction parser using LLM to understand natural language instructions."""

import json
import logging
from typing import List, Optional

from ..types import (
    ParsedInstruction, 
    Intent, 
    IntentType, 
    Entity, 
    LLMRequest,
    LLMProvider,
    PortalKnowledge
)
from ..config import AgentConfig
from .providers import OpenAIProvider, AnthropicProvider


logger = logging.getLogger(__name__)


class InstructionParser:
    """Parses natural language instructions into structured format."""
    
    PORTAL_KNOWLEDGE = {
        "sunat": PortalKnowledge(
            name="SUNAT",
            base_url="https://sunat.gob.pe",
            login_url="https://ww1.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias",
            document_types=[
                "constancia de inscripción",
                "constancia de RUC", 
                "certificado de no adeudo",
                "declaración jurada",
                "boleta de pago",
                "formulario PDT"
            ],
            typical_flows=[
                "download_constancia_ruc",
                "download_certificado_no_adeudo", 
                "check_tax_status",
                "download_payment_voucher"
            ],
            authentication_method="form",
            special_instructions=[
                "Requiere RUC y clave SOL",
                "Captcha presente en algunos formularios",
                "Sesión expira en 30 minutos"
            ]
        ),
        "essalud": PortalKnowledge(
            name="EsSalud",
            base_url="https://essalud.gob.pe",
            document_types=[
                "certificado de afiliación",
                "carta de presentación",
                "declaración jurada de salud"
            ],
            authentication_method="form"
        ),
        "reniec": PortalKnowledge(
            name="RENIEC",
            base_url="https://reniec.gob.pe",
            document_types=[
                "partida de nacimiento",
                "certificado de nacimiento",
                "antecedentes penales"
            ],
            authentication_method="form"
        )
    }
    
    def __init__(self, config: AgentConfig):
        """Initialize instruction parser.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        
        # Initialize LLM provider
        if config.llm.provider == LLMProvider.OPENAI:
            from ..config import Environment
            env = Environment()
            self.llm_provider = OpenAIProvider(env.get_api_key())
        elif config.llm.provider == LLMProvider.ANTHROPIC:
            from ..config import Environment
            env = Environment()
            self.llm_provider = AnthropicProvider(env.get_api_key())
        else:
            raise ValueError(f"Unsupported LLM provider: {config.llm.provider}")
    
    async def parse_instruction(self, text: str) -> ParsedInstruction:
        """Parse natural language instruction into structured format.
        
        Args:
            text: Natural language instruction
            
        Returns:
            Parsed instruction with intent, entities, and metadata
        """
        logger.info(f"Parsing instruction: {text}")
        
        try:
            # Extract intent
            intent = await self.extract_intent(text)
            
            # Extract entities
            entities = await self.identify_entities(text)
            
            # Identify portal
            portal_identified = self._identify_portal(text, entities)
            
            # Extract document types
            document_types = self._extract_document_types(text, portal_identified)
            
            # Calculate confidence based on clarity of intent and entities
            confidence = self._calculate_confidence(intent, entities, portal_identified)
            
            return ParsedInstruction(
                original_text=text,
                intent=intent,
                entities=entities,
                portal_identified=portal_identified,
                document_types=document_types,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error parsing instruction: {e}")
            
            # Return fallback parsed instruction
            return ParsedInstruction(
                original_text=text,
                intent=Intent(type=IntentType.NAVIGATE_PORTAL, confidence=0.1),
                entities=[],
                confidence=0.1
            )
    
    async def extract_intent(self, text: str) -> Intent:
        """Extract user intent from instruction.
        
        Args:
            text: User instruction
            
        Returns:
            Identified intent
        """
        system_prompt = """You are an expert at understanding user intents for government portal automation.

Analyze the user's instruction and identify the primary intent. Choose from these intent types:
- download_document: User wants to download a specific document
- fill_form: User wants to fill out a form
- search_information: User wants to search or look up information
- submit_application: User wants to submit an application
- check_status: User wants to check the status of something
- update_information: User wants to update their information
- generate_report: User wants to generate or create a report
- authenticate: User wants to log in or authenticate
- navigate_portal: User wants to navigate to a specific section

Return your response as JSON with:
{
  "intent_type": "intent_name",
  "confidence": 0.9,
  "reasoning": "Brief explanation of why you chose this intent"
}"""
        
        request = LLMRequest(
            prompt=f"User instruction: \"{text}\"\n\nAnalyze this instruction and identify the primary intent.",
            model=self.config.llm.model,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=200
        )
        
        response = await self.llm_provider.generate_response(request)
        
        try:
            # Parse JSON response
            result = json.loads(response.content)
            intent_type = IntentType(result["intent_type"])
            confidence = float(result["confidence"])
            
            return Intent(type=intent_type, confidence=confidence)
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse intent response: {e}")
            
            # Fallback to simple keyword matching
            return self._fallback_intent_extraction(text)
    
    async def identify_entities(self, text: str) -> List[Entity]:
        """Identify named entities in the instruction.
        
        Args:
            text: User instruction
            
        Returns:
            List of identified entities
        """
        system_prompt = """You are an expert at extracting entities from government portal instructions.

Identify and extract relevant entities from the user's instruction. Look for:
- portal: Government portal name (SUNAT, EsSalud, RENIEC, etc.)
- document: Document type (RUC, DNI, certificate, constancia, etc.) 
- ruc: RUC number (11 digits)
- dni: DNI number (8 digits)
- period: Time period (month, year, date range)
- company: Company name
- person: Person name
- amount: Monetary amount

Return your response as JSON array:
[
  {
    "type": "entity_type",
    "value": "extracted_value",
    "confidence": 0.9,
    "start_pos": 10,
    "end_pos": 15
  }
]"""
        
        request = LLMRequest(
            prompt=f"User instruction: \"{text}\"\n\nExtract all relevant entities.",
            model=self.config.llm.model,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=500
        )
        
        response = await self.llm_provider.generate_response(request)
        
        try:
            # Parse JSON response
            entities_data = json.loads(response.content)
            entities = []
            
            for entity_data in entities_data:
                entity = Entity(
                    type=entity_data["type"],
                    value=entity_data["value"],
                    confidence=float(entity_data["confidence"]),
                    start_pos=int(entity_data.get("start_pos", 0)),
                    end_pos=int(entity_data.get("end_pos", 0))
                )
                entities.append(entity)
            
            return entities
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse entities response: {e}")
            
            # Fallback to simple regex-based extraction
            return self._fallback_entity_extraction(text)
    
    def _identify_portal(self, text: str, entities: List[Entity]) -> Optional[str]:
        """Identify which government portal is being referenced.
        
        Args:
            text: User instruction
            entities: Extracted entities
            
        Returns:
            Portal identifier or None
        """
        text_lower = text.lower()
        
        # Check entities first
        for entity in entities:
            if entity.type == "portal":
                return entity.value.lower()
        
        # Check for portal keywords
        portal_keywords = {
            "sunat": ["sunat", "ruc", "impuesto", "tributario", "constancia"],
            "essalud": ["essalud", "seguro", "salud", "afiliación"],
            "reniec": ["reniec", "dni", "partida", "antecedentes"],
            "ministerio": ["ministerio", "gobierno", "estado"]
        }
        
        for portal, keywords in portal_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return portal
        
        return None
    
    def _extract_document_types(
        self, 
        text: str, 
        portal: Optional[str]
    ) -> List[str]:
        """Extract document types mentioned in the instruction.
        
        Args:
            text: User instruction
            portal: Identified portal
            
        Returns:
            List of document types
        """
        text_lower = text.lower()
        document_types = []
        
        if portal and portal in self.PORTAL_KNOWLEDGE:
            portal_knowledge = self.PORTAL_KNOWLEDGE[portal]
            for doc_type in portal_knowledge.document_types:
                if doc_type.lower() in text_lower:
                    document_types.append(doc_type)
        
        # General document keywords
        general_docs = {
            "certificado", "constancia", "documento", "reporte", 
            "declaración", "formulario", "boleta", "recibo"
        }
        
        for doc in general_docs:
            if doc in text_lower and doc not in document_types:
                document_types.append(doc)
        
        return document_types
    
    def _calculate_confidence(
        self, 
        intent: Intent, 
        entities: List[Entity], 
        portal: Optional[str]
    ) -> float:
        """Calculate overall confidence in the parsing.
        
        Args:
            intent: Extracted intent
            entities: Extracted entities
            portal: Identified portal
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = intent.confidence
        
        # Boost confidence if we have relevant entities
        if entities:
            entity_confidence = sum(e.confidence for e in entities) / len(entities)
            confidence = (confidence + entity_confidence) / 2
        
        # Boost confidence if portal is identified
        if portal:
            confidence = min(1.0, confidence + 0.1)
        
        # Penalize if no entities found
        if not entities:
            confidence *= 0.8
        
        return round(confidence, 2)
    
    def _fallback_intent_extraction(self, text: str) -> Intent:
        """Fallback intent extraction using keyword matching.
        
        Args:
            text: User instruction
            
        Returns:
            Intent based on keyword matching
        """
        text_lower = text.lower()
        
        intent_keywords = {
            IntentType.DOWNLOAD_DOCUMENT: ["descargar", "download", "obtener", "constancia", "certificado"],
            IntentType.FILL_FORM: ["llenar", "completar", "formulario", "solicitud"],
            IntentType.SEARCH_INFORMATION: ["buscar", "consultar", "verificar", "revisar"],
            IntentType.SUBMIT_APPLICATION: ["enviar", "presentar", "solicitar", "aplicar"],
            IntentType.CHECK_STATUS: ["estado", "status", "verificar estado"],
            IntentType.UPDATE_INFORMATION: ["actualizar", "modificar", "cambiar"],
            IntentType.AUTHENTICATE: ["ingresar", "login", "autenticar", "iniciar sesión"],
        }
        
        for intent_type, keywords in intent_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return Intent(type=intent_type, confidence=0.6)
        
        # Default to navigate portal
        return Intent(type=IntentType.NAVIGATE_PORTAL, confidence=0.3)
    
    def _fallback_entity_extraction(self, text: str) -> List[Entity]:
        """Fallback entity extraction using regex patterns.
        
        Args:
            text: User instruction
            
        Returns:
            List of entities found using regex
        """
        import re
        entities = []
        
        # RUC pattern (11 digits)
        ruc_pattern = r'\b\d{11}\b'
        for match in re.finditer(ruc_pattern, text):
            entities.append(Entity(
                type="ruc",
                value=match.group(),
                confidence=0.9,
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        # DNI pattern (8 digits)
        dni_pattern = r'\b\d{8}\b'
        for match in re.finditer(dni_pattern, text):
            entities.append(Entity(
                type="dni",
                value=match.group(),
                confidence=0.9,
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        # Portal names
        portal_pattern = r'\b(sunat|essalud|reniec)\b'
        for match in re.finditer(portal_pattern, text, re.IGNORECASE):
            entities.append(Entity(
                type="portal",
                value=match.group().upper(),
                confidence=0.8,
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        return entities