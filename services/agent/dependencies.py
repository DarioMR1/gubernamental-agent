from functools import lru_cache
from agents.workflows.chat_agent import create_chat_workflow, create_government_tramites_agent

# Global workflow storage
_compiled_workflows = {}


@lru_cache()
def get_compiled_workflows():
    """Precompile LangGraph workflows for reuse"""
    global _compiled_workflows
    
    if not _compiled_workflows:
        # For backward compatibility, we still provide the enhanced agent as "chat"
        enhanced_agent = create_chat_workflow()
        _compiled_workflows = {
            "chat": enhanced_agent,
            "government_tramites": enhanced_agent  # Same agent, different reference
        }
    
    return _compiled_workflows


def get_chat_workflow():
    """Dependency for chat workflow (now uses government tramites agent)"""
    workflows = get_compiled_workflows()
    return workflows["chat"]


def get_government_tramites_workflow():
    """Dependency for government tramites workflow"""
    workflows = get_compiled_workflows()
    return workflows["government_tramites"]