# Copyright 2024 SEMOVI Multiagent System

"""Supabase connection utilities for SEMOVI agents."""

import os
import requests
import json
import base64
from google.adk.tools.tool_context import ToolContext


def get_authenticated_headers(tool_context):
    """
    Get authenticated headers for Supabase requests using JWT token from context.
    
    Args:
        tool_context: Tool context containing JWT token
        
    Returns:
        Dictionary with authentication headers or None if not available
    """
    try:
        # Get JWT token from tool context
        jwt_token = None
        if tool_context.state:
            jwt_token = tool_context.state.get("jwt_token")
        
        # Also check if it's directly in the context from input
        if not jwt_token and hasattr(tool_context, 'request_input'):
            jwt_token = getattr(tool_context.request_input, 'jwt_token', None)
            
        if not jwt_token:
            return None
        
        # Get Supabase configuration
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_anon_key:
            return None
        
        return {
            "Authorization": f"Bearer {jwt_token}",
            "apikey": supabase_anon_key,
            "Content-Type": "application/json"
        }
    except:
        return None


def get_user_id_from_jwt(tool_context):
    """
    Extract user_id (UUID) from JWT token stored in tool context.
    
    Args:
        tool_context: Tool context containing JWT token
        
    Returns:
        String UUID of the authenticated user, or None if extraction fails
    """
    try:
        # Get JWT token from tool context
        jwt_token = None
        if tool_context.state:
            jwt_token = tool_context.state.get("jwt_token")
        
        # Also check if it's directly in the context from input
        if not jwt_token and hasattr(tool_context, 'request_input'):
            jwt_token = getattr(tool_context.request_input, 'jwt_token', None)
            
        if not jwt_token:
            return None
        
        # JWT tokens have 3 parts separated by '.'
        parts = jwt_token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode the payload (second part)
        payload = parts[1]
        
        # Add padding if needed for base64 decoding
        missing_padding = len(payload) % 4
        if missing_padding:
            payload += '=' * (4 - missing_padding)
        
        # Decode base64 and parse JSON
        decoded_payload = base64.urlsafe_b64decode(payload)
        payload_data = json.loads(decoded_payload)
        
        # Extract user_id (sub field in JWT)
        user_id = payload_data.get('sub')
        return user_id
        
    except Exception as e:
        print(f"Error extracting user_id from JWT: {e}")
        return None


def get_supabase_config():
    """
    Get Supabase configuration from environment variables.
    
    Returns:
        Dictionary with Supabase URL and keys or None if not available
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_anon_key:
        return None
    
    return {
        "url": supabase_url,
        "anon_key": supabase_anon_key
    }


def ensure_user_profile_exists(tool_context):
    """
    Ensure that a user profile exists in the profiles table.
    Creates one if it doesn't exist using the JWT token information.
    
    Args:
        tool_context: Tool context containing JWT token
        
    Returns:
        Dictionary with success status and user_id or error information
    """
    try:
        user_id = get_user_id_from_jwt(tool_context)
        if not user_id:
            return {
                "status": "error",
                "message": "No valid JWT token found"
            }
        
        # Check if profile already exists
        profile_check = execute_supabase_query(
            tool_context,
            endpoint=f"profiles?select=id&id=eq.{user_id}",
            method="GET"
        )
        
        if profile_check["status"] == "success" and profile_check["data"]:
            # Profile exists
            return {
                "status": "success",
                "user_id": user_id,
                "profile_exists": True
            }
        
        # Extract user data from session state for profile creation
        user_data = tool_context.state.get("user_data", {})
        full_name = user_data.get("full_name", "")
        
        # Split name for first_name and last_name
        name_parts = full_name.split() if full_name else []
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        # Create profile data
        profile_data = {
            "id": user_id,
            "profile_type": "citizen",
            "first_name": first_name,
            "last_name": last_name,
            "phone": user_data.get("phone", ""),
            "is_active": True
        }
        
        # Create profile
        create_result = execute_supabase_query(
            tool_context,
            endpoint="profiles",
            method="POST", 
            data=profile_data
        )
        
        if create_result["status"] == "success":
            return {
                "status": "success",
                "user_id": user_id,
                "profile_exists": False,
                "profile_created": True
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to create user profile: {create_result.get('message', 'Unknown error')}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error ensuring user profile: {str(e)}"
        }


def execute_supabase_query(
    tool_context,
    endpoint,
    method = "GET",
    data: dict = None,
    params: dict = None
) :
    """
    Execute a Supabase query with proper authentication.
    
    Args:
        tool_context: Tool context for authentication
        endpoint: Supabase REST API endpoint
        method: HTTP method (GET, POST, PATCH, DELETE)
        data: Request payload for POST/PATCH requests
        params: Query parameters
        
    Returns:
        Dictionary with query results or error information
    """
    try:
        # Get configuration and headers
        config = get_supabase_config()
        if not config:
            return {
                "status": "error",
                "message": "Supabase configuration not found in environment variables"
            }
        
        headers = get_authenticated_headers(tool_context)
        if not headers:
            return {
                "status": "error", 
                "message": "Authentication required - no valid JWT token found"
            }
        
        # Build URL
        url = f"{config['url']}/rest/v1/{endpoint}"
        
        # Add prefer header for POST/PATCH operations
        if method in ["POST", "PATCH"]:
            headers["Prefer"] = "return=representation"
        
        # Execute request
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            return {
                "status": "success",
                "data": response.json(),
                "status_code": response.status_code
            }
        else:
            return {
                "status": "error",
                "message": f"Database query failed: {response.status_code} {response.text}",
                "status_code": response.status_code
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Database query timed out - please try again"
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error", 
            "message": f"Network error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }