"""Action planner that converts parsed instructions into executable action plans."""

import json
import logging
import uuid
from typing import List, Dict, Any, Optional

from ..types import (
    ParsedInstruction,
    ExecutionPlan,
    Action,
    ActionType,
    IntentType,
    ValidationResult,
    LLMRequest
)
from ..config import AgentConfig
from .providers import OpenAIProvider, AnthropicProvider


logger = logging.getLogger(__name__)


class ActionPlanner:
    """Converts parsed instructions into executable action plans."""
    
    # Portal-specific action templates
    PORTAL_TEMPLATES = {
        "sunat": {
            "download_constancia_ruc": [
                {"type": "navigate", "url": "https://sunat.gob.pe"},
                {"type": "click", "selector": "a[href*='consulta-ruc']"},
                {"type": "fill_form", "field": "ruc", "wait_for": "#input-ruc"},
                {"type": "click", "selector": "#btn-consultar"},
                {"type": "wait_for_element", "selector": ".resultado-consulta"},
                {"type": "click", "selector": "a[href*='constancia']"},
                {"type": "download", "wait_for": "download"}
            ],
            "download_certificado_no_adeudo": [
                {"type": "navigate", "url": "https://ww1.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias"},
                {"type": "authenticate", "method": "form"},
                {"type": "navigate", "section": "certificados"},
                {"type": "click", "selector": "a[href*='no-adeudo']"},
                {"type": "fill_form", "fields": ["period"]},
                {"type": "click", "selector": "#generar"},
                {"type": "download", "wait_for": "pdf"}
            ],
            "check_tax_status": [
                {"type": "navigate", "url": "https://sunat.gob.pe"},
                {"type": "click", "selector": "a[href*='estado-tributario']"},
                {"type": "fill_form", "field": "ruc"},
                {"type": "click", "selector": "#consultar"},
                {"type": "extract_data", "target": ".estado-resultado"}
            ]
        },
        "essalud": {
            "download_certificado_afiliacion": [
                {"type": "navigate", "url": "https://essalud.gob.pe"},
                {"type": "click", "selector": "a[href*='afiliacion']"},
                {"type": "authenticate", "method": "form"},
                {"type": "click", "selector": "a[href*='certificado']"},
                {"type": "download", "wait_for": "pdf"}
            ]
        },
        "reniec": {
            "download_antecedentes_penales": [
                {"type": "navigate", "url": "https://reniec.gob.pe"},
                {"type": "click", "selector": "a[href*='antecedentes']"},
                {"type": "fill_form", "field": "dni"},
                {"type": "fill_form", "field": "captcha"},
                {"type": "click", "selector": "#consultar"},
                {"type": "download", "wait_for": "pdf"}
            ]
        }
    }
    
    def __init__(self, config: AgentConfig):
        """Initialize action planner.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        
        # Initialize LLM provider (same as instruction parser)
        if config.llm.provider.value == "openai":
            from ..config import Environment
            env = Environment()
            self.llm_provider = OpenAIProvider(env.get_api_key())
        elif config.llm.provider.value == "anthropic":
            from ..config import Environment
            env = Environment()
            self.llm_provider = AnthropicProvider(env.get_api_key())
        else:
            raise ValueError(f"Unsupported LLM provider: {config.llm.provider}")
    
    async def create_execution_plan(
        self, 
        instruction: ParsedInstruction
    ) -> ExecutionPlan:
        """Create execution plan from parsed instruction.
        
        Args:
            instruction: Parsed instruction
            
        Returns:
            Execution plan with actions
        """
        logger.info(f"Creating execution plan for: {instruction.original_text}")
        
        try:
            # Try template-based planning first
            template_actions = self._get_template_actions(instruction)
            
            if template_actions:
                logger.info("Using template-based action planning")
                actions = await self._customize_template_actions(
                    template_actions, 
                    instruction
                )
            else:
                logger.info("Using LLM-based action planning")
                actions = await self._generate_llm_actions(instruction)
            
            # Create execution plan
            plan_id = str(uuid.uuid4())
            estimated_duration = self._estimate_duration(actions)
            requires_approval = self._requires_approval(actions, instruction)
            
            execution_plan = ExecutionPlan(
                id=plan_id,
                actions=actions,
                description=f"Execute: {instruction.original_text}",
                estimated_duration_seconds=estimated_duration,
                requires_approval=requires_approval
            )
            
            return execution_plan
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {e}")
            
            # Return minimal fallback plan
            fallback_action = Action(
                id=str(uuid.uuid4()),
                type=ActionType.NAVIGATE,
                parameters={"url": "https://sunat.gob.pe"},
                expected_result="Navigate to government portal"
            )
            
            return ExecutionPlan(
                id=str(uuid.uuid4()),
                actions=[fallback_action],
                description=f"Fallback plan for: {instruction.original_text}",
                estimated_duration_seconds=30,
                requires_approval=True
            )
    
    async def optimize_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Optimize execution plan for efficiency.
        
        Args:
            plan: Original execution plan
            
        Returns:
            Optimized execution plan
        """
        logger.info(f"Optimizing execution plan: {plan.id}")
        
        # Create optimized copy
        optimized_actions = []
        
        for i, action in enumerate(plan.actions):
            # Skip redundant screenshots
            if (action.type == ActionType.SCREENSHOT and 
                i > 0 and 
                plan.actions[i-1].type == ActionType.SCREENSHOT):
                continue
            
            # Combine sequential wait actions
            if (action.type == ActionType.WAIT and 
                i > 0 and 
                plan.actions[i-1].type == ActionType.WAIT):
                # Extend previous wait time instead of adding new wait
                prev_action = optimized_actions[-1]
                prev_timeout = prev_action.parameters.get("timeout", 5)
                curr_timeout = action.parameters.get("timeout", 5)
                prev_action.parameters["timeout"] = max(prev_timeout, curr_timeout)
                continue
            
            # Optimize timeouts based on action type
            optimized_action = self._optimize_action(action)
            optimized_actions.append(optimized_action)
        
        # Update plan with optimized actions
        plan.actions = optimized_actions
        plan.estimated_duration_seconds = self._estimate_duration(optimized_actions)
        
        logger.info(f"Optimized plan: {len(plan.actions)} actions, {plan.estimated_duration_seconds}s estimated")
        
        return plan
    
    async def validate_plan(self, plan: ExecutionPlan) -> ValidationResult:
        """Validate execution plan for correctness and safety.
        
        Args:
            plan: Execution plan to validate
            
        Returns:
            Validation result
        """
        logger.info(f"Validating execution plan: {plan.id}")
        
        errors = []
        warnings = []
        suggestions = []
        
        # Check for required actions
        has_navigation = any(action.type == ActionType.NAVIGATE for action in plan.actions)
        if not has_navigation:
            errors.append("Plan must include at least one navigation action")
        
        # Validate action sequence
        for i, action in enumerate(plan.actions):
            # Check for missing prerequisites
            if action.type == ActionType.CLICK and i == 0:
                warnings.append("First action is a click - ensure page is loaded")
            
            if action.type == ActionType.FILL_FORM and not any(
                prev.type == ActionType.NAVIGATE for prev in plan.actions[:i]
            ):
                errors.append("Form filling requires navigation first")
            
            if action.type == ActionType.DOWNLOAD and not any(
                prev.type in [ActionType.CLICK, ActionType.NAVIGATE] 
                for prev in plan.actions[:i]
            ):
                warnings.append("Download action may need user interaction first")
            
            # Check for dangerous actions
            if action.type == ActionType.AUTHENTICATE:
                if not plan.requires_approval:
                    suggestions.append("Authentication actions should require approval")
            
            # Validate parameters
            param_validation = self._validate_action_parameters(action)
            if param_validation:
                errors.extend(param_validation)
        
        # Calculate confidence score
        confidence_score = 1.0
        if errors:
            confidence_score -= len(errors) * 0.3
        if warnings:
            confidence_score -= len(warnings) * 0.1
        
        confidence_score = max(0.0, confidence_score)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            confidence_score=confidence_score
        )
    
    def _get_template_actions(
        self, 
        instruction: ParsedInstruction
    ) -> Optional[List[Dict[str, Any]]]:
        """Get template actions based on instruction.
        
        Args:
            instruction: Parsed instruction
            
        Returns:
            Template actions or None if no template matches
        """
        if not instruction.portal_identified:
            return None
        
        portal = instruction.portal_identified.lower()
        intent = instruction.intent.type
        
        # Map intent and document types to template flows
        if portal in self.PORTAL_TEMPLATES:
            portal_templates = self.PORTAL_TEMPLATES[portal]
            
            # Check for specific document type flows
            for doc_type in instruction.document_types:
                doc_key = f"{intent.value}_{doc_type.replace(' ', '_')}"
                if doc_key in portal_templates:
                    return portal_templates[doc_key]
            
            # Check for generic intent flows
            if intent == IntentType.DOWNLOAD_DOCUMENT:
                if "download_constancia_ruc" in portal_templates:
                    return portal_templates["download_constancia_ruc"]
            elif intent == IntentType.CHECK_STATUS:
                if "check_tax_status" in portal_templates:
                    return portal_templates["check_tax_status"]
        
        return None
    
    async def _customize_template_actions(
        self, 
        template_actions: List[Dict[str, Any]],
        instruction: ParsedInstruction
    ) -> List[Action]:
        """Customize template actions with instruction-specific data.
        
        Args:
            template_actions: Template action definitions
            instruction: Parsed instruction
            
        Returns:
            List of customized actions
        """
        actions = []
        
        # Extract entity values for customization
        entity_values = {entity.type: entity.value for entity in instruction.entities}
        
        for template_action in template_actions:
            action_id = str(uuid.uuid4())
            action_type = ActionType(template_action["type"])
            
            # Build parameters from template
            parameters = {}
            expected_result = template_action.get("expected_result", f"Execute {action_type.value}")
            
            if action_type == ActionType.NAVIGATE:
                parameters["url"] = template_action.get("url", "")
                if template_action.get("section"):
                    parameters["section"] = template_action["section"]
                expected_result = f"Navigate to {parameters.get('url', 'portal')}"
            
            elif action_type == ActionType.CLICK:
                parameters["selector"] = template_action.get("selector", "")
                parameters["wait_for_element"] = True
                expected_result = f"Click element: {parameters['selector']}"
            
            elif action_type == ActionType.FILL_FORM:
                parameters["selector"] = template_action.get("wait_for", "#input")
                
                # Fill with entity values
                field = template_action.get("field")
                if field == "ruc" and "ruc" in entity_values:
                    parameters["value"] = entity_values["ruc"]
                elif field == "dni" and "dni" in entity_values:
                    parameters["value"] = entity_values["dni"]
                else:
                    parameters["field"] = field
                    parameters["value"] = template_action.get("value", "")
                
                expected_result = f"Fill form field: {field}"
            
            elif action_type == ActionType.WAIT_FOR_ELEMENT:
                parameters["selector"] = template_action.get("selector", "")
                parameters["timeout"] = template_action.get("timeout", 10)
                expected_result = f"Wait for element: {parameters['selector']}"
            
            elif action_type == ActionType.DOWNLOAD:
                parameters["wait_for"] = template_action.get("wait_for", "download")
                parameters["timeout"] = template_action.get("timeout", 30)
                expected_result = "Download file"
            
            elif action_type == ActionType.AUTHENTICATE:
                parameters["method"] = template_action.get("method", "form")
                expected_result = "Authenticate user"
            
            elif action_type == ActionType.EXTRACT_DATA:
                parameters["selector"] = template_action.get("target", "body")
                expected_result = "Extract data from page"
            
            # Create action
            action = Action(
                id=action_id,
                type=action_type,
                parameters=parameters,
                expected_result=expected_result,
                timeout_seconds=template_action.get("timeout", 30)
            )
            
            actions.append(action)
        
        return actions
    
    async def _generate_llm_actions(
        self, 
        instruction: ParsedInstruction
    ) -> List[Action]:
        """Generate actions using LLM when no template is available.
        
        Args:
            instruction: Parsed instruction
            
        Returns:
            List of generated actions
        """
        system_prompt = """You are an expert at creating step-by-step action plans for government portal automation.

Create a detailed action plan for the user's instruction. Use these action types:
- navigate: Go to a URL
- click: Click on an element (provide CSS selector)
- fill_form: Fill a form field (provide selector and value)
- wait_for_element: Wait for an element to appear
- download: Download a file
- authenticate: Log in or authenticate
- extract_data: Extract information from the page
- screenshot: Take a screenshot

Return your response as JSON array:
[
  {
    "type": "navigate",
    "parameters": {"url": "https://example.com"},
    "expected_result": "Navigate to portal homepage",
    "timeout_seconds": 30
  },
  {
    "type": "click", 
    "parameters": {"selector": "#menu-item"},
    "expected_result": "Click menu item",
    "timeout_seconds": 10
  }
]

Be specific with selectors and include appropriate timeouts."""
        
        context_info = f"""
Instruction: {instruction.original_text}
Intent: {instruction.intent.type.value}
Portal: {instruction.portal_identified or 'unknown'}
Entities: {[f"{e.type}: {e.value}" for e in instruction.entities]}
Document Types: {instruction.document_types}
"""
        
        request = LLMRequest(
            prompt=f"{context_info}\n\nCreate a step-by-step action plan for this instruction.",
            model=self.config.llm.model,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=1000
        )
        
        response = await self.llm_provider.generate_response(request)
        
        try:
            actions_data = json.loads(response.content)
            actions = []
            
            for action_data in actions_data:
                action = Action(
                    id=str(uuid.uuid4()),
                    type=ActionType(action_data["type"]),
                    parameters=action_data.get("parameters", {}),
                    expected_result=action_data.get("expected_result", ""),
                    timeout_seconds=action_data.get("timeout_seconds", 30)
                )
                actions.append(action)
            
            return actions
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse LLM actions response: {e}")
            
            # Return fallback actions
            return self._create_fallback_actions(instruction)
    
    def _create_fallback_actions(
        self, 
        instruction: ParsedInstruction
    ) -> List[Action]:
        """Create basic fallback actions.
        
        Args:
            instruction: Parsed instruction
            
        Returns:
            List of basic actions
        """
        actions = []
        
        # Basic navigation
        portal_urls = {
            "sunat": "https://sunat.gob.pe",
            "essalud": "https://essalud.gob.pe", 
            "reniec": "https://reniec.gob.pe"
        }
        
        url = portal_urls.get(
            instruction.portal_identified or "", 
            "https://www.gob.pe"
        )
        
        navigate_action = Action(
            id=str(uuid.uuid4()),
            type=ActionType.NAVIGATE,
            parameters={"url": url},
            expected_result=f"Navigate to {instruction.portal_identified or 'government'} portal"
        )
        actions.append(navigate_action)
        
        # Take screenshot for manual intervention
        screenshot_action = Action(
            id=str(uuid.uuid4()),
            type=ActionType.SCREENSHOT,
            parameters={"filename": "manual_intervention_needed"},
            expected_result="Take screenshot for manual review"
        )
        actions.append(screenshot_action)
        
        return actions
    
    def _estimate_duration(self, actions: List[Action]) -> int:
        """Estimate execution duration for actions.
        
        Args:
            actions: List of actions
            
        Returns:
            Estimated duration in seconds
        """
        duration = 0
        
        for action in actions:
            if action.type == ActionType.NAVIGATE:
                duration += 10  # Page load time
            elif action.type == ActionType.CLICK:
                duration += 2   # Click and response
            elif action.type == ActionType.FILL_FORM:
                duration += 3   # Form filling
            elif action.type == ActionType.WAIT_FOR_ELEMENT:
                duration += action.timeout_seconds
            elif action.type == ActionType.DOWNLOAD:
                duration += 15  # Download time
            elif action.type == ActionType.AUTHENTICATE:
                duration += 10  # Login process
            elif action.type == ActionType.EXTRACT_DATA:
                duration += 5   # Data extraction
            elif action.type == ActionType.SCREENSHOT:
                duration += 2   # Screenshot capture
            else:
                duration += 5   # Default
        
        # Add 20% buffer
        return int(duration * 1.2)
    
    def _requires_approval(
        self, 
        actions: List[Action], 
        instruction: ParsedInstruction
    ) -> bool:
        """Determine if plan requires human approval.
        
        Args:
            actions: List of actions
            instruction: Parsed instruction
            
        Returns:
            True if approval is required
        """
        # Authentication always requires approval
        if any(action.type == ActionType.AUTHENTICATE for action in actions):
            return True
        
        # Sensitive operations require approval
        sensitive_operations = [
            IntentType.SUBMIT_APPLICATION,
            IntentType.UPDATE_INFORMATION,
            IntentType.FILL_FORM
        ]
        
        if instruction.intent.type in sensitive_operations:
            return True
        
        # Low confidence instructions require approval
        if instruction.confidence < 0.7:
            return True
        
        return False
    
    def _optimize_action(self, action: Action) -> Action:
        """Optimize individual action parameters.
        
        Args:
            action: Action to optimize
            
        Returns:
            Optimized action
        """
        # Optimize timeouts based on action type
        if action.type == ActionType.NAVIGATE:
            action.timeout_seconds = max(action.timeout_seconds, 15)
        elif action.type == ActionType.DOWNLOAD:
            action.timeout_seconds = max(action.timeout_seconds, 30)
        elif action.type == ActionType.WAIT_FOR_ELEMENT:
            action.timeout_seconds = min(action.timeout_seconds, 20)
        
        return action
    
    def _validate_action_parameters(self, action: Action) -> List[str]:
        """Validate action parameters.
        
        Args:
            action: Action to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if action.type == ActionType.NAVIGATE:
            if not action.parameters.get("url"):
                errors.append(f"Navigate action {action.id} missing URL")
        
        elif action.type == ActionType.CLICK:
            if not action.parameters.get("selector"):
                errors.append(f"Click action {action.id} missing selector")
        
        elif action.type == ActionType.FILL_FORM:
            if not action.parameters.get("selector"):
                errors.append(f"Fill form action {action.id} missing selector")
        
        elif action.type == ActionType.WAIT_FOR_ELEMENT:
            if not action.parameters.get("selector"):
                errors.append(f"Wait action {action.id} missing selector")
        
        return errors