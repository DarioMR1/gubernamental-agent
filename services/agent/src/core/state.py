"""Agent state management."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..types import (
    AgentState, 
    SessionStatus, 
    WorkflowStage, 
    ActionResult, 
    ExecutionPlan,
    ErrorContext
)
from ..config import AgentConfig


class AgentStateManager:
    """Manages agent state persistence and retrieval."""
    
    def __init__(self, config: AgentConfig):
        """Initialize state manager.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.storage_path = Path(config.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for active sessions
        self._active_sessions: Dict[str, AgentState] = {}
        self._lock = asyncio.Lock()
    
    async def create_session(
        self, 
        user_instruction: str,
        session_id: Optional[str] = None
    ) -> AgentState:
        """Create a new agent session.
        
        Args:
            user_instruction: User's natural language instruction
            session_id: Optional custom session ID. If None, generates UUID
            
        Returns:
            New agent state
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        state = AgentState(
            session_id=session_id,
            user_instruction=user_instruction,
            status=SessionStatus.PENDING,
            current_stage=WorkflowStage.INSTRUCTION_PARSING
        )
        
        async with self._lock:
            self._active_sessions[session_id] = state
        
        await self._persist_state(state)
        return state
    
    async def get_session(self, session_id: str) -> Optional[AgentState]:
        """Get session state by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Agent state if found, None otherwise
        """
        async with self._lock:
            # Check in-memory cache first
            if session_id in self._active_sessions:
                return self._active_sessions[session_id]
        
        # Try to load from disk
        state = await self._load_state(session_id)
        if state:
            async with self._lock:
                self._active_sessions[session_id] = state
        
        return state
    
    async def update_session(self, state: AgentState) -> None:
        """Update session state.
        
        Args:
            state: Updated agent state
        """
        state.updated_at = datetime.now()
        
        async with self._lock:
            self._active_sessions[state.session_id] = state
        
        await self._persist_state(state)
    
    async def update_status(self, session_id: str, status: SessionStatus) -> None:
        """Update session status.
        
        Args:
            session_id: Session identifier
            status: New status
        """
        state = await self.get_session(session_id)
        if state:
            state.update_status(status)
            await self.update_session(state)
    
    async def update_stage(self, session_id: str, stage: WorkflowStage) -> None:
        """Update workflow stage.
        
        Args:
            session_id: Session identifier
            stage: New workflow stage
        """
        state = await self.get_session(session_id)
        if state:
            state.update_stage(stage)
            await self.update_session(state)
    
    async def set_execution_plan(
        self, 
        session_id: str, 
        plan: ExecutionPlan
    ) -> None:
        """Set execution plan for session.
        
        Args:
            session_id: Session identifier
            plan: Execution plan
        """
        state = await self.get_session(session_id)
        if state:
            state.execution_plan = plan
            await self.update_session(state)
    
    async def add_action_result(
        self, 
        session_id: str, 
        result: ActionResult
    ) -> None:
        """Add action result to session history.
        
        Args:
            session_id: Session identifier
            result: Action result to add
        """
        state = await self.get_session(session_id)
        if state:
            state.add_action_result(result)
            
            # Update current step if this was a successful step
            if result.success and state.execution_plan:
                state.current_step += 1
            
            await self.update_session(state)
    
    async def set_error(
        self, 
        session_id: str, 
        error_context: ErrorContext
    ) -> None:
        """Set error context for session.
        
        Args:
            session_id: Session identifier
            error_context: Error context
        """
        state = await self.get_session(session_id)
        if state:
            state.set_error(error_context)
            await self.update_session(state)
    
    async def clear_error(self, session_id: str) -> None:
        """Clear error context for session.
        
        Args:
            session_id: Session identifier
        """
        state = await self.get_session(session_id)
        if state:
            state.clear_error()
            await self.update_session(state)
    
    async def set_session_variable(
        self, 
        session_id: str, 
        key: str, 
        value: Any
    ) -> None:
        """Set session variable.
        
        Args:
            session_id: Session identifier
            key: Variable key
            value: Variable value
        """
        state = await self.get_session(session_id)
        if state:
            state.session_variables[key] = value
            await self.update_session(state)
    
    async def get_session_variable(
        self, 
        session_id: str, 
        key: str,
        default: Any = None
    ) -> Any:
        """Get session variable.
        
        Args:
            session_id: Session identifier
            key: Variable key
            default: Default value if key not found
            
        Returns:
            Variable value or default
        """
        state = await self.get_session(session_id)
        if state:
            return state.session_variables.get(key, default)
        return default
    
    async def list_active_sessions(self) -> List[str]:
        """Get list of active session IDs.
        
        Returns:
            List of active session IDs
        """
        async with self._lock:
            return list(self._active_sessions.keys())
    
    async def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session summary information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session summary dictionary
        """
        state = await self.get_session(session_id)
        if not state:
            return None
        
        return {
            "session_id": state.session_id,
            "user_instruction": state.user_instruction,
            "status": state.status.value,
            "current_stage": state.current_stage.value,
            "progress_percentage": state.progress_percentage,
            "created_at": state.created_at.isoformat() if state.created_at else None,
            "updated_at": state.updated_at.isoformat() if state.updated_at else None,
            "has_errors": state.has_errors,
            "total_actions": state.execution_plan.total_actions if state.execution_plan else 0,
            "completed_actions": len(state.execution_history),
            "current_step": state.current_step
        }
    
    async def cleanup_session(self, session_id: str) -> None:
        """Clean up session from memory and optionally disk.
        
        Args:
            session_id: Session identifier
        """
        async with self._lock:
            self._active_sessions.pop(session_id, None)
        
        # Note: We keep session files on disk for audit purposes
        # They can be cleaned up separately by a maintenance process
    
    async def _persist_state(self, state: AgentState) -> None:
        """Persist state to disk.
        
        Args:
            state: Agent state to persist
        """
        file_path = self.storage_path / f"{state.session_id}.json"
        
        # Convert state to serializable dictionary
        state_dict = {
            "session_id": state.session_id,
            "user_instruction": state.user_instruction,
            "status": state.status.value,
            "current_stage": state.current_stage.value,
            "current_step": state.current_step,
            "session_variables": state.session_variables,
            "created_at": state.created_at.isoformat() if state.created_at else None,
            "updated_at": state.updated_at.isoformat() if state.updated_at else None,
        }
        
        # Add execution plan if available
        if state.execution_plan:
            state_dict["execution_plan"] = {
                "id": state.execution_plan.id,
                "description": state.execution_plan.description,
                "estimated_duration_seconds": state.execution_plan.estimated_duration_seconds,
                "requires_approval": state.execution_plan.requires_approval,
                "created_at": state.execution_plan.created_at.isoformat() if state.execution_plan.created_at else None,
                "actions": [
                    {
                        "id": action.id,
                        "type": action.type.value,
                        "parameters": action.parameters,
                        "expected_result": action.expected_result,
                        "timeout_seconds": action.timeout_seconds,
                        "retry_attempts": action.retry_attempts,
                        "created_at": action.created_at.isoformat() if action.created_at else None,
                    }
                    for action in state.execution_plan.actions
                ]
            }
        
        # Add execution history
        state_dict["execution_history"] = [
            {
                "action_id": result.action_id,
                "success": result.success,
                "execution_time": result.execution_time,
                "screenshot_path": result.screenshot_path,
                "error_message": result.error_message,
                "data_extracted": result.data_extracted,
                "retry_count": result.retry_count,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            }
            for result in state.execution_history
        ]
        
        # Add error context if available
        if state.error_context:
            state_dict["error_context"] = {
                "error_type": state.error_context.error_type,
                "error_message": state.error_context.error_message,
                "action_id": state.error_context.action_id,
                "screenshot_path": state.error_context.screenshot_path,
                "stack_trace": state.error_context.stack_trace,
                "retry_count": state.error_context.retry_count,
                "occurred_at": state.error_context.occurred_at.isoformat() if state.error_context.occurred_at else None,
            }
        
        # Write to file atomically
        temp_file = file_path.with_suffix(".tmp")
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)
            temp_file.replace(file_path)
        except Exception:
            # Clean up temp file if write failed
            if temp_file.exists():
                temp_file.unlink()
            raise
    
    async def _load_state(self, session_id: str) -> Optional[AgentState]:
        """Load state from disk.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Loaded agent state or None if not found
        """
        file_path = self.storage_path / f"{session_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                state_dict = json.load(f)
            
            # Reconstruct AgentState from dictionary
            # This is a simplified reconstruction - in a full implementation,
            # you'd want more robust deserialization logic
            
            state = AgentState(
                session_id=state_dict["session_id"],
                user_instruction=state_dict["user_instruction"],
                status=SessionStatus(state_dict["status"]),
                current_stage=WorkflowStage(state_dict["current_stage"]),
                current_step=state_dict.get("current_step", 0),
                session_variables=state_dict.get("session_variables", {}),
                created_at=datetime.fromisoformat(state_dict["created_at"]) if state_dict.get("created_at") else None,
                updated_at=datetime.fromisoformat(state_dict["updated_at"]) if state_dict.get("updated_at") else None,
            )
            
            # TODO: Reconstruct execution_plan, execution_history, error_context
            # This would require importing and reconstructing the dataclass objects
            
            return state
            
        except Exception as e:
            # Log error but don't raise - return None to indicate state couldn't be loaded
            # In a full implementation, you'd want proper logging here
            print(f"Error loading state for session {session_id}: {e}")
            return None