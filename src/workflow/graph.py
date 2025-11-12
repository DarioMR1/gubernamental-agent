"""LangGraph workflow definition for the governmental agent."""

import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..types import AgentState, SessionStatus, WorkflowStage
from ..config import AgentConfig
from .nodes import WorkflowNodes
from .conditions import WorkflowConditions


logger = logging.getLogger(__name__)


class AgentWorkflow:
    """LangGraph workflow for governmental agent execution."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the workflow.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.nodes = WorkflowNodes(config)
        self.conditions = WorkflowConditions()
        
        # Create memory saver for checkpointing
        self.memory = MemorySaver()
        
        # Build the workflow graph
        self.graph = self._build_graph()
        self.compiled_graph = None
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow.
        
        Returns:
            Configured StateGraph
        """
        logger.info("Building LangGraph workflow")
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_instruction", self.nodes.instruction_parsing_node)
        workflow.add_node("create_plan", self.nodes.planning_node)
        workflow.add_node("validate_plan", self.nodes.plan_validation_node)
        workflow.add_node("request_approval", self.nodes.human_approval_node)
        workflow.add_node("execute_action", self.nodes.execution_node)
        workflow.add_node("validate_result", self.nodes.result_validation_node)
        workflow.add_node("handle_error", self.nodes.error_handling_node)
        workflow.add_node("complete", self.nodes.completion_node)
        
        # Define the flow
        workflow.set_entry_point("parse_instruction")
        
        # From instruction parsing to planning
        workflow.add_edge("parse_instruction", "create_plan")
        
        # From planning to validation
        workflow.add_edge("create_plan", "validate_plan")
        
        # Conditional edge from plan validation
        workflow.add_conditional_edges(
            "validate_plan",
            self.conditions.should_request_approval,
            {
                "approve": "request_approval",
                "execute": "execute_action",
                "error": "handle_error"
            }
        )
        
        # From approval to execution
        workflow.add_conditional_edges(
            "request_approval", 
            self.conditions.approval_granted,
            {
                "approved": "execute_action",
                "denied": "complete",
                "timeout": "complete"
            }
        )
        
        # Execution loop
        workflow.add_conditional_edges(
            "execute_action",
            self.conditions.should_continue_execution,
            {
                "continue": "execute_action",
                "validate": "validate_result", 
                "error": "handle_error",
                "complete": "complete"
            }
        )
        
        # Result validation
        workflow.add_conditional_edges(
            "validate_result",
            self.conditions.should_retry_or_complete,
            {
                "retry": "execute_action",
                "complete": "complete",
                "error": "handle_error"
            }
        )
        
        # Error handling
        workflow.add_conditional_edges(
            "handle_error",
            self.conditions.should_retry_after_error,
            {
                "retry": "execute_action",
                "abort": "complete",
                "human_intervention": "request_approval"
            }
        )
        
        # Completion always goes to end
        workflow.add_edge("complete", END)
        
        logger.info("LangGraph workflow built successfully")
        return workflow
    
    def compile_workflow(self) -> None:
        """Compile the workflow for execution."""
        if self.compiled_graph is None:
            logger.info("Compiling LangGraph workflow")
            self.compiled_graph = self.graph.compile(
                checkpointer=self.memory,
                interrupt_before=["request_approval"],  # Always interrupt for human approval
                debug=True
            )
            logger.info("Workflow compiled successfully")
    
    async def execute_workflow(
        self, 
        initial_state: AgentState,
        thread_id: str = "default"
    ) -> AgentState:
        """Execute the workflow.
        
        Args:
            initial_state: Initial agent state
            thread_id: Thread ID for checkpointing
            
        Returns:
            Final agent state
        """
        if self.compiled_graph is None:
            self.compile_workflow()
        
        logger.info(f"Executing workflow for session {initial_state.session_id}")
        
        try:
            # Configure the execution
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "session_id": initial_state.session_id
                }
            }
            
            # Execute the workflow
            final_state = None
            async for state in self.compiled_graph.astream(
                initial_state,
                config=config
            ):
                # Log progress
                current_node = list(state.keys())[0] if state else "unknown"
                current_state = list(state.values())[0] if state else initial_state
                
                logger.info(
                    f"Workflow step: {current_node} - "
                    f"Stage: {current_state.current_stage.value} - "
                    f"Status: {current_state.status.value}"
                )
                
                final_state = current_state
            
            return final_state or initial_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            
            # Set error state
            initial_state.status = SessionStatus.FAILED
            initial_state.current_stage = WorkflowStage.ERROR_HANDLING
            
            return initial_state
    
    async def resume_workflow(
        self,
        thread_id: str,
        approved: bool = True,
        feedback: str = ""
    ) -> AgentState:
        """Resume workflow after human approval.
        
        Args:
            thread_id: Thread ID to resume
            approved: Whether the action was approved
            feedback: Optional feedback from human
            
        Returns:
            Updated agent state
        """
        if self.compiled_graph is None:
            self.compile_workflow()
        
        logger.info(f"Resuming workflow thread {thread_id} with approval: {approved}")
        
        try:
            config = {
                "configurable": {
                    "thread_id": thread_id
                }
            }
            
            # Update state with approval response
            current_state = await self.get_current_state(thread_id)
            if current_state:
                current_state.session_variables["approval_granted"] = approved
                current_state.session_variables["approval_feedback"] = feedback
            
            # Resume execution
            final_state = None
            async for state in self.compiled_graph.astream(
                None,  # Continue from checkpoint
                config=config
            ):
                current_node = list(state.keys())[0] if state else "unknown"
                current_state = list(state.values())[0] if state else current_state
                
                logger.info(f"Resumed workflow step: {current_node}")
                final_state = current_state
            
            return final_state or current_state
            
        except Exception as e:
            logger.error(f"Failed to resume workflow: {e}")
            raise
    
    async def get_current_state(self, thread_id: str) -> AgentState:
        """Get current state of a workflow thread.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Current agent state
        """
        if self.compiled_graph is None:
            return None
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            state_snapshot = await self.compiled_graph.aget_state(config)
            
            if state_snapshot and state_snapshot.values:
                return state_snapshot.values
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get current state: {e}")
            return None
    
    async def get_workflow_history(self, thread_id: str) -> list[Dict[str, Any]]:
        """Get workflow execution history.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            List of workflow states
        """
        if self.compiled_graph is None:
            return []
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            history = []
            
            async for state in self.compiled_graph.aget_state_history(config):
                history.append({
                    "step": len(history),
                    "timestamp": state.created_at.isoformat() if state.created_at else None,
                    "node": state.next[0] if state.next else "END",
                    "status": state.values.status.value if state.values else "unknown",
                    "stage": state.values.current_stage.value if state.values else "unknown"
                })
            
            return list(reversed(history))  # Return in chronological order
            
        except Exception as e:
            logger.error(f"Failed to get workflow history: {e}")
            return []
    
    async def abort_workflow(self, thread_id: str) -> None:
        """Abort a running workflow.
        
        Args:
            thread_id: Thread ID to abort
        """
        logger.info(f"Aborting workflow thread {thread_id}")
        
        try:
            # Update state to aborted
            current_state = await self.get_current_state(thread_id)
            if current_state:
                current_state.status = SessionStatus.ABORTED
                current_state.session_variables["aborted"] = True
        
        except Exception as e:
            logger.error(f"Failed to abort workflow: {e}")
    
    def get_workflow_visualization(self) -> str:
        """Get a text representation of the workflow.
        
        Returns:
            Workflow visualization as string
        """
        return """
Governmental Agent Workflow:

START 
  ↓
parse_instruction (Parse user instruction with LLM)
  ↓  
create_plan (Generate execution plan)
  ↓
validate_plan (Validate plan safety and correctness)
  ↓
[Conditional: Approval Required?]
  ├─ approve → request_approval (Wait for human approval)
  │             ↓
  │           [Conditional: Approved?]
  │             ├─ approved → execute_action
  │             ├─ denied → complete
  │             └─ timeout → complete
  │
  └─ execute → execute_action (Execute next action)
                ↓
              [Conditional: Continue?]
                ├─ continue → execute_action (Loop)
                ├─ validate → validate_result 
                ├─ error → handle_error
                └─ complete → complete
                              ↓
                            END

Error Handling Flow:
handle_error
  ↓
[Conditional: Retry?]
  ├─ retry → execute_action
  ├─ abort → complete
  └─ human_intervention → request_approval
"""