# Copyright 2024 SEMOVI Multiagent System

"""Authentication tools for direct login within SEMOVI agent."""

import os
import requests
from datetime import datetime

from google.adk.tools.tool_context import ToolContext


def authenticate_user(user_email: str, user_password: str, tool_context: ToolContext):
    """
    Authenticate user directly with email and password for testing purposes.
    
    Args:
        tool_context: Context for accessing session state
        email: User's email address
        password: User's password
        
    Returns:
        Dict with authentication results and user profile
    """
    try:
        # Validate inputs
        if not user_email or not user_email.strip():
            return {
                "status": "error",
                "message": "Email is required for authentication"
            }
        
        if not user_password or not user_password.strip():
            return {
                "status": "error", 
                "message": "Password is required for authentication"
            }
        
        # Get Supabase configuration
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_anon_key:
            return {
                "status": "error",
                "message": "Sistema de autenticación no configurado. Contacte al administrador."
            }
        
        # Prepare authentication request
        auth_data = {
            "email": user_email.strip().lower(),
            "password": user_password
        }
        
        headers = {
            "apikey": supabase_anon_key,
            "Content-Type": "application/json"
        }
        
        # Authenticate with Supabase Auth
        auth_response = requests.post(
            f"{supabase_url}/auth/v1/token?grant_type=password",
            headers=headers,
            json=auth_data,
            timeout=10
        )
        
        if auth_response.status_code == 200:
            auth_result = auth_response.json()
            access_token = auth_result.get("access_token")
            user_data = auth_result.get("user", {})
            
            if not access_token:
                return {
                    "status": "error",
                    "message": "Error en autenticación. Token no recibido."
                }
            
            # Store JWT token in session state
            tool_context.state["jwt_token"] = access_token
            tool_context.state["auth_user_id"] = user_data.get("id")
            tool_context.state["authenticated_at"] = datetime.now().isoformat()
            
            # Get user profile from profiles table
            profile_result = _get_user_profile_by_token(tool_context, access_token)
            
            if profile_result["status"] == "success":
                profile = profile_result["profile"]
                
                # Store user profile in session
                tool_context.state["user_profile"] = profile
                
                # Update process stage to authenticated
                tool_context.state["process_stage"] = "authenticated"
                
                return {
                    "status": "success",
                    "message": f"¡Bienvenido/a {profile.get('first_name', '')} {profile.get('last_name', '')}!",
                    "user_profile": profile,
                    "access_token": access_token,
                    "authentication_timestamp": tool_context.state["authenticated_at"]
                }
            else:
                # Auth successful but profile retrieval failed - still allow access
                return {
                    "status": "partial_success",
                    "message": f"Autenticación exitosa. Bienvenido/a {user_data.get('email', user_email)}!",
                    "user_email": user_data.get("email"),
                    "access_token": access_token,
                    "profile_error": profile_result.get("message", ""),
                    "authentication_timestamp": tool_context.state["authenticated_at"]
                }
        
        elif auth_response.status_code == 400:
            # Invalid credentials
            return {
                "status": "error",
                "message": "Credenciales inválidas. Por favor verifica tu email y contraseña."
            }
        else:
            # Other authentication error
            return {
                "status": "error",
                "message": f"Error de autenticación: {auth_response.status_code}. Intenta nuevamente."
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Tiempo de espera agotado. Verifica tu conexión a internet e intenta nuevamente."
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Error de red: {str(e)}. Verifica tu conexión e intenta nuevamente."
        }
    except Exception as e:
        # Store error in state for debugging
        tool_context.state["last_auth_error"] = {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "status": "error",
            "message": f"Error inesperado en autenticación: {str(e)}"
        }


def _get_user_profile_by_token(tool_context: ToolContext, auth_token: str):
    """
    Get user profile information using JWT token.
    
    Args:
        tool_context: Tool context for state access
        jwt_token: JWT access token
        
    Returns:
        Dict with user profile information
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_anon_key:
            return {
                "status": "error",
                "message": "Configuración de base de datos no encontrada"
            }
        
        # Headers for authenticated request
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "apikey": supabase_anon_key,
            "Content-Type": "application/json"
        }
        
        # Get user profile from profiles table (RLS will ensure only user's own profile)
        response = requests.get(
            f"{supabase_url}/rest/v1/profiles?select=*",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            profiles = response.json()
            if profiles and len(profiles) > 0:
                profile = profiles[0]  # Should only return user's own profile due to RLS
                
                return {
                    "status": "success",
                    "profile": {
                        "id": profile.get("id"),
                        "first_name": profile.get("first_name", ""),
                        "last_name": profile.get("last_name", ""),
                        "phone": profile.get("phone", ""),
                        "profile_type": profile.get("profile_type", "citizen"),
                        "is_active": profile.get("is_active", True),
                        "created_at": profile.get("created_at")
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": "Perfil de usuario no encontrado"
                }
        else:
            return {
                "status": "error",
                "message": f"Error obteniendo perfil: {response.status_code}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error obteniendo perfil: {str(e)}"
        }


def check_authentication_status(tool_context: ToolContext):
    """
    Check if user is currently authenticated and return status.
    
    Args:
        tool_context: Tool context for accessing session state
        
    Returns:
        Dict with authentication status
    """
    try:
        # Check if JWT token exists in state
        jwt_token = tool_context.state.get("jwt_token")
        auth_user_id = tool_context.state.get("auth_user_id")
        authenticated_at = tool_context.state.get("authenticated_at")
        user_profile = tool_context.state.get("user_profile", {})
        
        if jwt_token and auth_user_id:
            # User is authenticated
            first_name = user_profile.get("first_name", "")
            last_name = user_profile.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip()
            
            return {
                "status": "authenticated",
                "authenticated": True,
                "user_id": auth_user_id,
                "full_name": full_name,
                "first_name": first_name,
                "last_name": last_name,
                "profile_type": user_profile.get("profile_type", "citizen"),
                "authenticated_at": authenticated_at,
                "message": f"Usuario autenticado: {full_name if full_name else 'Usuario'}"
            }
        else:
            # User is not authenticated
            return {
                "status": "not_authenticated",
                "authenticated": False,
                "message": "Usuario no autenticado. Por favor proporciona tu email y contraseña."
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error verificando autenticación: {str(e)}"
        }


def logout_user(tool_context: ToolContext):
    """
    Logout user by clearing authentication data from session.
    
    Args:
        tool_context: Tool context for accessing session state
        
    Returns:
        Dict with logout results
    """
    try:
        # Get user info before clearing
        user_profile = tool_context.state.get("user_profile", {})
        first_name = user_profile.get("first_name", "Usuario")
        
        # Clear authentication data from session
        auth_keys_to_clear = [
            "jwt_token",
            "auth_user_id", 
            "authenticated_at",
            "user_profile"
        ]
        
        for key in auth_keys_to_clear:
            if key in tool_context.state:
                del tool_context.state[key]
        
        # Reset process stage
        tool_context.state["process_stage"] = "welcome"
        
        # Log logout
        tool_context.state["last_logout"] = {
            "timestamp": datetime.now().isoformat(),
            "user_name": first_name
        }
        
        return {
            "status": "success", 
            "message": f"¡Hasta luego, {first_name}! Has cerrado sesión exitosamente."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error cerrando sesión: {str(e)}"
        }


def request_user_credentials(tool_context: ToolContext):
    """
    Request user credentials for authentication.
    
    Args:
        tool_context: Tool context for state access
        
    Returns:
        Dict with credential request message
    """
    return {
        "status": "credentials_required",
        "message": """🔐 **Autenticación Requerida**

Para acceder a los servicios de SEMOVI, necesito que te autentiques.

Por favor proporciona:
- **Email**: Tu dirección de correo electrónico registrada
- **Contraseña**: Tu contraseña de acceso

Ejemplo:
"Mi email es usuario@email.com y mi contraseña es mipassword123"

Una vez autenticado, podré ayudarte con todos los trámites de SEMOVI de manera personalizada.""",
        "required_fields": ["email", "password"],
        "authentication_step": "credentials_request"
    }