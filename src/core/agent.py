"""Main governmental agent implementation."""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from ..types import (
    AgentState,
    AgentResponse, 
    SessionStatus,
    WorkflowStage,
    ExecutionSummary,
    ApprovalRequest,
    ApprovalResponse,
    ErrorContext
)
from ..config import AgentConfig
from .state import AgentStateManager


logger = logging.getLogger(__name__)


class GovernmentalAgent:
    """Main agent class for governmental portal automation."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the governmental agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.state_manager = AgentStateManager(config)
        
        # Will be initialized in subsequent implementations
        self.instruction_parser = None  # LLM parser
        self.action_planner = None      # Action planner  
        self.executor = None            # Playwright executor
        self.workflow = None            # LangGraph workflow
        self.monitor = None             # Monitoring system
        
        # Track active executions
        self._active_executions: Dict[str, asyncio.Task] = {}
        self._approval_requests: Dict[str, ApprovalRequest] = {}
    
    async def execute_instruction(self, instruction: str) -> AgentResponse:
        """Execute a natural language instruction.
        
        Args:
            instruction: User's natural language instruction
            
        Returns:
            Agent response with execution status
        """
        logger.info(f"Received instruction: {instruction}")
        
        try:
            # Create new session
            state = await self.state_manager.create_session(instruction)
            
            # Start execution in background
            task = asyncio.create_task(self._execute_workflow(state))
            self._active_executions[state.session_id] = task
            
            # Return immediate response
            return AgentResponse(
                session_id=state.session_id,
                status=SessionStatus.RUNNING,
                message="Instruction received and processing started",
                progress_percentage=0.0,
                current_stage=WorkflowStage.INSTRUCTION_PARSING,
                estimated_completion=None
            )
            
        except Exception as e:
            logger.error(f"Error starting instruction execution: {e}")
            return AgentResponse(
                session_id="",
                status=SessionStatus.FAILED,
                message=f"Failed to start execution: {str(e)}",
                progress_percentage=0.0,
                current_stage=WorkflowStage.ERROR_HANDLING
            )
    
    async def get_status(self, session_id: str) -> Optional[AgentResponse]:
        """Get current status of a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Current agent response or None if session not found
        """
        state = await self.state_manager.get_session(session_id)
        if not state:
            return None
        
        # Calculate estimated completion time
        estimated_completion = None
        if state.execution_plan and state.progress_percentage > 0:
            # Simple estimation based on current progress
            # In a real implementation, this would be more sophisticated
            elapsed_time = 0
            if state.execution_history:
                total_execution_time = sum(r.execution_time for r in state.execution_history)
                remaining_progress = 100 - state.progress_percentage
                if state.progress_percentage > 0:
                    estimated_remaining = (total_execution_time / state.progress_percentage) * remaining_progress
                    estimated_completion = datetime.now().timestamp() + estimated_remaining
        
        # Check if approval is required
        requires_approval = session_id in self._approval_requests
        approval_message = None
        if requires_approval:
            approval_req = self._approval_requests[session_id]
            approval_message = f"Approval required: {approval_req.action_description}"
        
        return AgentResponse(
            session_id=state.session_id,
            status=state.status,
            message=self._get_status_message(state),
            progress_percentage=state.progress_percentage,
            current_stage=state.current_stage,
            next_action=self._get_next_action_description(state),
            estimated_completion=datetime.fromtimestamp(estimated_completion) if estimated_completion else None,
            requires_approval=requires_approval,
            approval_message=approval_message
        )
    
    async def abort_execution(self, session_id: str) -> bool:
        """Abort an ongoing execution.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successfully aborted, False otherwise
        """
        logger.info(f"Aborting execution for session {session_id}")
        
        # Cancel the execution task
        if session_id in self._active_executions:
            task = self._active_executions[session_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass  # Expected when cancelling
            
            del self._active_executions[session_id]
        
        # Update session status
        await self.state_manager.update_status(session_id, SessionStatus.ABORTED)
        
        # Clean up any pending approval requests
        self._approval_requests.pop(session_id, None)
        
        return True
    
    async def approve_action(
        self, 
        session_id: str, 
        approved: bool, 
        feedback: Optional[str] = None
    ) -> bool:
        """Respond to an approval request.
        
        Args:
            session_id: Session identifier
            approved: Whether the action is approved
            feedback: Optional feedback from approver
            
        Returns:
            True if approval was processed, False if no pending approval
        """
        if session_id not in self._approval_requests:
            return False
        
        approval_request = self._approval_requests[session_id]
        
        response = ApprovalResponse(
            session_id=session_id,
            approved=approved,
            feedback=feedback
        )
        
        # Store approval response in session variables
        await self.state_manager.set_session_variable(
            session_id, 
            "approval_response", 
            response
        )
        
        # Remove from pending approvals
        del self._approval_requests[session_id]
        
        # Update session status
        if approved:
            await self.state_manager.update_status(session_id, SessionStatus.RUNNING)
        else:
            await self.state_manager.update_status(session_id, SessionStatus.ABORTED)
        
        logger.info(f"Approval {'granted' if approved else 'denied'} for session {session_id}")
        return True
    
    async def get_execution_summary(self, session_id: str) -> Optional[ExecutionSummary]:
        """Get execution summary for a completed session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Execution summary or None if session not found or not completed
        """
        state = await self.state_manager.get_session(session_id)
        if not state or not state.is_completed:
            return None
        
        successful_actions = sum(1 for r in state.execution_history if r.success)
        failed_actions = len(state.execution_history) - successful_actions
        total_time = sum(r.execution_time for r in state.execution_history)
        
        # Extract files and data
        files_downloaded = []
        data_extracted = {}
        screenshots_taken = []
        error_messages = []
        
        for result in state.execution_history:
            if result.screenshot_path:
                screenshots_taken.append(result.screenshot_path)
            
            if result.error_message:
                error_messages.append(result.error_message)
            
            if result.data_extracted:
                data_extracted.update(result.data_extracted)
        
        return ExecutionSummary(
            session_id=session_id,
            success=state.status == SessionStatus.COMPLETED,
            total_actions=len(state.execution_history),
            successful_actions=successful_actions,
            failed_actions=failed_actions,
            execution_time_seconds=total_time,
            files_downloaded=files_downloaded,
            data_extracted=data_extracted,
            screenshots_taken=screenshots_taken,
            error_messages=error_messages
        )
    
    async def list_sessions(self) -> list[Dict[str, Any]]:
        """List all sessions with summary information.
        
        Returns:
            List of session summaries
        """
        session_ids = await self.state_manager.list_active_sessions()
        summaries = []
        
        for session_id in session_ids:
            summary = await self.state_manager.get_session_summary(session_id)
            if summary:
                summaries.append(summary)
        
        return summaries
    
    async def _execute_workflow(self, state: AgentState) -> None:
        """Execute the complete workflow for a session.
        
        Args:
            state: Initial agent state
        """
        try:
            logger.info(f"Starting workflow execution for session {state.session_id}")
            
            # Update status to running
            await self.state_manager.update_status(state.session_id, SessionStatus.RUNNING)
            
            # For now, this is a placeholder that simulates workflow execution
            # In the full implementation, this will orchestrate:
            # 1. Instruction parsing with LLM
            # 2. Action planning
            # 3. Execution with Playwright
            # 4. Error handling and recovery
            # 5. Human approval when needed
            
            await self._simulate_workflow_execution(state)
            
        except asyncio.CancelledError:
            logger.info(f"Workflow execution cancelled for session {state.session_id}")
            raise
        except Exception as e:
            logger.error(f"Workflow execution failed for session {state.session_id}: {e}")
            
            error_context = ErrorContext(
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=str(e)
            )
            
            await self.state_manager.set_error(state.session_id, error_context)
        finally:
            # Clean up active execution
            self._active_executions.pop(state.session_id, None)
    
    async def _simulate_workflow_execution(self, state: AgentState) -> None:
        """Simulate workflow execution (placeholder implementation).
        
        Args:
            state: Agent state
        """
        # This is a placeholder that simulates the workflow stages
        # Replace with actual LangGraph workflow implementation
        
        stages = [
            WorkflowStage.INSTRUCTION_PARSING,
            WorkflowStage.PLAN_CREATION, 
            WorkflowStage.PLAN_VALIDATION,
            WorkflowStage.EXECUTION,
            WorkflowStage.RESULT_VALIDATION,
            WorkflowStage.COMPLETION
        ]
        
        for i, stage in enumerate(stages):
            await self.state_manager.update_stage(state.session_id, stage)
            
            # Simulate work
            await asyncio.sleep(1)
            
            logger.info(f"Session {state.session_id} completed stage: {stage.value}")
        
        # Mark as completed
        await self.state_manager.update_status(state.session_id, SessionStatus.COMPLETED)
        logger.info(f"Workflow completed for session {state.session_id}")
    
    def _get_status_message(self, state: AgentState) -> str:
        """Get human-readable status message.
        
        Args:
            state: Agent state
            
        Returns:
            Status message
        """
        if state.status == SessionStatus.PENDING:
            return "Session created, waiting to start"
        elif state.status == SessionStatus.RUNNING:
            return f"Executing: {state.current_stage.value.replace('_', ' ').title()}"
        elif state.status == SessionStatus.COMPLETED:
            return "Execution completed successfully"
        elif state.status == SessionStatus.FAILED:
            error_msg = state.error_context.error_message if state.error_context else "Unknown error"
            return f"Execution failed: {error_msg}"
        elif state.status == SessionStatus.REQUIRES_APPROVAL:
            return "Waiting for human approval"
        elif state.status == SessionStatus.ABORTED:
            return "Execution aborted by user"
        elif state.status == SessionStatus.PAUSED:
            return "Execution paused"
        else:
            return f"Status: {state.status.value}"
    
    def _get_next_action_description(self, state: AgentState) -> Optional[str]:
        """Get description of next action to be performed.
        
        Args:
            state: Agent state
            
        Returns:
            Next action description or None
        """
        if not state.execution_plan or state.current_step >= len(state.execution_plan.actions):
            return None
        
        next_action = state.execution_plan.actions[state.current_step]
        return f"{next_action.type.value}: {next_action.expected_result}"