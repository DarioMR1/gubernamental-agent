"""Response type definitions for the governmental agent."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from .state_types import SessionStatus, WorkflowStage


@dataclass
class AgentResponse:
    """Response from the agent containing current status and progress."""
    
    session_id: str
    status: SessionStatus
    message: str
    progress_percentage: float
    current_stage: WorkflowStage
    next_action: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    requires_approval: bool = False
    approval_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ExecutionSummary:
    """Summary of a completed execution."""
    
    session_id: str
    success: bool
    total_actions: int
    successful_actions: int
    failed_actions: int
    execution_time_seconds: float
    files_downloaded: List[str] = None
    data_extracted: Dict[str, Any] = None
    screenshots_taken: List[str] = None
    error_messages: List[str] = None
    completed_at: datetime = None
    
    def __post_init__(self) -> None:
        if self.files_downloaded is None:
            self.files_downloaded = []
        if self.data_extracted is None:
            self.data_extracted = {}
        if self.screenshots_taken is None:
            self.screenshots_taken = []
        if self.error_messages is None:
            self.error_messages = []
        if self.completed_at is None:
            self.completed_at = datetime.now()
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of actions."""
        if self.total_actions == 0:
            return 100.0
        return (self.successful_actions / self.total_actions) * 100


@dataclass
class ApprovalRequest:
    """Request for human approval during execution."""
    
    session_id: str
    action_description: str
    risk_level: str  # "low", "medium", "high"
    context: Dict[str, Any]
    screenshot_path: Optional[str] = None
    timeout_seconds: int = 300  # 5 minutes default
    created_at: datetime = None
    
    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ApprovalResponse:
    """Response to an approval request."""
    
    session_id: str
    approved: bool
    feedback: Optional[str] = None
    modifications: Dict[str, Any] = None
    responded_at: datetime = None
    
    def __post_init__(self) -> None:
        if self.modifications is None:
            self.modifications = {}
        if self.responded_at is None:
            self.responded_at = datetime.now()


@dataclass
class ValidationResult:
    """Result of validating an execution plan or action."""
    
    valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    confidence_score: float = 1.0
    validated_at: datetime = None
    
    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []
        if self.validated_at is None:
            self.validated_at = datetime.now()
    
    @property
    def has_errors(self) -> bool:
        """Check if validation found any errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if validation found any warnings."""
        return len(self.warnings) > 0