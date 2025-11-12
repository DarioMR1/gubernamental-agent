"""Workflow management endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from fastapi.responses import StreamingResponse

from ..types import (
    ApprovalRequest,
    ApprovalResponse,
    ExecutionPlanResponse,
    SuccessResponse,
    ListResponse,
    PaginationMeta
)
from ..middleware.auth import get_current_user, require_permission, require_role
from ...workflow import AgentWorkflow
from ...core import GovernmentalAgent
from ...config import AgentConfig


logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize workflow and agent
_agent_config = AgentConfig() 
_workflow = AgentWorkflow(_agent_config)
_agent = GovernmentalAgent(_agent_config)


@router.get(
    "/pending-approvals",
    response_model=ListResponse[ApprovalRequest],
    summary="Get pending approvals",
    description="Retrieve list of sessions requiring human approval"
)
async def get_pending_approvals(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"), 
    current_user: dict = Depends(require_permission("workflows:approve"))
):
    """Get list of sessions requiring approval."""
    
    try:
        # Get pending approvals from workflow system
        approvals_data = await _get_pending_approvals_from_storage({
            "page": page,
            "per_page": per_page
        })
        
        # Convert to API response format
        approvals = [
            ApprovalRequest(
                session_id=approval["session_id"],
                action_summary=approval["action_summary"],
                risk_level=approval["risk_level"],
                estimated_duration=approval["estimated_duration"],
                portal=approval.get("portal"),
                confidence=approval["confidence"]
            )
            for approval in approvals_data["items"]
        ]
        
        # Create pagination metadata
        pagination = PaginationMeta(
            page=page,
            per_page=per_page,
            total=approvals_data["total"],
            total_pages=(approvals_data["total"] + per_page - 1) // per_page
        )
        
        return ListResponse(
            data=approvals,
            meta=pagination
        )
        
    except Exception as e:
        logger.error(f"Failed to get pending approvals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending approvals: {str(e)}"
        )


@router.get(
    "/{session_id}/approval-request",
    response_model=SuccessResponse[ApprovalRequest],
    summary="Get approval request details",
    description="Get detailed approval request information for a specific session"
)
async def get_approval_request(
    session_id: str = Path(..., description="Session ID"),
    current_user: dict = Depends(require_permission("workflows:approve"))
):
    """Get approval request details for a session."""
    
    try:
        # Get session state from workflow
        current_state = await _workflow.get_current_state(session_id)
        
        if not current_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Check if session actually requires approval
        if current_state.status.value != "requires_approval":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session {session_id} does not require approval"
            )
        
        # Extract approval context from session
        approval_context = current_state.session_variables.get("approval_context", {})
        
        approval_request = ApprovalRequest(
            session_id=session_id,
            action_summary=approval_context.get("instruction", "No summary available"),
            risk_level=_assess_risk_level(current_state),
            estimated_duration=approval_context.get("estimated_duration", 0),
            portal=approval_context.get("portal"),
            confidence=approval_context.get("confidence", 0.0)
        )
        
        return SuccessResponse(data=approval_request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get approval request for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get approval request: {str(e)}"
        )


@router.post(
    "/{session_id}/approve",
    response_model=SuccessResponse[dict],
    summary="Approve session execution",
    description="Approve or deny execution of a session requiring human approval"
)
async def approve_session(
    session_id: str = Path(..., description="Session ID"),
    response: ApprovalResponse = ...,
    current_user: dict = Depends(require_permission("workflows:approve"))
):
    """Approve or deny session execution."""
    
    try:
        # Verify approval request exists
        await get_approval_request(session_id, current_user)
        
        # Resume workflow with approval response
        updated_state = await _workflow.resume_workflow(
            thread_id=session_id,
            approved=response.approved,
            feedback=response.feedback or ""
        )
        
        # Log approval action
        logger.info(
            f"Session {session_id} {'approved' if response.approved else 'denied'} "
            f"by user {current_user['user_id']}"
        )
        
        # Record approval in audit trail
        await _record_approval_decision(
            session_id=session_id,
            approver_id=current_user["user_id"],
            approved=response.approved,
            feedback=response.feedback,
            conditions=response.conditions
        )
        
        return SuccessResponse(
            data={
                "session_id": session_id,
                "approved": response.approved,
                "status": updated_state.status.value if updated_state else "unknown",
                "message": f"Session {'approved' if response.approved else 'denied'} successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve session: {str(e)}"
        )


@router.get(
    "/{session_id}/execution-plan",
    response_model=SuccessResponse[ExecutionPlanResponse],
    summary="Get execution plan",
    description="Retrieve the detailed execution plan for a session"
)
async def get_execution_plan(
    session_id: str = Path(..., description="Session ID"),
    current_user: dict = Depends(require_permission("workflows:read"))
):
    """Get session execution plan."""
    
    try:
        # Get session state
        current_state = await _workflow.get_current_state(session_id)
        
        if not current_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Check if user has access to this session
        session_metadata = current_state.session_variables.get("metadata", {})
        if (session_metadata.get("user_id") != current_user["user_id"] and 
            "admin" not in current_user.get("roles", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        
        # Extract execution plan
        if not current_state.execution_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution plan not found for session {session_id}"
            )
        
        plan = ExecutionPlanResponse(
            session_id=session_id,
            total_actions=current_state.execution_plan.total_actions,
            estimated_duration=current_state.execution_plan.estimated_duration_seconds,
            requires_approval=current_state.execution_plan.requires_approval,
            confidence_score=current_state.execution_plan.confidence_score,
            actions=[
                {
                    "id": action.id,
                    "type": action.type.value,
                    "parameters": action.parameters,
                    "expected_result": action.expected_result,
                    "timeout_seconds": action.timeout_seconds
                }
                for action in current_state.execution_plan.actions
            ]
        )
        
        return SuccessResponse(data=plan)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution plan for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution plan: {str(e)}"
        )


@router.get(
    "/{session_id}/stream",
    summary="Stream workflow execution",
    description="Stream real-time updates of workflow execution"
)
async def stream_workflow_execution(
    session_id: str = Path(..., description="Session ID"),
    current_user: dict = Depends(require_permission("workflows:read"))
):
    """Stream real-time workflow execution updates."""
    
    try:
        # Verify session exists and user has access
        current_state = await _workflow.get_current_state(session_id)
        
        if not current_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Check access permissions
        session_metadata = current_state.session_variables.get("metadata", {})
        if (session_metadata.get("user_id") != current_user["user_id"] and 
            "admin" not in current_user.get("roles", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        
        # Create event stream generator
        async def event_stream():
            """Generate Server-Sent Events for workflow updates."""
            
            import asyncio
            import json
            
            try:
                # Send initial state
                yield f"data: {json.dumps({'type': 'status', 'data': {'status': current_state.status.value, 'stage': current_state.current_stage.value}})}\n\n"
                
                # Monitor workflow updates
                last_update = current_state.session_variables.get("updated_at")
                
                while True:
                    # Check for updates (in production, use pub/sub or database change streams)
                    current_state = await _workflow.get_current_state(session_id)
                    
                    if current_state:
                        current_update = current_state.session_variables.get("updated_at")
                        
                        # Send update if state changed
                        if current_update != last_update:
                            event_data = {
                                "type": "update",
                                "data": {
                                    "status": current_state.status.value,
                                    "stage": current_state.current_stage.value,
                                    "progress": _calculate_progress(current_state),
                                    "current_step": current_state.current_step,
                                    "errors": bool(current_state.has_errors)
                                }
                            }
                            yield f"data: {json.dumps(event_data)}\n\n"
                            last_update = current_update
                        
                        # Stop streaming if workflow completed
                        if current_state.status.value in ["completed", "failed", "aborted"]:
                            yield f"data: {json.dumps({'type': 'complete', 'data': {'final_status': current_state.status.value}})}\n\n"
                            break
                    
                    # Wait before next check
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                logger.info(f"Stream cancelled for session {session_id}")
            except Exception as e:
                logger.error(f"Error in event stream for session {session_id}: {e}")
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Stream error occurred'}})}\n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create stream for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create execution stream: {str(e)}"
        )


@router.get(
    "/{session_id}/history",
    response_model=SuccessResponse[List[dict]],
    summary="Get workflow execution history",
    description="Retrieve the complete execution history of a workflow"
)
async def get_workflow_history(
    session_id: str = Path(..., description="Session ID"),
    current_user: dict = Depends(require_permission("workflows:read"))
):
    """Get workflow execution history."""
    
    try:
        # Verify session exists and user has access
        current_state = await _workflow.get_current_state(session_id)
        
        if not current_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Check access permissions
        session_metadata = current_state.session_variables.get("metadata", {})
        if (session_metadata.get("user_id") != current_user["user_id"] and 
            "admin" not in current_user.get("roles", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        
        # Get workflow history
        history = await _workflow.get_workflow_history(session_id)
        
        return SuccessResponse(data=history)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow history for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow history: {str(e)}"
        )


# Helper functions

def _assess_risk_level(state) -> str:
    """Assess the risk level of a session."""
    
    # Get parsed instruction info
    parsed_instruction = state.session_variables.get("parsed_instruction", {})
    intent_type = parsed_instruction.get("intent_type", "")
    portal = parsed_instruction.get("portal_identified", "")
    confidence = parsed_instruction.get("confidence", 1.0)
    
    # High risk scenarios
    if intent_type in ["submit_application", "update_information", "authenticate"]:
        return "high"
    
    if portal == "sunat" and intent_type in ["fill_form", "download_document"]:
        return "high" 
    
    # Medium risk scenarios  
    if confidence < 0.7:
        return "medium"
    
    if intent_type in ["fill_form", "download_document"]:
        return "medium"
    
    # Low risk scenarios
    return "low"


def _calculate_progress(state) -> float:
    """Calculate execution progress percentage."""
    
    if not state.execution_plan:
        return 0.0
    
    total_actions = len(state.execution_plan.actions)
    if total_actions == 0:
        return 100.0
    
    return (state.current_step / total_actions) * 100.0


async def _get_pending_approvals_from_storage(query_params: dict) -> dict:
    """Get pending approvals from storage."""
    # This would be implemented using the actual storage layer
    return {
        "items": [],
        "total": 0
    }


async def _record_approval_decision(session_id: str, approver_id: str, approved: bool, feedback: str, conditions: List[str]) -> None:
    """Record approval decision in audit trail."""
    # This would be implemented using the actual storage layer
    logger.info(f"Recording approval decision for session {session_id} by {approver_id}: {'approved' if approved else 'denied'}")
    pass