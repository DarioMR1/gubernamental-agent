"""
Authentication tools for test agent

These tools allow the agent to authenticate users and manage their profile information
by connecting to the Rust API.
"""

import os
import requests
from typing import Dict, Optional, List
from google.adk.tools.tool_context import ToolContext
from .config import JUNTOSS_API_KEY

# Smart API URL detection
def get_api_base_url():
    """
    Intelligently detects whether to use local or production API.
    Checks if local server is running, falls back to production if not.
    """
    import socket
    
    # URLs
    LOCAL_URL = "http://localhost:8080"
    PRODUCTION_URL = "https://api.juntoss.com"
    
    # Allow override via environment variable
    if os.getenv("JUNTOSS_API_URL"):
        return os.getenv("JUNTOSS_API_URL")
    
    # Check if running in production environment (Cloud Run)
    if os.getenv("K_SERVICE") or os.getenv("GOOGLE_CLOUD_PROJECT"):
        return PRODUCTION_URL
    
    # Try to connect to local server
    try:
        # Extract host and port from local URL
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)  # 500ms timeout for quick check
        result = sock.connect_ex(('localhost', 8080))
        sock.close()
        
        if result == 0:
            # Port is open, local server is running
            print(f"[Auto-detected] Using local API: {LOCAL_URL}")
            return LOCAL_URL
        else:
            # Port is closed, use production
            print(f"[Auto-detected] Using production API: {PRODUCTION_URL}")
            return PRODUCTION_URL
    except Exception:
        # If check fails, default to production
        return PRODUCTION_URL

# Get API configuration
API_BASE_URL = get_api_base_url()
API_VERSION = "api/v1"

# Session management
class AuthSession:
    """Manages dual authentication session (Access Token + API Key)."""
    _instance = None
    _api_key: Optional[str] = None
    _access_token: Optional[str] = None
    _auth_info: Optional[dict] = None
    _auth_method: Optional[str] = None  # 'access_token' or 'api_key'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def set_api_key(self, api_key: str) -> dict:
        """Set the API key for the session and validate it."""
        # Validate API key format
        if not api_key.startswith("jts_") or len(api_key) < 48:
            return {
                "status": "error",
                "is_authenticated": False,
                "message": "Invalid API key format. API keys should start with 'jts_' and be at least 48 characters."
            }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # First validate the API key
            validate_response = requests.get(
                f"{API_BASE_URL}/{API_VERSION}/auth/validate",
                headers=headers,
                timeout=10
            )
            
            if validate_response.status_code != 200:
                return {
                    "status": "error",
                    "is_authenticated": False,
                    "message": f"Failed to validate API key: HTTP {validate_response.status_code}"
                }
            
            validate_data = validate_response.json()
            if not validate_data.get("valid", False):
                return {
                    "status": "error",
                    "is_authenticated": False,
                    "message": "Invalid API key"
                }
            
            # Now get full auth info including accessible tenants
            info_response = requests.get(
                f"{API_BASE_URL}/{API_VERSION}/auth/info",
                headers=headers,
                timeout=10
            )
            
            if info_response.status_code == 200:
                data = info_response.json()
                self._api_key = api_key
                self._auth_method = 'api_key'
                self._auth_info = data
                return {
                    "status": "success",
                    "is_authenticated": True,
                    "auth_method": "api_key",
                    "scope": data.get("scope"),
                    "business_id": data.get("business_id"),
                    "partner_id": data.get("partner_id"),
                    "permissions": data.get("permissions", {}),
                    "description": data.get("description", ""),
                    "accessible_tenants": data.get("accessible_tenants", []),
                    "message": "API key validated and session established successfully"
                }
            else:
                return {
                    "status": "error",
                    "is_authenticated": False,
                    "message": f"Failed to get auth info: HTTP {info_response.status_code}"
                }
        except Exception as e:
            return {
                "status": "error",
                "is_authenticated": False,
                "message": f"Failed to authenticate with API key: {str(e)}"
            }
    
    def set_access_token(self, access_token: str) -> dict:
        """Set the access token for the session and validate it."""
        # Check if it's a service account token
        if access_token.startswith("svc_"):
            return self.set_service_account(access_token)
        
        # For JWT tokens, we don't validate with /auth/validate (that's for API keys)
        # Instead, we'll test it against a protected endpoint
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Try to get auth info using the JWT token
            # The API will validate the JWT internally
            info_response = requests.get(
                f"{API_BASE_URL}/{API_VERSION}/auth/info",
                headers=headers,
                timeout=10
            )
            
            if info_response.status_code == 200:
                data = info_response.json()
                self._access_token = access_token
                self._auth_method = 'access_token'
                self._auth_info = data
                
                # JWT tokens from Supabase won't have all the same fields as API keys
                # So we handle the response more flexibly
                return {
                    "status": "success",
                    "is_authenticated": True,
                    "auth_method": "access_token",
                    "scope": data.get("scope", "user"),
                    "business_id": data.get("business_id"),
                    "partner_id": data.get("partner_id"),
                    "permissions": data.get("permissions", {}),
                    "description": data.get("description", "JWT authenticated user"),
                    "accessible_tenants": data.get("accessible_tenants", []),
                    "message": "JWT token validated and session established successfully"
                }
            elif info_response.status_code == 401:
                # Token is invalid or expired
                return {
                    "status": "error",
                    "is_authenticated": False,
                    "message": "Invalid or expired JWT token. Please log in again."
                }
            else:
                return {
                    "status": "error",
                    "is_authenticated": False,
                    "message": f"Failed to validate JWT token: HTTP {info_response.status_code}"
                }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "is_authenticated": False,
                "message": "Cannot connect to Juntoss API. Please check if the API is running at api.juntoss.com."
            }
        except Exception as e:
            return {
                "status": "error",
                "is_authenticated": False,
                "message": f"Failed to authenticate with JWT token: {str(e)}"
            }
    
    def set_service_account(self, service_token: str) -> dict:
        """Set the service account token for the session and exchange it for a unified token."""
        # Validate service account token format
        if not service_token.startswith("svc_") or len(service_token) < 20:
            return {
                "status": "error",
                "is_authenticated": False,
                "message": "Invalid service account token format. Service tokens should start with 'svc_'."
            }
        
        try:
            # Exchange the service account token for a unified token
            exchange_response = requests.post(
                f"{API_BASE_URL}/{API_VERSION}/auth/exchange",
                json={"token": service_token, "expires_in": 3600},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if exchange_response.status_code == 200:
                exchange_data = exchange_response.json()
                unified_token = exchange_data.get("access_token")
                
                # Store the unified token and use the exchange data directly
                # We don't need to validate with /auth/info since the exchange already validated
                self._access_token = unified_token  # Store the unified token
                self._auth_method = 'service_account'
                
                # Build auth info from exchange response
                self._auth_info = {
                    "business_id": exchange_data.get("business_id"),
                    "tenant_id": exchange_data.get("tenant_id"),
                    "permissions": exchange_data.get("permissions", {}),
                    "token_type": exchange_data.get("original_type"),
                    "scope": "business" if exchange_data.get("business_id") else "global",
                    "accessible_tenants": [exchange_data.get("tenant_id")] if exchange_data.get("tenant_id") else []
                }
                
                return {
                    "status": "success",
                    "is_authenticated": True,
                    "auth_method": "service_account",
                    "scope": self._auth_info["scope"],
                    "business_id": exchange_data.get("business_id"),
                    "tenant_id": exchange_data.get("tenant_id"),
                    "permissions": exchange_data.get("permissions", {}),
                    "description": "Service account authenticated",
                    "accessible_tenants": self._auth_info["accessible_tenants"],
                    "message": "Service account token exchanged and session established successfully"
                }
            elif exchange_response.status_code == 401:
                return {
                    "status": "error",
                    "is_authenticated": False,
                    "message": "Invalid service account token"
                }
            else:
                return {
                    "status": "error",
                    "is_authenticated": False,
                    "message": f"Failed to exchange service account token: HTTP {exchange_response.status_code}"
                }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "is_authenticated": False,
                "message": "Cannot connect to Juntoss API for token exchange."
            }
        except Exception as e:
            return {
                "status": "error",
                "is_authenticated": False,
                "message": f"Failed to exchange service account token: {str(e)}"
            }
    
    def is_authenticated(self) -> bool:
        """Check if session is authenticated."""
        return self._access_token is not None or self._api_key is not None
    
    def clear(self):
        """Clear the session."""
        self._api_key = None
        self._access_token = None
        self._auth_info = None
        self._auth_method = None
    
    def get_headers(self) -> dict:
        """Get headers with authentication token (prioritizing access token)."""
        if self._access_token:
            return {
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json"
            }
        elif self._api_key:
            return {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"
            }
        else:
            raise ValueError("No authentication token set in session. Please authenticate first.")
    
    def get_auth_info(self) -> Optional[dict]:
        """Get the cached authentication info."""
        return self._auth_info

# Global session instance
session = AuthSession()

# Load API key from environment variable
DEFAULT_API_KEY = JUNTOSS_API_KEY

# Default tenant cache
_default_tenant_id = None

# Auto-initialization function
def _auto_initialize():
    """Automatically initialize authentication with API key on module import."""
    try:
        # Only auto-authenticate with API key if available and not already authenticated
        if DEFAULT_API_KEY and not session.is_authenticated():
            auth_result = session.set_api_key(DEFAULT_API_KEY)
            if auth_result.get("is_authenticated", False):
                # Silent success - API key is ready as fallback
                return True
            else:
                # Silent failure - will try JWT from frontend
                return False
        return False
    except Exception:
        # Silent failure - will try JWT from frontend
        return False

# Auto-initialize when module is imported (silently)
_auto_initialize()

def get_default_tenant_id() -> Optional[str]:
    """Get the default tenant ID for the authenticated session."""
    global _default_tenant_id
    
    if _default_tenant_id is not None:
        return _default_tenant_id
    
    try:
        if not session.is_authenticated():
            return None
        
        # Get auth info from session
        auth_info = session.get_auth_info()
        if auth_info:
            # First check if tenant_id is directly available (service accounts)
            if auth_info.get("tenant_id"):
                _default_tenant_id = str(auth_info["tenant_id"])
                return _default_tenant_id
            
            # Check for accessible_tenants array
            accessible_tenants = auth_info.get("accessible_tenants", [])
            if accessible_tenants:
                # Handle both string array and object array formats
                if isinstance(accessible_tenants[0], str):
                    # Simple string array format (service accounts)
                    _default_tenant_id = accessible_tenants[0]
                    return _default_tenant_id
                elif isinstance(accessible_tenants[0], dict):
                    # Object array format (regular users)
                    for tenant in accessible_tenants:
                        if tenant.get("is_default", False) or len(accessible_tenants) == 1:
                            _default_tenant_id = tenant.get("tenant_id")
                            return _default_tenant_id
                    
                    # If no default found, use the first available tenant
                    if accessible_tenants[0].get("tenant_id"):
                        _default_tenant_id = accessible_tenants[0].get("tenant_id")
                        return _default_tenant_id
            
            # Fallback: if no accessible_tenants, try to use business_id directly as tenant_id
            elif auth_info.get("business_id"):
                _default_tenant_id = str(auth_info["business_id"])
                return _default_tenant_id
        
        return None
    except Exception as e:
        print(f"[DEBUG] Error getting default tenant ID: {e}")
        return None


def execute_dsl_batch(tenant_id: Optional[str] = None, commands: Optional[List[str]] = None, options: Optional[dict] = None, tool_context: ToolContext = None) -> dict:
    """Execute DSL commands in batch for maximum performance and scalability.
    
    This tool executes multiple DSL commands in a single batch operation, which is
    much faster and more efficient than executing individual commands. Perfect for
    creating complex semantic structures with types, nodes, and relationships.
    
    Args:
        tenant_id: The tenant/knowledge graph ID where commands will be executed. 
                  If not provided, uses the default tenant automatically.
        commands: List of DSL commands to execute (CREATE TYPE, CREATE NODE, CREATE RELATIONSHIP).
                  This parameter is required and must be provided.
        options: Optional execution options (validate_before_execution, dry_run, etc.)
        tool_context: ADK tool context containing session state (injected automatically)
    
    Returns:
        A dictionary with status, execution results, and statistics
    """
    global _default_tenant_id
    
    try:
        # Check if we have tool_context with auth_token
        if tool_context and hasattr(tool_context, 'state'):
            auth_token = tool_context.state.get('auth_token')
            if auth_token:
                # Always use the token from session state for this request
                # Check if it's a service account token and handle accordingly
                if auth_token.startswith("svc_"):
                    auth_result = session.set_service_account(auth_token)
                else:
                    auth_result = session.set_access_token(auth_token)
                if auth_result.get("is_authenticated", False):
                    # Clear cached tenant to get user-specific tenant
                    _default_tenant_id = None
                else:
                    # JWT failed, try API key as fallback
                    if DEFAULT_API_KEY and not session.is_authenticated():
                        api_auth_result = session.set_api_key(DEFAULT_API_KEY)
                        if api_auth_result.get("is_authenticated", False):
                            # Clear cached tenant to get API key tenant
                            _default_tenant_id = None
                        else:
                            return {
                                "status": "error",
                                "message": f"Failed to authenticate with both JWT and API key: {auth_result.get('message', 'Unknown error')}"
                            }
                    else:
                        return {
                            "status": "error",
                            "message": f"Failed to authenticate with JWT token: {auth_result.get('message', 'Unknown error')}"
                        }
            else:
                # No auth token in session state, try API key
                if not session.is_authenticated() and DEFAULT_API_KEY:
                    api_auth_result = session.set_api_key(DEFAULT_API_KEY)
                    if api_auth_result.get("is_authenticated", False):
                        # Clear cached tenant to get API key tenant
                        _default_tenant_id = None
                    else:
                        return {
                            "status": "error",
                            "message": "No authentication token found in session and API key authentication failed."
                        }
                elif not session.is_authenticated():
                    return {
                        "status": "error",
                        "message": "No authentication token found in session. Please ensure you are logged in."
                    }
        
        # If no tool_context, check if we have existing authentication or try API key
        if not tool_context and not session.is_authenticated():
            if DEFAULT_API_KEY:
                api_auth_result = session.set_api_key(DEFAULT_API_KEY)
                if not api_auth_result.get("is_authenticated", False):
                    return {
                        "status": "error",
                        "message": "Not authenticated. API key authentication failed."
                    }
                # Clear cached tenant to get API key tenant
                _default_tenant_id = None
            else:
                return {
                    "status": "error",
                    "message": "Not authenticated. Please provide authentication through session state or API key."
                }
        
        # Use default tenant if not provided
        if tenant_id is None:
            tenant_id = get_default_tenant_id()
            if tenant_id is None:
                return {
                    "status": "error",
                    "message": "No tenant ID provided and no default tenant available. Please specify a tenant_id or check authentication."
                }
        
        # Validate commands parameter
        if commands is None:
            return {
                "status": "error",
                "message": "Commands parameter is required. Please provide a list of DSL commands."
            }
        
        headers = session.get_headers()
        
        # Default options if not provided
        if options is None:
            options = {
                "validate_before_execution": True,
                "dry_run": False,
                "use_optimized_executor": True
            }
        
        payload = {
            "dsl_commands": commands,
            "options": options
        }
        
        response = requests.post(
            f"{API_BASE_URL}/{API_VERSION}/batch/{tenant_id}/execute",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract key metrics from the response
            stats = data.get("stats", {})
            batch_result = data.get("batch_result", {})
            
            return {
                "status": "success",
                "execution_id": data.get("execution_id"),
                "success": data.get("success", False),
                "tenant_id": tenant_id,
                "stats": {
                    "transactions_executed": stats.get("transactions_executed", 0),
                    "operations_executed": stats.get("operations_executed", 0),
                    "operations_failed": stats.get("operations_failed", 0),
                    "execution_time_ms": stats.get("execution_time_ms", 0),
                    "ops_per_second": stats.get("ops_per_second", 0),
                    "operation_breakdown": stats.get("operation_breakdown", {})
                },
                "batch_result": {
                    "successful_operations": len(batch_result.get("successful_operations", [])),
                    "failed_operations": len(batch_result.get("failed_operations", [])),
                    "operation_details": batch_result.get("successful_operations", [])
                },
                "error": data.get("error"),
                "warnings": data.get("warnings", []),
                "message": f"Batch execution completed: {stats.get('operations_executed', 0)} operations in {stats.get('execution_time_ms', 0)}ms"
            }
        elif response.status_code == 401:
            return {
                "status": "error",
                "message": "Invalid or expired authentication"
            }
        elif response.status_code == 403:
            return {
                "status": "error", 
                "message": f"You don't have access to tenant {tenant_id}"
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to execute DSL batch: HTTP {response.status_code}"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Network error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to execute DSL batch: {str(e)}"
        }



# Import auth tools
from .auth_tools import check_authentication_status, get_user_business_info

# List of all available tool functions
ALL_TOOL_FUNCTIONS = [
    execute_dsl_batch,
    check_authentication_status,
    get_user_business_info,
]