"""Structured logging system for the governmental agent."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog

from ..types import Action, ActionResult, AgentState, SessionStatus
from ..config import AgentConfig
from ..utils import format_execution_log


class StructuredLogger:
    """Structured logger for governmental agent operations."""
    
    def __init__(self, config: AgentConfig):
        """Initialize structured logger.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.logs_path = Path(config.logs_path)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Configure structlog
        self._configure_structlog()
        
        # Get logger instance
        self.logger = structlog.get_logger("gubernamental_agent")
        
        # Session-specific loggers
        self.session_loggers: Dict[str, structlog.BoundLogger] = {}
    
    def _configure_structlog(self) -> None:
        """Configure structlog with appropriate processors and handlers."""
        # Determine log format
        if self.config.monitoring.log_format == "json":
            renderer = structlog.processors.JSONRenderer()
        else:
            renderer = structlog.processors.KeyValueRenderer()
        
        # Configure processors
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer
        ]
        
        # Configure structlog
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, self.config.monitoring.log_level)
            ),
            context_class=dict,
            logger_factory=self._create_logger_factory(),
            cache_logger_on_first_use=True
        )
    
    def _create_logger_factory(self) -> Any:
        """Create logger factory with file and console handlers."""
        # Create main logger
        logger = logging.getLogger("gubernamental_agent")
        logger.setLevel(getattr(logging, self.config.monitoring.log_level))
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.config.monitoring.log_level))
        
        # File handler for all logs
        log_file = self.logs_path / "agent.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always capture all levels in file
        
        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.propagate = False
        
        return structlog.stdlib.LoggerFactory()
    
    def get_session_logger(self, session_id: str) -> structlog.BoundLogger:
        """Get or create a session-specific logger.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Bound logger with session context
        """
        if session_id not in self.session_loggers:
            # Create session-specific file handler
            session_log_file = self.logs_path / f"session_{session_id}.log"
            session_handler = logging.FileHandler(session_log_file, encoding='utf-8')
            session_handler.setLevel(logging.DEBUG)
            
            # Create session logger
            session_logger = logging.getLogger(f"gubernamental_agent.session.{session_id}")
            session_logger.addHandler(session_handler)
            session_logger.setLevel(logging.DEBUG)
            
            # Create bound logger with session context
            self.session_loggers[session_id] = structlog.get_logger(
                f"gubernamental_agent.session.{session_id}"
            ).bind(session_id=session_id)
        
        return self.session_loggers[session_id]
    
    def log_session_start(self, state: AgentState) -> None:
        """Log session start.
        
        Args:
            state: Agent state
        """
        session_logger = self.get_session_logger(state.session_id)
        
        session_logger.info(
            "Session started",
            user_instruction=state.user_instruction,
            status=state.status.value,
            stage=state.current_stage.value,
            timestamp=datetime.now().isoformat()
        )
    
    def log_session_end(self, state: AgentState) -> None:
        """Log session completion.
        
        Args:
            state: Final agent state
        """
        session_logger = self.get_session_logger(state.session_id)
        
        # Calculate metrics
        total_actions = len(state.execution_history)
        successful_actions = sum(1 for r in state.execution_history if r.success)
        total_time = sum(r.execution_time for r in state.execution_history)
        
        session_logger.info(
            "Session completed",
            final_status=state.status.value,
            final_stage=state.current_stage.value,
            total_actions=total_actions,
            successful_actions=successful_actions,
            success_rate=successful_actions / total_actions if total_actions > 0 else 0,
            total_execution_time=total_time,
            progress_percentage=state.progress_percentage,
            has_errors=state.has_errors,
            error_message=state.error_context.error_message if state.error_context else None,
            timestamp=datetime.now().isoformat()
        )
    
    def log_action_start(self, action: Action, session_id: str) -> None:
        """Log action execution start.
        
        Args:
            action: Action being executed
            session_id: Session identifier
        """
        session_logger = self.get_session_logger(session_id)
        
        session_logger.info(
            "Action started",
            action_id=action.id,
            action_type=action.type.value,
            action_parameters=action.parameters,
            expected_result=action.expected_result,
            timeout_seconds=action.timeout_seconds,
            timestamp=datetime.now().isoformat()
        )
    
    def log_action_success(
        self, 
        action: Action, 
        result: ActionResult, 
        session_id: str
    ) -> None:
        """Log successful action execution.
        
        Args:
            action: Action that was executed
            result: Action result
            session_id: Session identifier
        """
        session_logger = self.get_session_logger(session_id)
        
        log_entry = format_execution_log(
            session_id=session_id,
            action_id=action.id,
            action_type=action.type.value,
            status="success",
            duration=result.execution_time,
            details={
                "screenshot_path": result.screenshot_path,
                "data_extracted": result.data_extracted,
                "retry_count": result.retry_count
            }
        )
        
        session_logger.info(
            "Action completed successfully",
            **log_entry
        )
    
    def log_action_error(
        self, 
        action: Action, 
        result: ActionResult, 
        session_id: str
    ) -> None:
        """Log failed action execution.
        
        Args:
            action: Action that failed
            result: Action result with error
            session_id: Session identifier
        """
        session_logger = self.get_session_logger(session_id)
        
        log_entry = format_execution_log(
            session_id=session_id,
            action_id=action.id,
            action_type=action.type.value,
            status="error",
            duration=result.execution_time,
            details={
                "error_message": result.error_message,
                "screenshot_path": result.screenshot_path,
                "retry_count": result.retry_count
            }
        )
        
        session_logger.error(
            "Action failed",
            **log_entry
        )
    
    def log_workflow_stage(
        self, 
        session_id: str, 
        stage: str, 
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log workflow stage transition.
        
        Args:
            session_id: Session identifier
            stage: Workflow stage name
            status: Stage status
            metadata: Additional metadata
        """
        session_logger = self.get_session_logger(session_id)
        
        log_data = {
            "workflow_stage": stage,
            "stage_status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if metadata:
            log_data.update(metadata)
        
        session_logger.info(
            f"Workflow stage: {stage}",
            **log_data
        )
    
    def log_llm_request(
        self,
        session_id: str,
        provider: str,
        model: str,
        prompt_length: int,
        response_tokens: int,
        cost_estimate: Optional[float] = None,
        response_time_ms: int = 0
    ) -> None:
        """Log LLM API request.
        
        Args:
            session_id: Session identifier
            provider: LLM provider name
            model: Model used
            prompt_length: Length of prompt
            response_tokens: Tokens in response
            cost_estimate: Estimated cost
            response_time_ms: Response time in milliseconds
        """
        session_logger = self.get_session_logger(session_id)
        
        session_logger.debug(
            "LLM request completed",
            llm_provider=provider,
            llm_model=model,
            prompt_length=prompt_length,
            response_tokens=response_tokens,
            cost_estimate=cost_estimate,
            response_time_ms=response_time_ms,
            timestamp=datetime.now().isoformat()
        )
    
    def log_approval_request(
        self,
        session_id: str,
        action_description: str,
        risk_level: str,
        context: Dict[str, Any]
    ) -> None:
        """Log human approval request.
        
        Args:
            session_id: Session identifier
            action_description: Description of action requiring approval
            risk_level: Risk level assessment
            context: Additional context
        """
        session_logger = self.get_session_logger(session_id)
        
        session_logger.warning(
            "Human approval requested",
            action_description=action_description,
            risk_level=risk_level,
            approval_context=context,
            timestamp=datetime.now().isoformat()
        )
    
    def log_approval_response(
        self,
        session_id: str,
        approved: bool,
        feedback: Optional[str] = None,
        response_time_seconds: Optional[float] = None
    ) -> None:
        """Log human approval response.
        
        Args:
            session_id: Session identifier
            approved: Whether action was approved
            feedback: Optional feedback from approver
            response_time_seconds: Time taken to respond
        """
        session_logger = self.get_session_logger(session_id)
        
        session_logger.info(
            f"Approval {'granted' if approved else 'denied'}",
            approved=approved,
            feedback=feedback,
            response_time_seconds=response_time_seconds,
            timestamp=datetime.now().isoformat()
        )
    
    def log_security_event(
        self,
        session_id: str,
        event_type: str,
        description: str,
        severity: str = "medium",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log security-related events.
        
        Args:
            session_id: Session identifier
            event_type: Type of security event
            description: Event description
            severity: Event severity (low, medium, high, critical)
            metadata: Additional metadata
        """
        session_logger = self.get_session_logger(session_id)
        
        log_data = {
            "security_event_type": event_type,
            "security_severity": severity,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        
        if metadata:
            log_data.update(metadata)
        
        # Log at appropriate level based on severity
        log_level = {
            "low": "info",
            "medium": "warning", 
            "high": "error",
            "critical": "critical"
        }.get(severity, "warning")
        
        getattr(session_logger, log_level)(
            f"Security event: {event_type}",
            **log_data
        )
    
    def log_performance_metrics(
        self,
        session_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """Log performance metrics.
        
        Args:
            session_id: Session identifier
            metrics: Performance metrics dictionary
        """
        session_logger = self.get_session_logger(session_id)
        
        session_logger.info(
            "Performance metrics",
            performance_metrics=metrics,
            timestamp=datetime.now().isoformat()
        )
    
    def export_session_logs(self, session_id: str, format: str = "json") -> str:
        """Export session logs to file.
        
        Args:
            session_id: Session identifier
            format: Export format ("json" or "text")
            
        Returns:
            Path to exported file
        """
        session_log_file = self.logs_path / f"session_{session_id}.log"
        
        if not session_log_file.exists():
            raise FileNotFoundError(f"No log file found for session {session_id}")
        
        export_file = self.logs_path / f"session_{session_id}_export.{format}"
        
        if format == "json":
            # Parse and export as structured JSON
            logs = []
            with open(session_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        else:
            # Copy as-is for text format
            import shutil
            shutil.copy2(session_log_file, export_file)
        
        return str(export_file)
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> None:
        """Clean up old log files.
        
        Args:
            days_to_keep: Number of days of logs to keep
        """
        import time
        
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        
        for log_file in self.logs_path.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    self.logger.info(f"Cleaned up old log file: {log_file}")
                except Exception as e:
                    self.logger.warning(f"Failed to clean up log file {log_file}: {e}")
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of session logs.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session log summary
        """
        session_log_file = self.logs_path / f"session_{session_id}.log"
        
        if not session_log_file.exists():
            return {"error": f"No log file found for session {session_id}"}
        
        summary = {
            "session_id": session_id,
            "total_log_entries": 0,
            "actions_executed": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "workflow_stages": [],
            "llm_requests": 0,
            "approval_requests": 0,
            "security_events": 0,
            "errors": []
        }
        
        with open(session_log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    summary["total_log_entries"] += 1
                    
                    # Analyze log entry
                    message = log_entry.get("event", "")
                    
                    if "Action started" in message:
                        summary["actions_executed"] += 1
                    elif "Action completed successfully" in message:
                        summary["successful_actions"] += 1
                    elif "Action failed" in message:
                        summary["failed_actions"] += 1
                        summary["errors"].append(log_entry.get("error_message", ""))
                    elif "Workflow stage" in message:
                        stage = log_entry.get("workflow_stage", "")
                        if stage not in summary["workflow_stages"]:
                            summary["workflow_stages"].append(stage)
                    elif "LLM request" in message:
                        summary["llm_requests"] += 1
                    elif "approval requested" in message.lower():
                        summary["approval_requests"] += 1
                    elif "security_event_type" in log_entry:
                        summary["security_events"] += 1
                        
                except json.JSONDecodeError:
                    continue
        
        return summary