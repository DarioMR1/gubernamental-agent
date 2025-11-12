from functools import lru_cache
from agents.workflows.chat_agent import create_chat_workflow

# Global workflow storage
_compiled_workflows = {}


@lru_cache()
def get_compiled_workflows():
    """Precompile LangGraph workflows for reuse"""
    global _compiled_workflows
    
    if not _compiled_workflows:
        _compiled_workflows = {
            "chat": create_chat_workflow().compile()
        }
    
    return _compiled_workflows


def get_chat_workflow():
    """Dependency for chat workflow"""
    workflows = get_compiled_workflows()
    return workflows["chat"]