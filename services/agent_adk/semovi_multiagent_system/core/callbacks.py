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
            "phone": "",
            "email": "",
            "extraction_timestamp": "",
            "extraction_method": ""
        },
        "service_determination": {
            "status": "",
            "license_type": "",  # LIC_A | LIC_A1 | LIC_A2
            "procedure_type": "",  # EXPEDITION | RENEWAL | REPLACEMENT
            "vehicle_info": {
                "type": "",  # auto | motorcycle
                "cylinder_capacity": None
            },
            "costs": {
                "base_cost": 0.0,
                "additional_cost": 0.0, 
                "total_cost": 0.0,
                "currency": "MXN"
            },
            "requirements": {
                "total_requirements": 0,
                "required_documents": [],
                "base_requirements": [],
                "license_specific": [],
                "procedure_specific": []
            },
            "age_validation": {},
            "processing_time_days": 1,
            "validity_years": 3
        },
        "office_search": {
            "search_postal_code": "",
            "found_offices": [],
            "total_found": 0,
            "search_timestamp": ""
        },
        "appointment": {
            "office_id": None,
            "office_name": "",
            "available_slots": [],
            "slots_by_date": {},
            "search_range_days": 14,
            "last_availability_check": "",
            "selected_slot": {
                "slot_id": None,
                "date": "",
                "time": ""
            },
            "confirmation": {
                "appointment_id": None,
                "confirmation_code": "",
                "status": "",
                "office": {},
                "date": "",
                "time": "",
                "license_type": "",
                "procedure_type": "",
                "total_cost": 0.0,
                "created_at": ""
            }
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
        "validation_results": {},
        "missing_info_request": {},
        "cost_calculation": {},
        "age_validation": {},
        "email_confirmation": {},
        "pdf_confirmation": {},
        "last_generated_code": {},
        "last_error": {},
        "last_auth_error": {},
        "last_logout": {},
        "authentication_status": {
            "is_authenticated": False,
            "jwt_token": None,
            "auth_user_id": None,
            "authenticated_at": None,
            "user_profile": {}
        },
        # Additional state variables used by tools
        "jwt_token": None,
        "auth_user_id": None, 
        "authenticated_at": None,
        "user_profile": {},
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
    
    # 🔥 AUTO-AUTHENTICATE WITH JWT TOKEN FROM FRONTEND
    # Check if JWT token was sent from frontend in state_delta
    jwt_token = callback_context.state.get("jwt_token")
    
    if jwt_token and not callback_context.state.get("authentication_status", {}).get("is_authenticated"):
        print(f"[CALLBACK] 🔐 JWT token detected, attempting auto-authentication...")
        try:
            # Import here to avoid circular imports
            from ..tools.authentication_tools import authenticate_with_jwt_token
            
            # Create a mock tool context to use authentication functions
            class MockToolContext:
                def __init__(self, state):
                    self.state = state
            
            mock_context = MockToolContext(callback_context.state)
            auth_result = authenticate_with_jwt_token(jwt_token, mock_context)
            
            if auth_result["status"] == "success":
                print(f"[CALLBACK] ✅ Auto-authentication successful: {auth_result.get('message', '')}")
                # State has already been updated by authenticate_with_jwt_token
            else:
                print(f"[CALLBACK] ❌ Auto-authentication failed: {auth_result.get('message', '')}")
                # Clear invalid token
                if "jwt_token" in callback_context.state:
                    del callback_context.state["jwt_token"]
                    
        except Exception as e:
            print(f"[CALLBACK] ❌ Error during auto-authentication: {str(e)}")
            # Clear problematic token
            if "jwt_token" in callback_context.state:
                del callback_context.state["jwt_token"]
    
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
        "offices_found": len(state.get("office_search", {}).get("found_offices", [])),
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