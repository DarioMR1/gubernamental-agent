import os
import json
import jwt
import requests
from datetime import datetime
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from dotenv import load_dotenv
from typing import Dict, Optional, Any

# Load environment variables
load_dotenv()

def get_user_profile(tool_context: ToolContext, session_id: Optional[str] = None) -> dict:
    """
    Get user profile information using JWT token passed from frontend.
    The frontend sends the JWT token via session context.
    """
    try:
        # Get JWT token from tool context (passed by frontend via Agent Engine)
        if not tool_context:
            return {
                "status": "error",
                "message": "No tool context available"
            }

        # JWT token is passed via the Agent Engine input state
        jwt_token = None
        if tool_context.state:
            jwt_token = tool_context.state.get("jwt_token")
        
        # Also check if it's directly in the context from input
        if not jwt_token and hasattr(tool_context, 'request_input'):
            jwt_token = getattr(tool_context.request_input, 'jwt_token', None)
            
        if not jwt_token:
            return {
                "status": "error", 
                "message": "No JWT token found - user must be authenticated to access profile data"
            }
        
        # Get Supabase URL from environment
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_anon_key:
            return {
                "status": "error",
                "message": "Supabase configuration not found"
            }
        
        # Make request to Supabase using JWT token for RLS
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "apikey": supabase_anon_key,
            "Content-Type": "application/json"
        }
        
        # Get user profile from profiles table
        response = requests.get(
            f"{supabase_url}/rest/v1/profiles?select=*",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            profiles = response.json()
            if profiles:
                profile = profiles[0]  # Should only return user's own profile due to RLS
                
                # Store profile in context for future use
                if tool_context.state:
                    tool_context.state["user_profile"] = profile
                
                return {
                    "status": "success",
                    "profile": {
                        "id": profile.get("id"),
                        "first_name": profile.get("first_name"),
                        "last_name": profile.get("last_name"),
                        "phone": profile.get("phone"),
                        "profile_type": profile.get("profile_type"),
                        "is_active": profile.get("is_active"),
                        "created_at": profile.get("created_at")
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": "No profile found for user"
                }
        else:
            return {
                "status": "error",
                "message": f"Failed to fetch profile: {response.status_code} {response.text}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting user profile: {str(e)}"
        }


def get_user_appointments(tool_context: ToolContext) -> dict:
    """
    Get user's appointments using JWT token for RLS access.
    """
    try:
        # Get JWT token from session context
        if not tool_context.state:
            return {
                "status": "error",
                "message": "No session context available"
            }
        
        jwt_token = tool_context.state.get("jwt_token")
        if not jwt_token:
            return {
                "status": "error",
                "message": "No JWT token found in session context"
            }
        
        # Get Supabase configuration
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_anon_key:
            return {
                "status": "error",
                "message": "Supabase configuration not found"
            }
        
        # Headers for authenticated request
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "apikey": supabase_anon_key,
            "Content-Type": "application/json"
        }
        
        # Get appointments with related data (offices, services, etc.)
        query = """
        appointments:*,
        offices:office_id(*),
        service_categories:service_category_id(*),
        service_types:service_type_id(*),
        appointment_slots:appointment_slot_id(*)
        """
        
        response = requests.get(
            f"{supabase_url}/rest/v1/appointments?select={query}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            appointments = response.json()
            
            # Format appointments data for better readability
            formatted_appointments = []
            for apt in appointments:
                formatted_appointments.append({
                    "id": apt.get("id"),
                    "status": apt.get("status"),
                    "confirmation_code": apt.get("confirmation_code"),
                    "notes": apt.get("notes"),
                    "user_info": apt.get("user_info", {}),
                    "office": apt.get("offices", {}).get("name"),
                    "office_address": apt.get("offices", {}).get("address"),
                    "service_category": apt.get("service_categories", {}).get("name"),
                    "service_type": apt.get("service_types", {}).get("name"),
                    "appointment_date": apt.get("appointment_slots", {}).get("slot_date"),
                    "appointment_time": apt.get("appointment_slots", {}).get("start_time"),
                    "created_at": apt.get("created_at")
                })
            
            return {
                "status": "success",
                "appointments": formatted_appointments,
                "total_count": len(formatted_appointments)
            }
            
        else:
            return {
                "status": "error",
                "message": f"Failed to fetch appointments: {response.status_code} {response.text}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting user appointments: {str(e)}"
        }


def update_user_profile(tool_context: ToolContext, first_name: Optional[str] = None, last_name: Optional[str] = None, phone: Optional[str] = None) -> dict:
    """
    Update user profile information using JWT token for RLS access.
    """
    try:
        # Get JWT token from session context
        if not tool_context.state:
            return {
                "status": "error",
                "message": "No session context available"
            }
        
        jwt_token = tool_context.state.get("jwt_token")
        if not jwt_token:
            return {
                "status": "error",
                "message": "No JWT token found in session context"
            }
        
        # Get Supabase configuration
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_anon_key:
            return {
                "status": "error",
                "message": "Supabase configuration not found"
            }
        
        # Prepare update data (only include provided fields)
        update_data = {}
        if first_name is not None:
            update_data["first_name"] = first_name
        if last_name is not None:
            update_data["last_name"] = last_name
        if phone is not None:
            update_data["phone"] = phone
        
        if not update_data:
            return {
                "status": "error",
                "message": "No fields provided to update"
            }
        
        update_data["updated_at"] = datetime.now().isoformat()
        
        # Headers for authenticated request
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "apikey": supabase_anon_key,
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # Update profile using RLS (will only update user's own profile)
        response = requests.patch(
            f"{supabase_url}/rest/v1/profiles",
            headers=headers,
            json=update_data,
            timeout=10
        )
        
        if response.status_code == 200:
            updated_profile = response.json()
            if updated_profile:
                # Update cached profile in context
                if tool_context.state:
                    tool_context.state["user_profile"] = updated_profile[0]
                
                return {
                    "status": "success",
                    "message": "Profile updated successfully",
                    "updated_profile": updated_profile[0]
                }
            else:
                return {
                    "status": "error",
                    "message": "Profile update failed - no data returned"
                }
        else:
            return {
                "status": "error",
                "message": f"Failed to update profile: {response.status_code} {response.text}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error updating user profile: {str(e)}"
        }


# Create the root agent
root_agent = Agent(
    name="profile_agent",
    model="gemini-2.0-flash",
    description="""
    Agent for accessing and managing user profile data through authenticated JWT tokens.
    This agent demonstrates how to securely access Supabase data using Row Level Security (RLS).
    """,
    instruction=f"""
    You are a Profile Management Assistant that helps users access and manage their profile information.
    
    CURRENT DATE: {datetime.now().strftime("%d %B %Y")}
    
    ### Your Capabilities:
    1. **get_user_profile**: Retrieve the user's profile information including name, phone, account type, etc.
    2. **get_user_appointments**: Get all appointments scheduled by the user with detailed information
    3. **update_user_profile**: Update user's profile information (name, phone number)
    
    ### Security Model:
    - You access data using JWT tokens provided by the frontend application
    - All database access uses Row Level Security (RLS) policies
    - Users can only see and modify their own data
    - You do not store or handle Supabase credentials directly
    
    ### Instructions:
    1. **Always start** by getting the user's profile to understand who they are
    2. **Be helpful** in explaining what information is available
    3. **Respect privacy** - only access data the user has permission to see
    4. **Handle errors gracefully** and explain any access issues
    5. **Be conversational** and friendly while maintaining security
    
    ### Example Interactions:
    - "Let me check your profile information"
    - "Here are your upcoming appointments"
    - "I can update your phone number if needed"
    
    Remember: You are demonstrating secure, authenticated access to user data through RLS policies.
    """,
    tools=[
        get_user_profile,
        get_user_appointments, 
        update_user_profile
    ],
    sub_agents=[]
)