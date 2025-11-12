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
        
    For 'update_profile' action, data can be in two formats:
    
    FORMAT 1 - Structured (recommended):
    data = {
        "profile_data": {
            "full_name": "Juan Pérez García",
            "first_name": "Juan",
            "last_name": "Pérez",
            "mother_last_name": "García",
            "birth_date": "1990-01-01",
            "nationality": "mexicana",
            "contact_info": {
                "email": "juan@example.com",
                "phone": "5512345678"
            },
            "address": {
                "street": "Av. Reforma 123",
                "neighborhood": "Centro",
                "postal_code": "06000",
                "municipality": "Cuauhtémoc",
                "state": "Ciudad de México"
            }
        }
    }
    
    FORMAT 2 - Direct (for compatibility):
    data = {
        "nombre": "Juan Pérez García",           # Maps to full_name
        "email": "juan@example.com",            # Maps to contact_info.email  
        "telefono": "5512345678"                # Maps to contact_info.phone
    }
        
    Returns:
        Dict with operation result and current state
    """
    
    # Debug logging
    print(f"🗂️ TOOL DEBUG: manage_conversation_state called")
    print(f"🗂️ TOOL DEBUG: action={action}, session_id={session_id}, conversation_id={conversation_id}")
    print(f"🗂️ TOOL DEBUG: data={data}")
    
    result = {
        "success": False,
        "action": action,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "data": None,
        "errors": []
    }
    
    print(f"🗂️ TOOL DEBUG: Getting database session...")
    
    # Get database session using proper generator pattern
    db_generator = get_database()
    db: Session = next(db_generator)
    print(f"🗂️ TOOL DEBUG: Database session acquired successfully")
    
    try:
        if action == "create":
            # Create new tramite session
            data = data or {}  # Handle None data
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
            data = data or {}  # Handle None data
            new_phase = data.get("phase")
            
            session = db.query(TramiteSession).filter(
                TramiteSession.id == session_id
            ).first()
            
            if not session:
                result["errors"].append(f"Session {session_id} not found")
                return result
                
            old_phase = session.current_phase
            session.current_phase = new_phase
            session.updated_at = datetime.now()
            
            db.commit()
            
            result["success"] = True
            result["data"] = {
                "previous_phase": old_phase,
                "current_phase": new_phase,
                "updated_at": datetime.now().isoformat()
            }
            
        elif action == "update_step":
            # Update current RFC flow step (new action for step tracking)
            data = data or {}  # Handle None data
            new_step = data.get("step")
            
            session = db.query(TramiteSession).filter(
                TramiteSession.id == session_id
            ).first()
            
            if not session:
                result["errors"].append(f"Session {session_id} not found")
                return result
                
            # Store current step in current_phase field with "STEP_" prefix
            old_step = session.current_phase
            session.current_phase = f"STEP_{new_step}"
            session.updated_at = datetime.now()
            
            db.commit()
            
            result["success"] = True
            result["data"] = {
                "previous_step": old_step,
                "current_step": new_step,
                "updated_at": datetime.now().isoformat()
            }
                
        elif action == "update_profile":
            # Update user profile
            data = data or {}  # Handle None data
            profile_updates = data.get("profile_data", {})
            
            # COMPATIBILITY: Handle direct data format from agent
            # If profile_data is empty but we have direct fields, use those
            if not profile_updates and data:
                profile_updates = data.copy()
                print(f"🗂️ TOOL DEBUG: Using direct data format: {profile_updates}")
            
            session = db.query(TramiteSession).filter(
                TramiteSession.id == session_id
            ).first()
            
            if not session:
                print(f"❌ TOOL ERROR: Session {session_id} not found, attempting auto-creation...")
                
                # Auto-create session if it doesn't exist (similar to get_state action)
                try:
                    new_session = TramiteSession(
                        id=session_id,
                        conversation_id=conversation_id,
                        tramite_type=TramiteType.SAT_RFC_INSCRIPCION_PF.value,
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
                    db.flush()  # Flush to get IDs before using them
                    
                    print(f"🗂️ TOOL DEBUG: Auto-created session {session_id} with user_profile successfully")
                    session = new_session
                    
                except Exception as auto_create_error:
                    print(f"❌ TOOL ERROR: Failed to auto-create session: {auto_create_error}")
                    result["errors"].append(f"Session {session_id} not found and auto-creation failed: {str(auto_create_error)}")
                    return result
                
            user_profile = session.user_profile
            if not user_profile:
                result["errors"].append(f"User profile not found for session {session_id}")
                return result
            
            # Update profile fields with multiple field name support
            updated_fields = []
            
            # Handle full_name / nombre / nombre_completo
            for name_field in ["full_name", "nombre", "nombre_completo"]:
                if name_field in profile_updates:
                    user_profile.full_name = profile_updates[name_field]
                    updated_fields.append("full_name")
                    print(f"🗂️ TOOL DEBUG: Updated full_name from '{name_field}': {profile_updates[name_field]}")
                    break
                    
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
                birth_date_value = profile_updates["birth_date"]
                # Convert string date to datetime.date object if needed
                if isinstance(birth_date_value, str):
                    try:
                        # Try common date formats
                        if "-" in birth_date_value:  # YYYY-MM-DD
                            birth_date_obj = datetime.strptime(birth_date_value, "%Y-%m-%d").date()
                        elif "/" in birth_date_value:  # MM/DD/YYYY or DD/MM/YYYY
                            birth_date_obj = datetime.strptime(birth_date_value, "%m/%d/%Y").date()
                        else:
                            birth_date_obj = datetime.strptime(birth_date_value, "%Y-%m-%d").date()
                        
                        user_profile.birth_date = birth_date_obj
                        updated_fields.append("birth_date")
                        print(f"🗂️ TOOL DEBUG: Updated birth_date from string '{birth_date_value}' to date object")
                    except ValueError as e:
                        print(f"🗂️ TOOL DEBUG: Failed to parse birth_date '{birth_date_value}': {e}")
                        result["errors"].append(f"Invalid birth_date format: {birth_date_value}")
                else:
                    user_profile.birth_date = birth_date_value
                    updated_fields.append("birth_date")
                    print(f"🗂️ TOOL DEBUG: Updated birth_date with date object")
                
            if "nationality" in profile_updates:
                user_profile.nationality = profile_updates["nationality"]
                updated_fields.append("nationality")
            
            # Handle economic activity (stored as session metadata for now)
            for activity_field in ["activity_economic", "actividad_economica", "economic_activity"]:
                if activity_field in profile_updates:
                    # For now, we'll store this in the session metadata or add to validation notes
                    # Since there's no direct field in UserProfile for economic activity
                    print(f"🗂️ TOOL DEBUG: Economic activity identified: {profile_updates[activity_field]}")
                    updated_fields.append("economic_activity")
                    break
            
            # Update contact info - handle both nested and direct formats
            contact_updates = profile_updates.get("contact_info", {})
            
            # COMPATIBILITY: Check for direct contact fields in main data
            direct_contact_fields = {}
            for field_name, expected_name in [("email", "email"), ("telefono", "phone"), ("phone", "phone")]:
                if field_name in profile_updates:
                    direct_contact_fields[expected_name] = profile_updates[field_name]
            
            # Merge direct fields with nested contact_info
            contact_updates.update(direct_contact_fields)
            
            if contact_updates:
                print(f"🗂️ TOOL DEBUG: Processing contact updates: {contact_updates}")
                contact_info = user_profile.contact_info
                print(f"🗂️ TOOL DEBUG: Existing contact_info: {contact_info}")
                
                if not contact_info:
                    print(f"🗂️ TOOL DEBUG: Creating new ContactInfo for user_profile_id: {user_profile.id}")
                    contact_info = ContactInfo(user_profile_id=user_profile.id)
                    db.add(contact_info)
                    db.flush()  # Ensure the ContactInfo gets an ID before proceeding
                    print(f"🗂️ TOOL DEBUG: ContactInfo created successfully with id: {contact_info.id}")
                    
                if "email" in contact_updates:
                    old_email = contact_info.email
                    contact_info.email = contact_updates["email"]
                    updated_fields.append("email")
                    print(f"🗂️ TOOL DEBUG: Updated email: {old_email} → {contact_updates['email']}")
                    
                if "phone" in contact_updates:
                    old_phone = contact_info.phone
                    contact_info.phone = contact_updates["phone"] 
                    updated_fields.append("phone")
                    print(f"🗂️ TOOL DEBUG: Updated phone: {old_phone} → {contact_updates['phone']}")
                
                print(f"🗂️ TOOL DEBUG: ContactInfo final state - email: {contact_info.email}, phone: {contact_info.phone}")
            
            # Update address - handle both nested and direct formats
            address_updates = profile_updates.get("address", {})
            
            # COMPATIBILITY: Handle 'direccion' field from agent
            if "direccion" in profile_updates:
                if isinstance(profile_updates["direccion"], dict):
                    address_updates.update(profile_updates["direccion"])
                    print(f"🗂️ TOOL DEBUG: Found direccion dict: {profile_updates['direccion']}")
                elif isinstance(profile_updates["direccion"], str):
                    # Parse simple address string
                    address_updates["street"] = profile_updates["direccion"]
                    print(f"🗂️ TOOL DEBUG: Found direccion string: {profile_updates['direccion']}")
            
            # COMPATIBILITY: Map Spanish field names to English
            address_field_mapping = {
                "calle": "street",
                "numero_exterior": "exterior_number",
                "numero_interior": "interior_number",
                "colonia": "neighborhood",
                "codigo_postal": "postal_code",
                "municipio": "municipality",
                "delegacion": "municipality",  # Maps delegacion → municipality
                "estado": "state"
            }
            
            # Apply field mapping
            for spanish_field, english_field in address_field_mapping.items():
                if spanish_field in address_updates:
                    address_updates[english_field] = address_updates[spanish_field]
                    print(f"🗂️ TOOL DEBUG: Mapped address field '{spanish_field}' → '{english_field}': {address_updates[spanish_field]}")
                    # Remove the original Spanish field to avoid duplication
                    del address_updates[spanish_field]
            
            if address_updates:
                address = user_profile.address
                if not address:
                    address = Address(user_profile_id=user_profile.id)
                    db.add(address)
                    print(f"🗂️ TOOL DEBUG: Created new Address for user_profile_id: {user_profile.id}")
                    
                address_fields = ["street", "exterior_number", "interior_number", 
                                "neighborhood", "postal_code", "municipality", "state"]
                for field in address_fields:
                    if field in address_updates:
                        setattr(address, field, address_updates[field])
                        updated_fields.append(field)
                        print(f"🗂️ TOOL DEBUG: Updated address.{field}: {address_updates[field]}")
            
            # Update timestamp and commit changes
            user_profile.updated_at = datetime.now()
            print(f"🗂️ TOOL DEBUG: Updated user_profile.updated_at: {user_profile.updated_at}")
            print(f"🗂️ TOOL DEBUG: Updated fields: {updated_fields}")
            
            try:
                print(f"🗂️ TOOL DEBUG: About to commit transaction...")
                db.commit()
                print(f"✅ TOOL SUCCESS: Transaction committed successfully!")
                
                result["success"] = True
                result["data"] = {
                    "updated_fields": updated_fields,
                    "updated_at": datetime.now().isoformat(),
                    "session_id": session_id,
                    "user_profile_id": user_profile.id
                }
                
            except Exception as commit_error:
                print(f"❌ TOOL ERROR: Failed to commit transaction: {commit_error}")
                print(f"❌ TOOL ERROR: Commit error type: {type(commit_error)}")
                db.rollback()
                result["errors"].append(f"Failed to save changes: {str(commit_error)}")
                return result
            
        elif action == "get_state":
            # Get current session state with auto-creation fallback
            session = db.query(TramiteSession).filter(
                TramiteSession.id == session_id
            ).first()
            
            if not session:
                print(f"🗂️ TOOL DEBUG: Session {session_id} not found, attempting auto-creation...")
                
                # Auto-create session if it doesn't exist
                try:
                    new_session = TramiteSession(
                        id=session_id,
                        conversation_id=conversation_id,
                        tramite_type=TramiteType.SAT_RFC_INSCRIPCION_PF.value,
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
                    
                    print(f"🗂️ TOOL DEBUG: Auto-created session {session_id} successfully")
                    session = new_session
                    
                except Exception as auto_create_error:
                    print(f"❌ TOOL ERROR: Failed to auto-create session: {auto_create_error}")
                    result["errors"].append(f"Session {session_id} not found and auto-creation failed: {str(auto_create_error)}")
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
            data = data or {}  # Handle None data
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
                
            session.updated_at = datetime.now()
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
        print(f"❌ TOOL ERROR: manage_conversation_state failed: {str(e)}")
        print(f"❌ TOOL ERROR: Exception type: {type(e)}")
        import traceback
        print(f"❌ TOOL ERROR: Full traceback:")
        traceback.print_exc()
        
        try:
            db.rollback()
            print(f"🗂️ TOOL DEBUG: Transaction rolled back successfully")
        except Exception as rollback_error:
            print(f"❌ TOOL ERROR: Failed to rollback transaction: {rollback_error}")
            
        result["errors"].append(f"Database error: {str(e)}")
    finally:
        try:
            db.close()
            print(f"🗂️ TOOL DEBUG: Database session closed")
        except Exception as close_error:
            print(f"❌ TOOL ERROR: Failed to close database session: {close_error}")
            
        # Also close the generator properly
        try:
            db_generator.close()
        except Exception:
            pass  # Generator might not be closable in all cases
    
    print(f"🗂️ TOOL DEBUG: Returning result: {result}")
    return result