"""Session recording and audit trail system."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..types import Action, ActionResult, AgentState, SessionStatus
from ..config import AgentConfig
from ..utils import format_timestamp


logger = logging.getLogger(__name__)


class SessionRecording:
    """Represents a complete session recording."""
    
    def __init__(
        self,
        session_id: str,
        user_instruction: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        final_status: Optional[SessionStatus] = None
    ):
        """Initialize session recording.
        
        Args:
            session_id: Session identifier
            user_instruction: Original user instruction
            start_time: When session started
            end_time: When session ended
            final_status: Final session status
        """
        self.session_id = session_id
        self.user_instruction = user_instruction
        self.start_time = start_time
        self.end_time = end_time
        self.final_status = final_status
        
        # Recording data
        self.actions: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self.workflow_events: List[Dict[str, Any]] = []
        self.screenshots: List[str] = []
        self.llm_interactions: List[Dict[str, Any]] = []
        self.approval_events: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_action(self, action: Action) -> None:
        """Add action to recording.
        
        Args:
            action: Action being recorded
        """
        action_data = {
            "timestamp": datetime.now().isoformat(),
            "action_id": action.id,
            "action_type": action.type.value,
            "parameters": action.parameters,
            "expected_result": action.expected_result,
            "timeout_seconds": action.timeout_seconds
        }
        self.actions.append(action_data)
    
    def add_result(self, result: ActionResult) -> None:
        """Add action result to recording.
        
        Args:
            result: Action result being recorded
        """
        result_data = {
            "timestamp": datetime.now().isoformat(),
            "action_id": result.action_id,
            "success": result.success,
            "execution_time": result.execution_time,
            "screenshot_path": result.screenshot_path,
            "error_message": result.error_message,
            "data_extracted": result.data_extracted,
            "retry_count": result.retry_count
        }
        self.results.append(result_data)
    
    def add_workflow_event(
        self,
        event_type: str,
        stage: str,
        details: Dict[str, Any]
    ) -> None:
        """Add workflow event to recording.
        
        Args:
            event_type: Type of workflow event
            stage: Workflow stage
            details: Event details
        """
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "stage": stage,
            "details": details
        }
        self.workflow_events.append(event_data)
    
    def add_screenshot(self, screenshot_path: str) -> None:
        """Add screenshot to recording.
        
        Args:
            screenshot_path: Path to screenshot file
        """
        self.screenshots.append(screenshot_path)
    
    def add_llm_interaction(
        self,
        provider: str,
        model: str,
        prompt_type: str,
        response_summary: str,
        tokens_used: int,
        cost_estimate: Optional[float] = None
    ) -> None:
        """Add LLM interaction to recording.
        
        Args:
            provider: LLM provider
            model: Model used
            prompt_type: Type of prompt
            response_summary: Summary of response
            tokens_used: Number of tokens used
            cost_estimate: Estimated cost
        """
        llm_data = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "prompt_type": prompt_type,
            "response_summary": response_summary,
            "tokens_used": tokens_used,
            "cost_estimate": cost_estimate
        }
        self.llm_interactions.append(llm_data)
    
    def add_approval_event(
        self,
        event_type: str,
        description: str,
        approved: Optional[bool] = None,
        feedback: Optional[str] = None
    ) -> None:
        """Add approval event to recording.
        
        Args:
            event_type: Type of approval event
            description: Event description
            approved: Whether approved (if applicable)
            feedback: Approval feedback
        """
        approval_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "description": description,
            "approved": approved,
            "feedback": feedback
        }
        self.approval_events.append(approval_data)
    
    def add_error(
        self,
        error_type: str,
        error_message: str,
        context: Dict[str, Any]
    ) -> None:
        """Add error to recording.
        
        Args:
            error_type: Type of error
            error_message: Error message
            context: Error context
        """
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "context": context
        }
        self.errors.append(error_data)
    
    def finalize(
        self,
        end_time: datetime,
        final_status: SessionStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Finalize the session recording.
        
        Args:
            end_time: When session ended
            final_status: Final session status
            metadata: Additional metadata
        """
        self.end_time = end_time
        self.final_status = final_status
        
        if metadata:
            self.metadata.update(metadata)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert recording to dictionary for serialization.
        
        Returns:
            Dictionary representation of recording
        """
        return {
            "session_id": self.session_id,
            "user_instruction": self.user_instruction,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "final_status": self.final_status.value if self.final_status else None,
            "actions": self.actions,
            "results": self.results,
            "workflow_events": self.workflow_events,
            "screenshots": self.screenshots,
            "llm_interactions": self.llm_interactions,
            "approval_events": self.approval_events,
            "errors": self.errors,
            "metadata": self.metadata,
            "summary": self.get_summary()
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session summary statistics.
        
        Returns:
            Summary statistics
        """
        total_actions = len(self.actions)
        successful_actions = sum(1 for r in self.results if r["success"])
        total_time = sum(r["execution_time"] for r in self.results)
        total_llm_tokens = sum(i["tokens_used"] for i in self.llm_interactions)
        total_cost = sum(
            i["cost_estimate"] for i in self.llm_interactions 
            if i["cost_estimate"] is not None
        )
        
        return {
            "total_actions": total_actions,
            "successful_actions": successful_actions,
            "failed_actions": total_actions - successful_actions,
            "success_rate": successful_actions / total_actions if total_actions > 0 else 0,
            "total_execution_time": total_time,
            "total_screenshots": len(self.screenshots),
            "total_llm_interactions": len(self.llm_interactions),
            "total_llm_tokens": total_llm_tokens,
            "total_estimated_cost": total_cost,
            "total_errors": len(self.errors),
            "total_approval_events": len(self.approval_events),
            "workflow_stages_completed": len(set(e["stage"] for e in self.workflow_events))
        }


class SessionRecorder:
    """Records complete audit trail of agent sessions."""
    
    def __init__(self, config: AgentConfig):
        """Initialize session recorder.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.recordings_path = Path(config.storage_path) / "recordings"
        self.recordings_path.mkdir(parents=True, exist_ok=True)
        
        # Active recordings
        self.active_recordings: Dict[str, SessionRecording] = {}
    
    async def start_recording(self, session_id: str, user_instruction: str) -> None:
        """Start recording a new session.
        
        Args:
            session_id: Session identifier
            user_instruction: User's original instruction
        """
        logger.info(f"Starting session recording for {session_id}")
        
        recording = SessionRecording(
            session_id=session_id,
            user_instruction=user_instruction,
            start_time=datetime.now()
        )
        
        self.active_recordings[session_id] = recording
        
        # Record session start event
        recording.add_workflow_event(
            event_type="session_start",
            stage="initialization",
            details={
                "user_instruction": user_instruction,
                "config": {
                    "llm_provider": self.config.llm.provider.value,
                    "llm_model": self.config.llm.model,
                    "max_retry_attempts": self.config.max_retry_attempts,
                    "execution_timeout": self.config.execution_timeout_seconds
                }
            }
        )
    
    async def record_action(self, session_id: str, action: Action, result: ActionResult) -> None:
        """Record an action and its result.
        
        Args:
            session_id: Session identifier
            action: Action that was executed
            result: Result of the action
        """
        recording = self.active_recordings.get(session_id)
        if not recording:
            logger.warning(f"No active recording found for session {session_id}")
            return
        
        # Record action and result
        recording.add_action(action)
        recording.add_result(result)
        
        # Record screenshot if available
        if result.screenshot_path:
            recording.add_screenshot(result.screenshot_path)
        
        # Record error if action failed
        if not result.success and result.error_message:
            recording.add_error(
                error_type="action_execution_error",
                error_message=result.error_message,
                context={
                    "action_id": action.id,
                    "action_type": action.type.value,
                    "parameters": action.parameters,
                    "retry_count": result.retry_count
                }
            )
    
    async def record_workflow_event(
        self,
        session_id: str,
        event_type: str,
        stage: str,
        details: Dict[str, Any]
    ) -> None:
        """Record a workflow event.
        
        Args:
            session_id: Session identifier
            event_type: Type of workflow event
            stage: Workflow stage
            details: Event details
        """
        recording = self.active_recordings.get(session_id)
        if recording:
            recording.add_workflow_event(event_type, stage, details)
    
    async def record_llm_interaction(
        self,
        session_id: str,
        provider: str,
        model: str,
        prompt_type: str,
        response_summary: str,
        tokens_used: int,
        cost_estimate: Optional[float] = None
    ) -> None:
        """Record LLM interaction.
        
        Args:
            session_id: Session identifier
            provider: LLM provider
            model: Model used
            prompt_type: Type of prompt
            response_summary: Summary of response
            tokens_used: Number of tokens used
            cost_estimate: Estimated cost
        """
        recording = self.active_recordings.get(session_id)
        if recording:
            recording.add_llm_interaction(
                provider, model, prompt_type, response_summary, 
                tokens_used, cost_estimate
            )
    
    async def record_approval_request(
        self,
        session_id: str,
        description: str
    ) -> None:
        """Record approval request.
        
        Args:
            session_id: Session identifier
            description: Description of what requires approval
        """
        recording = self.active_recordings.get(session_id)
        if recording:
            recording.add_approval_event(
                event_type="approval_requested",
                description=description
            )
    
    async def record_approval_response(
        self,
        session_id: str,
        approved: bool,
        feedback: Optional[str] = None
    ) -> None:
        """Record approval response.
        
        Args:
            session_id: Session identifier
            approved: Whether approved
            feedback: Optional feedback
        """
        recording = self.active_recordings.get(session_id)
        if recording:
            recording.add_approval_event(
                event_type="approval_response",
                description=f"Action {'approved' if approved else 'denied'}",
                approved=approved,
                feedback=feedback
            )
    
    async def record_error(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        context: Dict[str, Any]
    ) -> None:
        """Record an error.
        
        Args:
            session_id: Session identifier
            error_type: Type of error
            error_message: Error message
            context: Error context
        """
        recording = self.active_recordings.get(session_id)
        if recording:
            recording.add_error(error_type, error_message, context)
    
    async def stop_recording(self, session_id: str, final_status: SessionStatus) -> SessionRecording:
        """Stop recording and finalize session.
        
        Args:
            session_id: Session identifier
            final_status: Final status of the session
            
        Returns:
            Completed session recording
        """
        recording = self.active_recordings.get(session_id)
        if not recording:
            raise ValueError(f"No active recording found for session {session_id}")
        
        logger.info(f"Stopping session recording for {session_id}")
        
        # Finalize recording
        recording.finalize(
            end_time=datetime.now(),
            final_status=final_status,
            metadata={
                "recording_completed": True,
                "finalized_at": datetime.now().isoformat()
            }
        )
        
        # Record final workflow event
        recording.add_workflow_event(
            event_type="session_end",
            stage="completion",
            details={
                "final_status": final_status.value,
                "summary": recording.get_summary()
            }
        )
        
        # Save to disk
        await self._save_recording(recording)
        
        # Remove from active recordings
        del self.active_recordings[session_id]
        
        return recording
    
    async def _save_recording(self, recording: SessionRecording) -> None:
        """Save recording to disk.
        
        Args:
            recording: Session recording to save
        """
        try:
            # Create filename with timestamp
            timestamp = format_timestamp(recording.start_time, "%Y%m%d_%H%M%S")
            filename = f"session_{recording.session_id}_{timestamp}.json"
            file_path = self.recordings_path / filename
            
            # Convert to dictionary and save
            recording_data = recording.to_dict()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(recording_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Session recording saved: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save session recording: {e}")
            raise
    
    def get_active_recordings(self) -> List[str]:
        """Get list of active recording session IDs.
        
        Returns:
            List of active session IDs
        """
        return list(self.active_recordings.keys())
    
    async def load_recording(self, session_id: str) -> Optional[SessionRecording]:
        """Load recording from disk.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Loaded session recording or None if not found
        """
        try:
            # Find recording file
            pattern = f"session_{session_id}_*.json"
            recording_files = list(self.recordings_path.glob(pattern))
            
            if not recording_files:
                return None
            
            # Load most recent file if multiple exist
            recording_file = max(recording_files, key=lambda p: p.stat().st_mtime)
            
            with open(recording_file, 'r', encoding='utf-8') as f:
                recording_data = json.load(f)
            
            # Reconstruct recording object
            recording = SessionRecording(
                session_id=recording_data["session_id"],
                user_instruction=recording_data["user_instruction"],
                start_time=datetime.fromisoformat(recording_data["start_time"])
            )
            
            if recording_data["end_time"]:
                recording.end_time = datetime.fromisoformat(recording_data["end_time"])
            
            if recording_data["final_status"]:
                recording.final_status = SessionStatus(recording_data["final_status"])
            
            # Load all recorded data
            recording.actions = recording_data.get("actions", [])
            recording.results = recording_data.get("results", [])
            recording.workflow_events = recording_data.get("workflow_events", [])
            recording.screenshots = recording_data.get("screenshots", [])
            recording.llm_interactions = recording_data.get("llm_interactions", [])
            recording.approval_events = recording_data.get("approval_events", [])
            recording.errors = recording_data.get("errors", [])
            recording.metadata = recording_data.get("metadata", {})
            
            return recording
            
        except Exception as e:
            logger.error(f"Failed to load recording for session {session_id}: {e}")
            return None
    
    async def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of a session recording.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session summary or None if not found
        """
        recording = await self.load_recording(session_id)
        if recording:
            return recording.get_summary()
        return None
    
    async def cleanup_old_recordings(self, days_to_keep: int = 90) -> None:
        """Clean up old recording files.
        
        Args:
            days_to_keep: Number of days of recordings to keep
        """
        import time
        
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        
        for recording_file in self.recordings_path.glob("session_*.json"):
            if recording_file.stat().st_mtime < cutoff_time:
                try:
                    recording_file.unlink()
                    logger.info(f"Cleaned up old recording: {recording_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up recording {recording_file}: {e}")
    
    async def export_recording(
        self,
        session_id: str,
        format: str = "json"
    ) -> str:
        """Export session recording in specified format.
        
        Args:
            session_id: Session identifier
            format: Export format ("json", "html", "csv")
            
        Returns:
            Path to exported file
        """
        recording = await self.load_recording(session_id)
        if not recording:
            raise ValueError(f"No recording found for session {session_id}")
        
        export_dir = self.recordings_path / "exports"
        export_dir.mkdir(exist_ok=True)
        
        timestamp = format_timestamp(datetime.now(), "%Y%m%d_%H%M%S")
        
        if format == "json":
            export_file = export_dir / f"session_{session_id}_{timestamp}.json"
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(recording.to_dict(), f, indent=2, ensure_ascii=False)
        
        elif format == "html":
            export_file = export_dir / f"session_{session_id}_{timestamp}.html"
            html_content = self._generate_html_report(recording)
            with open(export_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        elif format == "csv":
            export_file = export_dir / f"session_{session_id}_{timestamp}.csv"
            csv_content = self._generate_csv_report(recording)
            with open(export_file, 'w', encoding='utf-8') as f:
                f.write(csv_content)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return str(export_file)
    
    def _generate_html_report(self, recording: SessionRecording) -> str:
        """Generate HTML report from recording.
        
        Args:
            recording: Session recording
            
        Returns:
            HTML report content
        """
        # Simple HTML report template
        summary = recording.get_summary()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Session Recording: {recording.session_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Session Recording Report</h1>
            <h2>Session: {recording.session_id}</h2>
            
            <div class="summary">
                <h3>Summary</h3>
                <p><strong>Instruction:</strong> {recording.user_instruction}</p>
                <p><strong>Start Time:</strong> {recording.start_time}</p>
                <p><strong>End Time:</strong> {recording.end_time}</p>
                <p><strong>Final Status:</strong> {recording.final_status.value if recording.final_status else 'Unknown'}</p>
                <p><strong>Success Rate:</strong> {summary['success_rate']:.1%}</p>
                <p><strong>Total Actions:</strong> {summary['total_actions']}</p>
                <p><strong>Execution Time:</strong> {summary['total_execution_time']:.2f}s</p>
            </div>
            
            <div class="section">
                <h3>Actions</h3>
                <table>
                    <tr><th>Time</th><th>Action</th><th>Type</th><th>Result</th><th>Duration</th></tr>
        """
        
        # Add action rows
        for i, action in enumerate(recording.actions):
            result = recording.results[i] if i < len(recording.results) else None
            status_class = "success" if result and result["success"] else "error"
            status_text = "Success" if result and result["success"] else "Failed"
            duration = f"{result['execution_time']:.2f}s" if result else "N/A"
            
            html += f"""
                    <tr>
                        <td>{action['timestamp']}</td>
                        <td>{action['action_id']}</td>
                        <td>{action['action_type']}</td>
                        <td class="{status_class}">{status_text}</td>
                        <td>{duration}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_csv_report(self, recording: SessionRecording) -> str:
        """Generate CSV report from recording.
        
        Args:
            recording: Session recording
            
        Returns:
            CSV report content
        """
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            "Timestamp", "Action ID", "Action Type", "Success", 
            "Execution Time", "Error Message", "Screenshot"
        ])
        
        # Write action data
        for i, action in enumerate(recording.actions):
            result = recording.results[i] if i < len(recording.results) else None
            
            row = [
                action["timestamp"],
                action["action_id"], 
                action["action_type"],
                result["success"] if result else False,
                result["execution_time"] if result else 0,
                result["error_message"] if result and result["error_message"] else "",
                result["screenshot_path"] if result and result["screenshot_path"] else ""
            ]
            writer.writerow(row)
        
        return output.getvalue()