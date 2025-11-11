"""Action type definitions for the governmental agent."""

from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


class ActionType(Enum):
    """Defines the types of actions the agent can perform."""
    
    NAVIGATE = "navigate"
    CLICK = "click" 
    FILL_FORM = "fill_form"
    DOWNLOAD = "download"
    WAIT = "wait"
    AUTHENTICATE = "authenticate"
    SCREENSHOT = "screenshot"
    EXTRACT_DATA = "extract_data"
    UPLOAD_FILE = "upload_file"
    SELECT_DROPDOWN = "select_dropdown"
    SCROLL = "scroll"
    WAIT_FOR_ELEMENT = "wait_for_element"


@dataclass
class Action:
    """Represents a single action to be executed by the agent."""
    
    id: str
    type: ActionType
    parameters: Dict[str, Any]
    expected_result: str
    timeout_seconds: int = 30
    retry_attempts: int = 3
    created_at: datetime = None
    
    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ActionResult:
    """Result of executing an action."""
    
    action_id: str
    success: bool
    execution_time: float
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    data_extracted: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    completed_at: datetime = None
    
    def __post_init__(self) -> None:
        if self.completed_at is None:
            self.completed_at = datetime.now()


@dataclass
class ExecutionPlan:
    """Complete execution plan containing multiple actions."""
    
    id: str
    actions: list[Action]
    description: str
    estimated_duration_seconds: int
    requires_approval: bool = False
    created_at: datetime = None
    
    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def total_actions(self) -> int:
        """Get total number of actions in the plan."""
        return len(self.actions)
    
    def get_action_by_id(self, action_id: str) -> Optional[Action]:
        """Get action by its ID."""
        for action in self.actions:
            if action.id == action_id:
                return action
        return None