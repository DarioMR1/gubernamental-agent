from langchain.tools import tool
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
from sqlalchemy.orm import Session
from data.database import get_database
from data.models import TramiteSession, UserProfile, ContactInfo, Address, ChecklistItem
from domain_types.tramite_types import TramiteType, ConversationPhase


@tool("manage_conversation_state")
def manage_conversation_state(
    action: str, 
    session_id: str,
    conversation_id: str,
    data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Manages the conversation state for tramite sessions using real SQLite database.
    
    Actions:
    - 'create': Create new tramite session
    - 'update_phase': Update current conversation phase  
    - 'update_profile': Update user profile data
    - 'get_state': Get current conversation state
    - 'add_document': Add validated document to session
    - 'update_checklist': Update checklist progress
    
    Args:
        action: The action to perform
        session_id: Unique session identifier
        conversation_id: Associated conversation ID
        data: Action-specific data
        
    Returns:
        Dict with operation result and current state
    """
    
    result = {
        "success": False,
        "action": action,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "data": None,
        "errors": []
    }
    
    db: Session = next(get_database())
    
    try:
        if action == "create":
            # Create new tramite session
            tramite_type = data.get("tramite_type", TramiteType.SAT_RFC_INSCRIPCION_PF.value)
            
            # Check if session already exists
            existing_session = db.query(TramiteSession).filter(
                TramiteSession.id == session_id
            ).first()
            
            if existing_session:
                result["data"] = {
                    "session_id": existing_session.id,
                    "tramite_type": existing_session.tramite_type,
                    "current_phase": existing_session.current_phase,
                    "completion_percentage": existing_session.completion_percentage
                }
                result["success"] = True
                return result
            
            # Create new session
            new_session = TramiteSession(
                id=session_id,
                conversation_id=conversation_id,
                tramite_type=tramite_type,
                current_phase=ConversationPhase.WELCOME.value,
                completion_percentage=0.0,
                is_completed=False
            )
            
            db.add(new_session)
            
            # Create empty user profile
            user_profile = UserProfile(
                tramite_session_id=session_id,
                nationality="mexicana"
            )
            
            db.add(user_profile)
            db.commit()
            
            result["success"] = True
            result["data"] = {
                "session_id": session_id,
                "tramite_type": tramite_type,
                "current_phase": ConversationPhase.WELCOME.value,
                "completion_percentage": 0.0,
                "created_at": datetime.now().isoformat()
            }
            
        elif action == "update_phase":
            # Update conversation phase
            new_phase = data.get("phase")
            
            session = db.query(TramiteSession).filter(
                TramiteSession.id == session_id
            ).first()
            
            if not session:
                result["errors"].append(f"Session {session_id} not found")
                return result
                
            old_phase = session.current_phase
            session.current_phase = new_phase
            session.updated_at = datetime.utcnow()
            
            db.commit()
            
            result["success"] = True
            result["data"] = {
                "previous_phase": old_phase,
                "current_phase": new_phase,
                "updated_at": datetime.now().isoformat()
            }
                
        elif action == "update_profile":
            # Update user profile
            profile_updates = data.get("profile_data", {})
            
            session = db.query(TramiteSession).filter(
                TramiteSession.id == session_id
            ).first()
            
            if not session:
                result["errors"].append(f"Session {session_id} not found")
                return result
                
            user_profile = session.user_profile
            if not user_profile:
                result["errors"].append(f"User profile not found for session {session_id}")
                return result
            
            # Update profile fields
            updated_fields = []
            if "full_name" in profile_updates:
                user_profile.full_name = profile_updates["full_name"]
                updated_fields.append("full_name")
                
            if "first_name" in profile_updates:
                user_profile.first_name = profile_updates["first_name"]
                updated_fields.append("first_name")
                
            if "last_name" in profile_updates:
                user_profile.last_name = profile_updates["last_name"]
                updated_fields.append("last_name")
                
            if "mother_last_name" in profile_updates:
                user_profile.mother_last_name = profile_updates["mother_last_name"]
                updated_fields.append("mother_last_name")
                
            if "birth_date" in profile_updates:
                user_profile.birth_date = profile_updates["birth_date"]
                updated_fields.append("birth_date")
                
            if "nationality" in profile_updates:
                user_profile.nationality = profile_updates["nationality"]
                updated_fields.append("nationality")
            
            # Update contact info
            contact_updates = profile_updates.get("contact_info", {})
            if contact_updates:
                contact_info = user_profile.contact_info
                if not contact_info:
                    contact_info = ContactInfo(user_profile_id=user_profile.id)
                    db.add(contact_info)
                    
                if "email" in contact_updates:
                    contact_info.email = contact_updates["email"]
                    updated_fields.append("email")
                    
                if "phone" in contact_updates:
                    contact_info.phone = contact_updates["phone"] 
                    updated_fields.append("phone")
            
            # Update address
            address_updates = profile_updates.get("address", {})
            if address_updates:
                address = user_profile.address
                if not address:
                    address = Address(user_profile_id=user_profile.id)
                    db.add(address)
                    
                address_fields = ["street", "exterior_number", "interior_number", 
                                "neighborhood", "postal_code", "municipality", "state"]
                for field in address_fields:
                    if field in address_updates:
                        setattr(address, field, address_updates[field])
                        updated_fields.append(field)
            
            user_profile.updated_at = datetime.utcnow()
            db.commit()
            
            result["success"] = True
            result["data"] = {
                "updated_fields": updated_fields,
                "updated_at": datetime.now().isoformat()
            }
            
        elif action == "get_state":
            # Get current session state
            session = db.query(TramiteSession).filter(
                TramiteSession.id == session_id
            ).first()
            
            if not session:
                result["errors"].append(f"Session {session_id} not found")
                return result
                
            profile_data = {}
            if session.user_profile:
                profile = session.user_profile
                profile_data = {
                    "full_name": profile.full_name,
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                    "birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
                    "nationality": profile.nationality
                }
                
                if profile.contact_info:
                    profile_data["contact_info"] = {
                        "email": profile.contact_info.email,
                        "phone": profile.contact_info.phone
                    }
                    
                if profile.address:
                    profile_data["address"] = {
                        "street": profile.address.street,
                        "postal_code": profile.address.postal_code,
                        "municipality": profile.address.municipality,
                        "state": profile.address.state
                    }
            
            result["success"] = True
            result["data"] = {
                "session_id": session.id,
                "tramite_type": session.tramite_type,
                "current_phase": session.current_phase,
                "completion_percentage": session.completion_percentage,
                "is_completed": session.is_completed,
                "user_profile": profile_data,
                "last_updated": session.updated_at.isoformat() if session.updated_at else None
            }
            
        elif action == "add_document":
            # This would be handled by the document validation tool
            result["success"] = True
            result["data"] = {"message": "Document handling delegated to document validation tool"}
            
        elif action == "update_checklist":
            # Update checklist progress
            session = db.query(TramiteSession).filter(
                TramiteSession.id == session_id
            ).first()
            
            if not session:
                result["errors"].append(f"Session {session_id} not found")
                return result
                
            completion_percentage = data.get("completion_percentage", session.completion_percentage)
            session.completion_percentage = completion_percentage
            
            if completion_percentage >= 100:
                session.is_completed = True
                
            session.updated_at = datetime.utcnow()
            db.commit()
            
            result["success"] = True
            result["data"] = {
                "completion_percentage": completion_percentage,
                "is_completed": session.is_completed,
                "updated_at": datetime.now().isoformat()
            }
            
        else:
            result["errors"].append(f"Unknown action: {action}")
            
    except Exception as e:
        db.rollback()
        result["errors"].append(f"Database error: {str(e)}")
    finally:
        db.close()
        
    return result