"""Workflow nodes for LangGraph execution."""

import logging
from datetime import datetime

from ..types import AgentState, SessionStatus, WorkflowStage, ErrorContext
from ..config import AgentConfig
from ..llm import InstructionParser, ActionPlanner
from ..executor import PlaywrightExecutor


logger = logging.getLogger(__name__)


class WorkflowNodes:
    """Contains all workflow node implementations."""
    
    def __init__(self, config: AgentConfig):
        """Initialize workflow nodes.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        
        # Initialize components
        self.instruction_parser = InstructionParser(config)
        self.action_planner = ActionPlanner(config)
        self.executor = PlaywrightExecutor(config)
        
    async def instruction_parsing_node(self, state: AgentState) -> AgentState:
        """Parse user instruction using LLM.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        logger.info(f"Parsing instruction for session {state.session_id}")
        
        try:
            # Update stage
            state.current_stage = WorkflowStage.INSTRUCTION_PARSING
            state.status = SessionStatus.RUNNING
            
            # Parse the instruction
            parsed_instruction = await self.instruction_parser.parse_instruction(
                state.user_instruction
            )
            
            # Store parsed instruction in session variables
            state.session_variables["parsed_instruction"] = {
                "intent_type": parsed_instruction.intent.type.value,
                "intent_confidence": parsed_instruction.intent.confidence,
                "entities": [
                    {
                        "type": entity.type,
                        "value": entity.value,
                        "confidence": entity.confidence
                    }
                    for entity in parsed_instruction.entities
                ],
                "portal_identified": parsed_instruction.portal_identified,
                "document_types": parsed_instruction.document_types,
                "confidence": parsed_instruction.confidence
            }
            
            logger.info(
                f"Instruction parsed successfully. Intent: {parsed_instruction.intent.type.value}, "
                f"Confidence: {parsed_instruction.confidence:.2f}"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Instruction parsing failed: {e}")
            
            state.set_error(ErrorContext(
                error_type="instruction_parsing_failed",
                error_message=str(e)
            ))
            
            return state
    
    async def planning_node(self, state: AgentState) -> AgentState:
        """Create execution plan from parsed instruction.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        logger.info(f"Creating execution plan for session {state.session_id}")
        
        try:
            # Update stage
            state.current_stage = WorkflowStage.PLAN_CREATION
            
            # Get parsed instruction from session variables
            parsed_instruction_data = state.session_variables.get("parsed_instruction")
            if not parsed_instruction_data:
                raise ValueError("No parsed instruction found in session variables")
            
            # Reconstruct parsed instruction (simplified for this example)
            # In a full implementation, you'd have proper serialization/deserialization
            from ..types import ParsedInstruction, Intent, IntentType, Entity
            
            intent = Intent(
                type=IntentType(parsed_instruction_data["intent_type"]),
                confidence=parsed_instruction_data["intent_confidence"]
            )
            
            entities = [
                Entity(
                    type=entity_data["type"],
                    value=entity_data["value"],
                    confidence=entity_data["confidence"],
                    start_pos=0,
                    end_pos=0
                )
                for entity_data in parsed_instruction_data["entities"]
            ]
            
            parsed_instruction = ParsedInstruction(
                original_text=state.user_instruction,
                intent=intent,
                entities=entities,
                portal_identified=parsed_instruction_data["portal_identified"],
                document_types=parsed_instruction_data["document_types"],
                confidence=parsed_instruction_data["confidence"]
            )
            
            # Create execution plan
            execution_plan = await self.action_planner.create_execution_plan(parsed_instruction)
            
            # Optimize the plan
            execution_plan = await self.action_planner.optimize_plan(execution_plan)
            
            # Store in state
            state.execution_plan = execution_plan
            
            logger.info(
                f"Execution plan created with {execution_plan.total_actions} actions. "
                f"Estimated duration: {execution_plan.estimated_duration_seconds}s"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            
            state.set_error(ErrorContext(
                error_type="planning_failed",
                error_message=str(e)
            ))
            
            return state
    
    async def plan_validation_node(self, state: AgentState) -> AgentState:
        """Validate execution plan for safety and correctness.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        logger.info(f"Validating execution plan for session {state.session_id}")
        
        try:
            # Update stage
            state.current_stage = WorkflowStage.PLAN_VALIDATION
            
            if not state.execution_plan:
                raise ValueError("No execution plan found")
            
            # Validate the plan
            validation_result = await self.action_planner.validate_plan(state.execution_plan)
            
            # Store validation result
            state.session_variables["plan_validation"] = {
                "valid": validation_result.valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "suggestions": validation_result.suggestions,
                "confidence_score": validation_result.confidence_score
            }
            
            if not validation_result.valid:
                state.set_error(ErrorContext(
                    error_type="plan_validation_failed",
                    error_message=f"Plan validation failed: {', '.join(validation_result.errors)}"
                ))
            
            logger.info(
                f"Plan validation completed. Valid: {validation_result.valid}, "
                f"Confidence: {validation_result.confidence_score:.2f}"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Plan validation failed: {e}")
            
            state.set_error(ErrorContext(
                error_type="plan_validation_error",
                error_message=str(e)
            ))
            
            return state
    
    async def human_approval_node(self, state: AgentState) -> AgentState:
        """Request human approval for sensitive operations.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        logger.info(f"Requesting human approval for session {state.session_id}")
        
        try:
            # Update stage and status
            state.current_stage = WorkflowStage.APPROVAL_WAITING
            state.status = SessionStatus.REQUIRES_APPROVAL
            
            # Create approval request context
            approval_context = {
                "instruction": state.user_instruction,
                "planned_actions": len(state.execution_plan.actions) if state.execution_plan else 0,
                "estimated_duration": state.execution_plan.estimated_duration_seconds if state.execution_plan else 0,
                "portal": state.session_variables.get("parsed_instruction", {}).get("portal_identified"),
                "confidence": state.session_variables.get("parsed_instruction", {}).get("confidence", 0)
            }
            
            state.session_variables["approval_context"] = approval_context
            state.session_variables["approval_requested_at"] = datetime.now().isoformat()
            
            logger.info(f"Human approval requested for session {state.session_id}")
            
            return state
            
        except Exception as e:
            logger.error(f"Approval request failed: {e}")
            
            state.set_error(ErrorContext(
                error_type="approval_request_failed",
                error_message=str(e)
            ))
            
            return state
    
    async def execution_node(self, state: AgentState) -> AgentState:
        """Execute the next action in the plan.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        logger.info(f"Executing action for session {state.session_id}")
        
        try:
            # Update stage
            state.current_stage = WorkflowStage.EXECUTION
            state.status = SessionStatus.RUNNING
            
            if not state.execution_plan:
                raise ValueError("No execution plan found")
            
            # Get current action to execute
            if state.current_step >= len(state.execution_plan.actions):
                # All actions completed
                state.session_variables["execution_completed"] = True
                return state
            
            current_action = state.execution_plan.actions[state.current_step]
            
            # Start executor if not already started
            if not state.session_variables.get("executor_started", False):
                await self.executor.start()
                state.session_variables["executor_started"] = True
            
            # Execute the action
            result = await self.executor.execute_action(current_action)
            
            # Add result to execution history
            state.add_action_result(result)
            
            # Update current step if successful
            if result.success:
                state.current_step += 1
            
            logger.info(
                f"Action {current_action.id} executed. "
                f"Success: {result.success}, Time: {result.execution_time:.2f}s"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            
            state.set_error(ErrorContext(
                error_type="execution_failed",
                error_message=str(e),
                action_id=state.execution_plan.actions[state.current_step].id if state.execution_plan and state.current_step < len(state.execution_plan.actions) else None
            ))
            
            return state
    
    async def result_validation_node(self, state: AgentState) -> AgentState:
        """Validate execution results.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        logger.info(f"Validating results for session {state.session_id}")
        
        try:
            # Update stage
            state.current_stage = WorkflowStage.RESULT_VALIDATION
            
            # Simple validation: check if we have any successful actions
            successful_actions = sum(1 for result in state.execution_history if result.success)
            total_actions = len(state.execution_history)
            
            success_rate = successful_actions / total_actions if total_actions > 0 else 0
            
            state.session_variables["validation_results"] = {
                "successful_actions": successful_actions,
                "total_actions": total_actions,
                "success_rate": success_rate,
                "validation_passed": success_rate >= 0.8  # 80% success rate threshold
            }
            
            logger.info(
                f"Result validation completed. Success rate: {success_rate:.2f} "
                f"({successful_actions}/{total_actions})"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Result validation failed: {e}")
            
            state.set_error(ErrorContext(
                error_type="result_validation_failed",
                error_message=str(e)
            ))
            
            return state
    
    async def error_handling_node(self, state: AgentState) -> AgentState:
        """Handle errors and determine recovery strategy.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        logger.info(f"Handling error for session {state.session_id}")
        
        try:
            # Update stage
            state.current_stage = WorkflowStage.ERROR_HANDLING
            
            if not state.error_context:
                # No error to handle, continue
                return state
            
            # Analyze error and determine strategy
            error_type = state.error_context.error_type
            retry_count = state.error_context.retry_count
            
            # Increment retry count
            state.error_context.retry_count += 1
            
            # Determine recovery strategy
            if retry_count < self.config.max_retry_attempts:
                if error_type in ["execution_failed", "action_timeout"]:
                    state.session_variables["recovery_strategy"] = "retry"
                else:
                    state.session_variables["recovery_strategy"] = "human_intervention"
            else:
                state.session_variables["recovery_strategy"] = "abort"
            
            logger.info(
                f"Error handled. Type: {error_type}, Retry: {retry_count}, "
                f"Strategy: {state.session_variables.get('recovery_strategy')}"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error handling failed: {e}")
            
            # Set final error state
            state.status = SessionStatus.FAILED
            state.session_variables["recovery_strategy"] = "abort"
            
            return state
    
    async def completion_node(self, state: AgentState) -> AgentState:
        """Complete the workflow execution.
        
        Args:
            state: Current agent state
            
        Returns:
            Final agent state
        """
        logger.info(f"Completing workflow for session {state.session_id}")
        
        try:
            # Update stage
            state.current_stage = WorkflowStage.COMPLETION
            
            # Determine final status
            if state.session_variables.get("aborted", False):
                state.status = SessionStatus.ABORTED
            elif state.session_variables.get("execution_completed", False):
                state.status = SessionStatus.COMPLETED
            elif state.has_errors:
                state.status = SessionStatus.FAILED
            else:
                state.status = SessionStatus.COMPLETED
            
            # Clean up executor
            if state.session_variables.get("executor_started", False):
                await self.executor.cleanup()
                state.session_variables["executor_started"] = False
            
            # Store completion metadata
            state.session_variables["completed_at"] = datetime.now().isoformat()
            state.session_variables["final_status"] = state.status.value
            
            logger.info(f"Workflow completed with status: {state.status.value}")
            
            return state
            
        except Exception as e:
            logger.error(f"Completion failed: {e}")
            
            state.status = SessionStatus.FAILED
            state.set_error(ErrorContext(
                error_type="completion_failed",
                error_message=str(e)
            ))
            
            return state