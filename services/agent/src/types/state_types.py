"""State type definitions for the governmental agent."""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .action_types import ActionResult, ExecutionPlan


class SessionStatus(Enum):
    """Status of an agent session."""
    
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires_approval"
    ABORTED = "aborted"
    PAUSED = "paused"


class WorkflowStage(Enum):
    """Stages of the agent workflow."""
    
    INSTRUCTION_PARSING = "instruction_parsing"
    PLAN_CREATION = "plan_creation"
    PLAN_VALIDATION = "plan_validation"
    EXECUTION = "execution"
    APPROVAL_WAITING = "approval_waiting"
    RESULT_VALIDATION = "result_validation"
    COMPLETION = "completion"
    ERROR_HANDLING = "error_handling"


@dataclass
class ErrorContext:
    """Context information for errors during execution."""
    
    error_type: str
    error_message: str
    action_id: Optional[str] = None
    screenshot_path: Optional[str] = None
    stack_trace: Optional[str] = None
    retry_count: int = 0
    occurred_at: datetime = None
    
    def __post_init__(self) -> None:
        if self.occurred_at is None:
            self.occurred_at = datetime.now()


@dataclass
class AgentState:
    """Complete state of the agent during execution."""
    
    session_id: str
    user_instruction: str
    status: SessionStatus
    current_stage: WorkflowStage
    execution_plan: Optional[ExecutionPlan] = None
    current_step: int = 0
    execution_history: List[ActionResult] = field(default_factory=list)
    session_variables: Dict[str, Any] = field(default_factory=dict)
    error_context: Optional[ErrorContext] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def update_status(self, status: SessionStatus) -> None:
        """Update the session status and timestamp."""
        self.status = status
        self.updated_at = datetime.now()
    
    def update_stage(self, stage: WorkflowStage) -> None:
        """Update the current workflow stage."""
        self.current_stage = stage
        self.updated_at = datetime.now()
    
    def add_action_result(self, result: ActionResult) -> None:
        """Add an action result to the execution history."""
        self.execution_history.append(result)
        self.updated_at = datetime.now()
        
        if not result.success:
            self.error_context = ErrorContext(
                error_type="action_failed",
                error_message=result.error_message or "Action failed",
                action_id=result.action_id,
                screenshot_path=result.screenshot_path
            )
    
    def set_error(self, error_context: ErrorContext) -> None:
        """Set error context and update status."""
        self.error_context = error_context
        self.status = SessionStatus.FAILED
        self.updated_at = datetime.now()
    
    def clear_error(self) -> None:
        """Clear error context."""
        self.error_context = None
        self.updated_at = datetime.now()
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage based on completed actions."""
        if not self.execution_plan:
            return 0.0
        
        total_actions = self.execution_plan.total_actions
        if total_actions == 0:
            return 100.0
        
        completed_actions = len(self.execution_history)
        return min(100.0, (completed_actions / total_actions) * 100)
    
    @property
    def has_errors(self) -> bool:
        """Check if the session has any errors."""
        return self.error_context is not None
    
    @property
    def is_completed(self) -> bool:
        """Check if the session is completed."""
        return self.status == SessionStatus.COMPLETED
    
    @property
    def is_running(self) -> bool:
        """Check if the session is currently running."""
        return self.status == SessionStatus.RUNNING
    
    @property
    def requires_approval(self) -> bool:
        """Check if the session requires human approval."""
        return self.status == SessionStatus.REQUIRES_APPROVAL