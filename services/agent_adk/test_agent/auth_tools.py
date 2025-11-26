"""
Authentication verification tools for test agent

These tools help verify and manage authentication state from ADK session
"""

from typing import Dict, Any
from google.adk.tools.tool_context import ToolContext


def check_authentication_status(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Checks if the user is currently authenticated and returns authentication status.
    
    This tool verifies that the session has valid authentication credentials
    from the frontend user session.
    
    Args:
        tool_context: ADK tool context for accessing session state (injected automatically)
        
    Returns:
        A dictionary containing the authentication status
    """
    if not tool_context:
        return {
            "action": "check_authentication_status",
            "authenticated": False,
            "message": "No context available. Authentication cannot be verified."
        }
    
    # Check if we have state in the context
    if not hasattr(tool_context, 'state') or not tool_context.state:
        return {
            "action": "check_authentication_status",
            "authenticated": False,
            "message": "No session state available. Please ensure you are connected to the agent."
        }
    
    # Extract authentication information from state
    auth_token = tool_context.state.get("auth_token")
    user_id = tool_context.state.get("user_id")
    authenticated = tool_context.state.get("authenticated", False)
    
    if auth_token and user_id and authenticated:
        return {
            "action": "check_authentication_status",
            "authenticated": True,
            "user_info": {
                "user_id": user_id,
                "user_email": tool_context.state.get("user_email"),
                "user_name": tool_context.state.get("user_name"),
                "user_role": tool_context.state.get("user_role"),
                "business_name": tool_context.state.get("business_name")
            },
            "message": "User is authenticated and session is active."
        }
    else:
        return {
            "action": "check_authentication_status",
            "authenticated": False,
            "message": "User is not authenticated. Please log in through the frontend application."
        }


def get_user_business_info(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Retrieves the user's business information from the session state.
    
    This tool provides information about the business context of the authenticated user.
    
    Args:
        tool_context: ADK tool context for accessing session state (injected automatically)
        
    Returns:
        A dictionary containing business information
    """
    if not tool_context:
        return {
            "action": "get_user_business_info",
            "success": False,
            "error": "No context available."
        }
    
    if not hasattr(tool_context, 'state') or not tool_context.state:
        return {
            "action": "get_user_business_info",
            "success": False,
            "error": "No session state available."
        }
    
    authenticated = tool_context.state.get("authenticated", False)
    
    if not authenticated:
        return {
            "action": "get_user_business_info",
            "success": False,
            "error": "User is not authenticated."
        }
    
    # Extract business information
    business_info = {
        "business_name": tool_context.state.get("business_name"),
        "user_role": tool_context.state.get("user_role"),
        "user_name": tool_context.state.get("user_name"),
        "user_email": tool_context.state.get("user_email")
    }
    
    # Check if business information is available
    if business_info.get("business_name"):
        return {
            "action": "get_user_business_info",
            "success": True,
            "business_info": business_info,
            "message": f"Business information retrieved for {business_info['business_name']}"
        }
    else:
        return {
            "action": "get_user_business_info",
            "success": False,
            "error": "No business information available for this user.",
            "user_info": {
                "user_name": business_info.get("user_name"),
                "user_email": business_info.get("user_email"),
                "user_role": business_info.get("user_role")
            }
        }