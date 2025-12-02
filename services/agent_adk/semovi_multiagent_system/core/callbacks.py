# Copyright 2024 SEMOVI Multiagent System

"""System callbacks for initialization and state management."""

from datetime import datetime
from typing import Optional
import uuid

from google.adk.agents.callback_context import CallbackContext
from google.genai import types


async def initialize_semovi_session(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Initialize SEMOVI session state with required fields.
    
    This callback ensures all required state fields are properly initialized
    before any agent processing begins.
    """
    # Define required session fields for SEMOVI system
    required_fields = {
        "user_data": {
            "full_name": "",
            "curp": "",
            "address": "",
            "postal_code": "",
            "birth_date": "",
            "extraction_timestamp": ""
        },
        "service_determination": {
            "vehicle_type": "",  # auto | motorcycle
            "cylinder_capacity": None,  # for motorcycles
            "license_type": "",  # LICENSE_A | LICENSE_A1 | LICENSE_A2
            "procedure_type": "",  # EXPEDITION | RENEWAL | REPLACEMENT
            "total_cost": 0.0,
            "requirements": []
        },
        "office_search": {
            "search_postal_code": "",
            "found_offices": [],
            "selected_office": {}
        },
        "appointment": {
            "available_slots": [],
            "selected_slot": {},
            "confirmation": {}
        },
        "process_stage": "welcome",  # welcome -> authentication_required -> authenticated -> ine_extraction -> service_consultation -> office_search -> appointment_booking -> confirmed
        "session_metadata": {
            "session_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "interaction_count": 0,
            "agent_transitions": []
        },
        "information_queries": {
            "queries_made": [],
            "corpus_status": "ready",
            "last_corpus_update": "2024-12-01T00:00:00Z"
        },
        "authentication_status": {
            "is_authenticated": False,
            "jwt_token": None,
            "auth_user_id": None,
            "authenticated_at": None,
            "user_profile": {}
        },
        # Flatten key variables for template access
        "license_type": "",
        "procedure_type": "",
        "appointment_date": "",
        "appointment_time": "",
        "office_name": "",
        "total_cost": ""
    }
    
    # Initialize missing fields
    for field, default_value in required_fields.items():
        if field not in callback_context.state:
            callback_context.state[field] = default_value
    
    # Update session metadata
    callback_context.state["session_metadata"]["last_activity"] = datetime.now().isoformat()
    interactions = callback_context.state["session_metadata"].get("interaction_count", 0)
    callback_context.state["session_metadata"]["interaction_count"] = interactions + 1
    
    # Log system activity (optional)
    _log_session_activity(callback_context.state)
    
    return None  # Don't modify agent response


def _log_session_activity(state: dict) -> None:
    """Log session activity for monitoring and debugging."""
    session_id = state.get("session_metadata", {}).get("session_id", "unknown")
    interaction_count = state.get("session_metadata", {}).get("interaction_count", 0)
    process_stage = state.get("process_stage", "unknown")
    
    print(f"[SEMOVI_SYSTEM] Session: {session_id[:8]}... | "
          f"Interaction: #{interaction_count} | Stage: {process_stage}")


async def cleanup_session_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Cleanup callback executed after processing.
    
    Handles temporary data cleanup and optional persistence of critical data.
    """
    # Clean up temporary data if it exists
    if "temporary_data" in callback_context.state:
        current_time = datetime.now()
        temp_data = callback_context.state["temporary_data"]
        
        # Remove temporary data older than 1 hour
        for key, data in list(temp_data.items()):
            if isinstance(data, dict) and "created_at" in data:
                created_time = datetime.fromisoformat(data["created_at"])
                if (current_time - created_time).total_seconds() > 3600:  # 1 hour
                    del temp_data[key]
    
    # Update last activity timestamp
    if "session_metadata" in callback_context.state:
        callback_context.state["session_metadata"]["last_activity"] = datetime.now().isoformat()
    
    return None


def get_session_summary(callback_context: CallbackContext) -> dict:
    """
    Get a comprehensive summary of the current session state.
    
    Returns:
        Dict containing session summary information.
    """
    state = callback_context.state
    
    return {
        "session_id": state.get("session_metadata", {}).get("session_id", ""),
        "current_stage": state.get("process_stage", "unknown"),
        "user_identified": bool(state.get("user_data", {}).get("curp", "")),
        "service_determined": bool(state.get("service_determination", {}).get("license_type", "")),
        "office_selected": bool(state.get("office_search", {}).get("selected_office", {})),
        "appointment_confirmed": bool(state.get("appointment", {}).get("confirmation", {})),
        "interaction_count": state.get("session_metadata", {}).get("interaction_count", 0),
        "total_queries": len(state.get("information_queries", {}).get("queries_made", [])),
        "session_duration_minutes": _calculate_session_duration(state)
    }


def _calculate_session_duration(state: dict) -> float:
    """Calculate session duration in minutes."""
    try:
        created_at = state.get("session_metadata", {}).get("created_at", "")
        if not created_at:
            return 0.0
        
        created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        current_time = datetime.now()
        duration = current_time - created_time.replace(tzinfo=None)
        return round(duration.total_seconds() / 60, 2)
    except:
        return 0.0