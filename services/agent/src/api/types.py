"""API-specific types for requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Generic, TypeVar
from enum import Enum

from pydantic import BaseModel, Field, validator
from ..types import SessionStatus, WorkflowStage, ActionType


T = TypeVar('T')


# =============================================================================
# Base Response Types
# =============================================================================

class ErrorDetail(BaseModel):
    """Error detail structure."""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: ErrorDetail


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response format."""
    data: T = Field(..., description="Response data")
    meta: Optional[Dict[str, Any]] = Field(None, description="Response metadata")


class ListResponse(BaseModel, Generic[T]):
    """Paginated list response format."""
    data: List[T] = Field(..., description="List of items")
    meta: PaginationMeta = Field(..., description="Pagination information")


# =============================================================================
# Session Management Types
# =============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create a new session."""
    instruction: str = Field(
        ..., 
        min_length=1, 
        max_length=1000, 
        description="Natural language instruction for the agent"
    )
    priority: int = Field(
        1, 
        ge=1, 
        le=5, 
        description="Session priority (1=lowest, 5=highest)"
    )
    timeout_seconds: Optional[int] = Field(
        300, 
        ge=30, 
        le=3600, 
        description="Maximum execution timeout in seconds"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata for the session"
    )
    
    @validator('instruction')
    def validate_instruction(cls, v):
        """Validate instruction content."""
        if not v.strip():
            raise ValueError("Instruction cannot be empty or only whitespace")
        return v.strip()


class SessionResponse(BaseModel):
    """Session information response."""
    id: str = Field(..., description="Unique session identifier")
    instruction: str = Field(..., description="Original user instruction")
    status: SessionStatus = Field(..., description="Current session status")
    stage: WorkflowStage = Field(..., description="Current workflow stage")
    priority: int = Field(..., description="Session priority")
    progress_percentage: float = Field(
        ..., 
        ge=0.0, 
        le=100.0, 
        description="Execution progress percentage"
    )
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    metadata: Dict[str, Any] = Field({}, description="Session metadata")
    
    class Config:
        use_enum_values = True


class UpdateSessionRequest(BaseModel):
    """Request to update session properties."""
    priority: Optional[int] = Field(None, ge=1, le=5)
    metadata: Optional[Dict[str, Any]] = Field(None)


class SessionListQuery(BaseModel):
    """Query parameters for listing sessions."""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    status: Optional[SessionStatus] = Field(None, description="Filter by status")
    stage: Optional[WorkflowStage] = Field(None, description="Filter by stage")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date")


# =============================================================================
# Workflow Management Types  
# =============================================================================

class ApprovalRequest(BaseModel):
    """Human approval request details."""
    session_id: str = Field(..., description="Session requiring approval")
    action_summary: str = Field(..., description="Summary of actions to be performed")
    risk_level: str = Field(..., description="Risk assessment level")
    estimated_duration: int = Field(..., description="Estimated duration in seconds")
    portal: Optional[str] = Field(None, description="Target portal")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score")


class ApprovalResponse(BaseModel):
    """Human approval response."""
    approved: bool = Field(..., description="Whether the action is approved")
    feedback: Optional[str] = Field(None, description="Human feedback or instructions")
    conditions: Optional[List[str]] = Field(None, description="Approval conditions")


class ActionExecutionResult(BaseModel):
    """Result of an executed action."""
    action_id: str = Field(..., description="Action identifier")
    action_type: ActionType = Field(..., description="Type of action executed")
    success: bool = Field(..., description="Whether the action succeeded")
    execution_time: float = Field(..., description="Execution time in seconds")
    screenshot_path: Optional[str] = Field(None, description="Path to screenshot")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    data_extracted: Optional[Dict[str, Any]] = Field(None, description="Extracted data")
    retry_count: int = Field(0, description="Number of retry attempts")
    
    class Config:
        use_enum_values = True


class ExecutionPlanResponse(BaseModel):
    """Execution plan information."""
    session_id: str = Field(..., description="Session identifier")
    total_actions: int = Field(..., description="Total number of planned actions")
    estimated_duration: int = Field(..., description="Estimated duration in seconds")
    requires_approval: bool = Field(..., description="Whether human approval is needed")
    confidence_score: float = Field(..., description="Plan confidence score")
    actions: List[Dict[str, Any]] = Field(..., description="Planned actions")


class SessionHistoryResponse(BaseModel):
    """Session execution history."""
    session_id: str = Field(..., description="Session identifier")
    actions: List[ActionExecutionResult] = Field(..., description="Executed actions")
    workflow_steps: List[Dict[str, Any]] = Field(..., description="Workflow execution steps")
    screenshots: List[str] = Field(..., description="Screenshot file paths")
    logs: List[Dict[str, Any]] = Field(..., description="Execution logs")


# =============================================================================
# Health Check Types
# =============================================================================

class HealthStatus(str, Enum):
    """Health check status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Individual component health status."""
    status: HealthStatus = Field(..., description="Component health status")
    message: Optional[str] = Field(None, description="Status message")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    last_check: datetime = Field(..., description="Last health check timestamp")


class HealthResponse(BaseModel):
    """Overall application health response."""
    status: HealthStatus = Field(..., description="Overall application status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Health check timestamp")
    components: Dict[str, ComponentHealth] = Field(..., description="Component health details")
    
    class Config:
        use_enum_values = True


# =============================================================================
# File Management Types
# =============================================================================

class FileUploadResponse(BaseModel):
    """File upload response."""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    size_bytes: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="File MIME type")
    upload_url: str = Field(..., description="URL to access the file")
    uploaded_at: datetime = Field(..., description="Upload timestamp")


class DownloadFileRequest(BaseModel):
    """Request to download a file from a session."""
    session_id: str = Field(..., description="Session that downloaded the file")
    file_type: str = Field(..., description="Type of file to download")
    format: Optional[str] = Field("original", description="Desired file format")


# =============================================================================
# Analytics and Reporting Types
# =============================================================================

class SessionMetrics(BaseModel):
    """Session execution metrics."""
    total_sessions: int = Field(..., description="Total number of sessions")
    successful_sessions: int = Field(..., description="Successfully completed sessions")
    failed_sessions: int = Field(..., description="Failed sessions")
    pending_sessions: int = Field(..., description="Currently pending sessions")
    average_duration: float = Field(..., description="Average session duration in seconds")
    success_rate: float = Field(..., description="Success rate percentage")


class PortalMetrics(BaseModel):
    """Portal-specific metrics."""
    portal_name: str = Field(..., description="Portal identifier")
    total_operations: int = Field(..., description="Total operations performed")
    success_rate: float = Field(..., description="Success rate for this portal")
    average_duration: float = Field(..., description="Average operation duration")
    common_errors: List[str] = Field(..., description="Most common error types")


class SystemMetrics(BaseModel):
    """System performance metrics."""
    sessions: SessionMetrics = Field(..., description="Session-related metrics")
    portals: List[PortalMetrics] = Field(..., description="Portal-specific metrics")
    system_uptime: float = Field(..., description="System uptime in seconds")
    active_sessions: int = Field(..., description="Currently active sessions")
    queue_length: int = Field(..., description="Pending sessions in queue")