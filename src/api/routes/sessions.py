"""Session management endpoints."""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Path, HTTPException, status, Request
from fastapi.responses import FileResponse

from ..types import (
    CreateSessionRequest,
    SessionResponse, 
    UpdateSessionRequest,
    SessionListQuery,
    SuccessResponse,
    ListResponse,
    PaginationMeta,
    SessionHistoryResponse,
    DownloadFileRequest
)
from ..middleware.auth import get_current_user, require_permission
from ...core import GovernmentalAgent
from ...types import AgentState, SessionStatus
from ...config import AgentConfig


logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize agent (in production, this would be dependency injection)
_agent_config = AgentConfig()
_agent = GovernmentalAgent(_agent_config)


@router.post(
    "/",
    response_model=SuccessResponse[SessionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create new session",
    description="Create a new agent session with a natural language instruction"
)
async def create_session(
    request: CreateSessionRequest,
    current_user: dict = Depends(require_permission("sessions:create"))
):
    """Create a new agent session."""
    
    try:
        # Create session using the agent
        result = await _agent.execute_instruction(
            instruction=request.instruction,
            metadata={
                "priority": request.priority,
                "timeout_seconds": request.timeout_seconds,
                "user_id": current_user["user_id"],
                "created_by": current_user["username"],
                **request.metadata or {}
            }
        )
        
        # Convert agent result to API response
        session_response = SessionResponse(
            id=result.session_id,
            instruction=request.instruction,
            status=result.status,
            stage=result.current_stage,
            priority=request.priority,
            progress_percentage=result.progress_percentage,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            completed_at=None,
            metadata=request.metadata or {}
        )
        
        logger.info(f"Created session {result.session_id} for user {current_user['user_id']}")
        
        return SuccessResponse(
            data=session_response,
            meta={
                "request_id": getattr(request, "state", {}).get("request_id"),
                "estimated_duration": request.timeout_seconds
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get(
    "/",
    response_model=ListResponse[SessionResponse], 
    summary="List sessions",
    description="Retrieve a paginated list of sessions with optional filtering"
)
async def list_sessions(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[SessionStatus] = Query(None, alias="status", description="Filter by status"),
    created_after: Optional[datetime] = Query(None, description="Filter sessions created after this date"),
    created_before: Optional[datetime] = Query(None, description="Filter sessions created before this date"),
    current_user: dict = Depends(require_permission("sessions:read"))
):
    """List sessions with pagination and filtering."""
    
    try:
        # Build query parameters
        query_params = {
            "page": page,
            "per_page": per_page,
            "user_id": current_user["user_id"],  # Users can only see their own sessions
        }
        
        if status_filter:
            query_params["status"] = status_filter
        if created_after:
            query_params["created_after"] = created_after
        if created_before:
            query_params["created_before"] = created_before
        
        # Get sessions from storage (this would be implemented in storage layer)
        sessions_data = await _get_sessions_from_storage(query_params)
        
        # Convert to API response format
        sessions = [
            SessionResponse(
                id=session["id"],
                instruction=session["instruction"],
                status=SessionStatus(session["status"]),
                stage=session["stage"],
                priority=session.get("priority", 1),
                progress_percentage=session.get("progress_percentage", 0.0),
                created_at=session["created_at"],
                updated_at=session["updated_at"],
                completed_at=session.get("completed_at"),
                metadata=session.get("metadata", {})
            )
            for session in sessions_data["items"]
        ]
        
        # Create pagination metadata
        pagination = PaginationMeta(
            page=page,
            per_page=per_page,
            total=sessions_data["total"],
            total_pages=(sessions_data["total"] + per_page - 1) // per_page
        )
        
        return ListResponse(
            data=sessions,
            meta=pagination
        )
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get(
    "/{session_id}",
    response_model=SuccessResponse[SessionResponse],
    summary="Get session details", 
    description="Retrieve detailed information about a specific session"
)
async def get_session(
    session_id: str = Path(..., description="Session ID"),
    current_user: dict = Depends(require_permission("sessions:read"))
):
    """Get session details by ID."""
    
    try:
        # Get session status from agent
        agent_status = await _agent.get_status(session_id)
        
        if not agent_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Verify user has access to this session
        session_metadata = agent_status.get("metadata", {})
        if session_metadata.get("user_id") != current_user["user_id"]:
            # Check if user has admin permissions
            if "admin" not in current_user.get("roles", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this session"
                )
        
        # Convert to API response
        session_response = SessionResponse(
            id=session_id,
            instruction=agent_status["instruction"],
            status=agent_status["status"],
            stage=agent_status["current_stage"], 
            priority=session_metadata.get("priority", 1),
            progress_percentage=agent_status.get("progress_percentage", 0.0),
            created_at=session_metadata.get("created_at", datetime.now()),
            updated_at=agent_status.get("updated_at", datetime.now()),
            completed_at=agent_status.get("completed_at"),
            metadata=session_metadata
        )
        
        return SuccessResponse(data=session_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@router.patch(
    "/{session_id}",
    response_model=SuccessResponse[SessionResponse],
    summary="Update session",
    description="Update session properties like priority or metadata"
)
async def update_session(
    session_id: str = Path(..., description="Session ID"),
    request: UpdateSessionRequest = ...,
    current_user: dict = Depends(require_permission("sessions:update"))
):
    """Update session properties."""
    
    try:
        # Verify session exists and user has access
        session = await get_session(session_id, current_user)
        
        # Update session properties
        updates = {}
        if request.priority is not None:
            updates["priority"] = request.priority
        if request.metadata is not None:
            updates["metadata"] = {
                **session.data.metadata,
                **request.metadata
            }
        
        # Apply updates (this would be implemented in storage layer)
        await _update_session_in_storage(session_id, updates)
        
        # Return updated session
        return await get_session(session_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete session",
    description="Delete a session and all its associated data"
)
async def delete_session(
    session_id: str = Path(..., description="Session ID"),
    current_user: dict = Depends(require_permission("sessions:delete"))
):
    """Delete a session."""
    
    try:
        # Verify session exists and user has access
        await get_session(session_id, current_user)
        
        # Abort if session is running
        agent_status = await _agent.get_status(session_id)
        if agent_status and agent_status["status"] == SessionStatus.RUNNING:
            await _agent.abort_execution(session_id)
        
        # Delete session from storage
        await _delete_session_from_storage(session_id)
        
        logger.info(f"Deleted session {session_id} by user {current_user['user_id']}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.post(
    "/{session_id}/abort",
    response_model=SuccessResponse[SessionResponse],
    summary="Abort session execution",
    description="Stop execution of a running session"
)
async def abort_session(
    session_id: str = Path(..., description="Session ID"),
    current_user: dict = Depends(require_permission("sessions:control"))
):
    """Abort session execution."""
    
    try:
        # Verify session exists and user has access
        await get_session(session_id, current_user)
        
        # Abort execution
        await _agent.abort_execution(session_id)
        
        # Return updated session status
        return await get_session(session_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to abort session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to abort session: {str(e)}"
        )


@router.get(
    "/{session_id}/history",
    response_model=SuccessResponse[SessionHistoryResponse],
    summary="Get session execution history",
    description="Retrieve detailed execution history for a session"
)
async def get_session_history(
    session_id: str = Path(..., description="Session ID"),
    current_user: dict = Depends(require_permission("sessions:read"))
):
    """Get session execution history."""
    
    try:
        # Verify session exists and user has access
        await get_session(session_id, current_user)
        
        # Get history from storage
        history_data = await _get_session_history_from_storage(session_id)
        
        # Convert to API response
        history = SessionHistoryResponse(
            session_id=session_id,
            actions=history_data.get("actions", []),
            workflow_steps=history_data.get("workflow_steps", []),
            screenshots=history_data.get("screenshots", []),
            logs=history_data.get("logs", [])
        )
        
        return SuccessResponse(data=history)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session history {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session history: {str(e)}"
        )


@router.get(
    "/{session_id}/downloads/{file_id}",
    summary="Download session file",
    description="Download a file that was generated or downloaded during session execution"
)
async def download_session_file(
    session_id: str = Path(..., description="Session ID"),
    file_id: str = Path(..., description="File ID"),
    current_user: dict = Depends(require_permission("sessions:read"))
):
    """Download a file from a session."""
    
    try:
        # Verify session exists and user has access  
        await get_session(session_id, current_user)
        
        # Get file path from storage
        file_path = await _get_session_file_path(session_id, file_id)
        
        if not file_path or not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found in session {session_id}"
            )
        
        # Return file
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file {file_id} from session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )


# Helper functions (would be implemented in storage/service layer)

async def _get_sessions_from_storage(query_params: dict) -> dict:
    """Get sessions from storage with pagination."""
    # This would be implemented using the actual storage layer
    # For now, return mock data
    return {
        "items": [],
        "total": 0
    }


async def _update_session_in_storage(session_id: str, updates: dict) -> None:
    """Update session in storage."""
    # This would be implemented using the actual storage layer
    pass


async def _delete_session_from_storage(session_id: str) -> None:
    """Delete session from storage."""
    # This would be implemented using the actual storage layer  
    pass


async def _get_session_history_from_storage(session_id: str) -> dict:
    """Get session history from storage."""
    # This would be implemented using the actual storage layer
    return {
        "actions": [],
        "workflow_steps": [],
        "screenshots": [],
        "logs": []
    }


async def _get_session_file_path(session_id: str, file_id: str):
    """Get file path for session file."""
    # This would be implemented using the actual storage layer
    from pathlib import Path
    return Path(f"./storage/sessions/{session_id}/files/{file_id}")  # Mock path