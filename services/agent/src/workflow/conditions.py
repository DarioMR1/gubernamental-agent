"""Workflow conditions for LangGraph routing decisions."""

import logging
from typing import Literal

from ..types import AgentState, SessionStatus


logger = logging.getLogger(__name__)


class WorkflowConditions:
    """Contains all workflow condition functions for LangGraph routing."""
    
    def should_request_approval(
        self, 
        state: AgentState
    ) -> Literal["approve", "execute", "error"]:
        """Determine if human approval is required.
        
        Args:
            state: Current agent state
            
        Returns:
            Next step: "approve", "execute", or "error"
        """
        try:
            # Check if there are validation errors
            if state.has_errors:
                return "error"
            
            # Check if plan validation failed
            plan_validation = state.session_variables.get("plan_validation", {})
            if not plan_validation.get("valid", True):
                return "error"
            
            # Check if execution plan requires approval
            if state.execution_plan and state.execution_plan.requires_approval:
                return "approve"
            
            # Check confidence threshold
            parsed_instruction = state.session_variables.get("parsed_instruction", {})
            confidence = parsed_instruction.get("confidence", 1.0)
            
            if confidence < 0.7:  # Low confidence threshold
                return "approve"
            
            # Check for sensitive operations
            intent_type = parsed_instruction.get("intent_type", "")
            sensitive_intents = [
                "submit_application",
                "update_information", 
                "authenticate",
                "fill_form"
            ]
            
            if intent_type in sensitive_intents:
                return "approve"
            
            # Default to execute
            return "execute"
            
        except Exception as e:
            logger.error(f"Error in should_request_approval: {e}")
            return "error"
    
    def approval_granted(
        self, 
        state: AgentState
    ) -> Literal["approved", "denied", "timeout"]:
        """Check approval response.
        
        Args:
            state: Current agent state
            
        Returns:
            Approval result: "approved", "denied", or "timeout"
        """
        try:
            # Check if approval was granted
            approval_granted = state.session_variables.get("approval_granted")
            
            if approval_granted is None:
                # Still waiting for approval
                return "timeout"
            elif approval_granted:
                return "approved"
            else:
                return "denied"
                
        except Exception as e:
            logger.error(f"Error in approval_granted: {e}")
            return "denied"
    
    def should_continue_execution(
        self, 
        state: AgentState
    ) -> Literal["continue", "validate", "error", "complete"]:
        """Determine if execution should continue.
        
        Args:
            state: Current agent state
            
        Returns:
            Next step: "continue", "validate", "error", or "complete"
        """
        try:
            # Check for errors
            if state.has_errors:
                return "error"
            
            # Check if execution is marked as completed
            if state.session_variables.get("execution_completed", False):
                return "validate"
            
            # Check if we have more actions to execute
            if not state.execution_plan:
                return "complete"
            
            if state.current_step >= len(state.execution_plan.actions):
                return "validate"
            
            # Check if last action failed
            if state.execution_history:
                last_result = state.execution_history[-1]
                if not last_result.success:
                    return "error"
            
            # Continue with next action
            return "continue"
            
        except Exception as e:
            logger.error(f"Error in should_continue_execution: {e}")
            return "error"
    
    def should_retry_or_complete(
        self, 
        state: AgentState
    ) -> Literal["retry", "complete", "error"]:
        """Determine if we should retry failed actions or complete.
        
        Args:
            state: Current agent state
            
        Returns:
            Next step: "retry", "complete", or "error"
        """
        try:
            # Get validation results
            validation_results = state.session_variables.get("validation_results", {})
            validation_passed = validation_results.get("validation_passed", False)
            
            if validation_passed:
                return "complete"
            
            # Check if we have failed actions that can be retried
            failed_actions = [
                result for result in state.execution_history 
                if not result.success and result.retry_count < 3
            ]
            
            if failed_actions:
                return "retry"
            
            # If validation failed and no retries available, it's an error
            return "error"
            
        except Exception as e:
            logger.error(f"Error in should_retry_or_complete: {e}")
            return "error"
    
    def should_retry_after_error(
        self, 
        state: AgentState
    ) -> Literal["retry", "abort", "human_intervention"]:
        """Determine error recovery strategy.
        
        Args:
            state: Current agent state
            
        Returns:
            Recovery strategy: "retry", "abort", or "human_intervention"
        """
        try:
            # Get recovery strategy set by error handling node
            recovery_strategy = state.session_variables.get("recovery_strategy", "abort")
            
            if recovery_strategy == "retry":
                return "retry"
            elif recovery_strategy == "human_intervention":
                return "human_intervention"
            else:
                return "abort"
                
        except Exception as e:
            logger.error(f"Error in should_retry_after_error: {e}")
            return "abort"
    
    def is_execution_complete(self, state: AgentState) -> bool:
        """Check if execution is complete.
        
        Args:
            state: Current agent state
            
        Returns:
            True if execution is complete
        """
        try:
            # Check if explicitly marked as completed
            if state.session_variables.get("execution_completed", False):
                return True
            
            # Check if all actions have been executed
            if state.execution_plan:
                return state.current_step >= len(state.execution_plan.actions)
            
            return False
            
        except Exception as e:
            logger.error(f"Error in is_execution_complete: {e}")
            return False
    
    def requires_human_intervention(self, state: AgentState) -> bool:
        """Check if human intervention is required.
        
        Args:
            state: Current agent state
            
        Returns:
            True if human intervention is needed
        """
        try:
            # Check error context
            if state.error_context:
                error_type = state.error_context.error_type
                retry_count = state.error_context.retry_count
                
                # Certain errors always require human intervention
                human_intervention_errors = [
                    "authentication_failed",
                    "captcha_required", 
                    "plan_validation_failed",
                    "approval_timeout"
                ]
                
                if error_type in human_intervention_errors:
                    return True
                
                # After multiple retries, require intervention
                if retry_count >= 3:
                    return True
            
            # Check if approval is pending for too long
            approval_requested = state.session_variables.get("approval_requested_at")
            if approval_requested and state.status == SessionStatus.REQUIRES_APPROVAL:
                # In a real implementation, you'd check timestamp
                return False  # For now, assume approval is still pending
            
            return False
            
        except Exception as e:
            logger.error(f"Error in requires_human_intervention: {e}")
            return True  # Default to requiring intervention on error
    
    def should_take_screenshot(self, state: AgentState) -> bool:
        """Determine if a screenshot should be taken.
        
        Args:
            state: Current agent state
            
        Returns:
            True if screenshot should be taken
        """
        try:
            # Take screenshots on errors
            if state.has_errors:
                return True
            
            # Take screenshots at key stages
            key_stages = [
                "plan_validation",
                "execution", 
                "result_validation",
                "completion"
            ]
            
            return state.current_stage.value in key_stages
            
        except Exception as e:
            logger.error(f"Error in should_take_screenshot: {e}")
            return False
    
    def can_proceed_without_approval(self, state: AgentState) -> bool:
        """Check if execution can proceed without human approval.
        
        Args:
            state: Current agent state
            
        Returns:
            True if can proceed without approval
        """
        try:
            # Check confidence threshold
            parsed_instruction = state.session_variables.get("parsed_instruction", {})
            confidence = parsed_instruction.get("confidence", 0.0)
            
            if confidence < 0.8:
                return False
            
            # Check for read-only operations
            intent_type = parsed_instruction.get("intent_type", "")
            safe_intents = [
                "search_information",
                "check_status", 
                "navigate_portal",
                "download_document"  # If document is public
            ]
            
            if intent_type in safe_intents:
                return True
            
            # Check portal risk level
            portal = parsed_instruction.get("portal_identified", "")
            high_risk_portals = ["sunat"]  # SUNAT operations are typically sensitive
            
            if portal in high_risk_portals:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in can_proceed_without_approval: {e}")
            return False  # Default to requiring approval