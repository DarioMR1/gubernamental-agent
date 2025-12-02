# Copyright 2024 SEMOVI Multiagent System

"""Tools for license type determination and cost calculation."""

from datetime import datetime, date
from typing import Optional

from google.adk.tools.tool_context import ToolContext


def determine_license_requirements(
    tool_context: ToolContext,
    vehicle_type: str,  # auto | motorcycle  
    procedure: str  # expedition | renewal | replacement
):
    """
    Determine license type and requirements based on vehicle and procedure.
    
    Args:
        tool_context: Context for accessing session state
        vehicle_type: Type of vehicle (auto or motorcycle)
        cylinder_capacity: Engine cylinder capacity for motorcycles
        procedure: Type of procedure needed
        
    Returns:
        Dict with license type, costs, and requirements
    """
    try:
        # Normalize and validate inputs
        vehicle_type_mapping = {
            "auto": "auto", "automovil": "auto", "automobile": "auto", "car": "auto",
            "motorcycle": "motorcycle", "motocicleta": "motorcycle", "moto": "motorcycle"
        }
        
        procedure_mapping = {
            "expedition": "expedition", "expedicion": "expedition", "primera": "expedition", "first": "expedition",
            "renewal": "renewal", "renovacion": "renewal", "renovar": "renewal", "renew": "renewal",
            "replacement": "replacement", "reposicion": "replacement", "reponer": "replacement", "replace": "replacement"
        }
        
        # Normalize inputs
        vehicle_type_normalized = vehicle_type_mapping.get(vehicle_type.lower(), vehicle_type)
        procedure_normalized = procedure_mapping.get(procedure.lower(), procedure)
        
        if vehicle_type_normalized not in ["auto", "motorcycle"]:
            return {
                "status": "error",
                "message": f"Vehicle type '{vehicle_type}' not recognized. Must be 'auto' or 'motorcycle'"
            }
        
        if procedure_normalized not in ["expedition", "renewal", "replacement"]:
            return {
                "status": "error", 
                "message": f"Procedure '{procedure}' not recognized. Must be 'expedition', 'renewal', or 'replacement'"
            }
        
        # Use normalized values
        vehicle_type = vehicle_type_normalized
        procedure = procedure_normalized
        
        # Get cylinder_capacity from context if needed for motorcycles
        cylinder_capacity = None
        if vehicle_type == "motorcycle":
            # Try to get from session state first
            service_info = tool_context.state.get("service_determination", {})
            vehicle_info = service_info.get("vehicle_info", {})
            cylinder_capacity = vehicle_info.get("cylinder_capacity")
            
            # If not in state, default to 250cc for basic motorcycle license
            if cylinder_capacity is None:
                cylinder_capacity = 250
        
        # Determine license type
        license_determination = _determine_license_type(vehicle_type, cylinder_capacity)
        
        if license_determination["status"] != "success":
            return license_determination
        
        license_type = license_determination["license_type"]
        
        # Get costs and requirements
        cost_info = _get_cost_information(license_type, procedure)
        requirements_info = _get_requirements_information(license_type, procedure)
        
        # Calculate age requirements
        user_birth_date = tool_context.state.get("user_data", {}).get("birth_date", "")
        age_validation = _validate_age_requirements(license_type, user_birth_date)
        
        # Compile complete information
        result = {
            "status": "success",
            "license_type": license_type,
            "procedure_type": procedure.upper(),
            "vehicle_info": {
                "type": vehicle_type,
                "cylinder_capacity": cylinder_capacity
            },
            "costs": cost_info,
            "requirements": requirements_info,
            "age_validation": age_validation,
            "processing_time_days": 1,
            "validity_years": 3
        }
        
        # Store in session state
        tool_context.state["service_determination"] = result
        tool_context.state["process_stage"] = "service_determined"
        
        # Flatten key variables for template access
        tool_context.state["license_type"] = license_type
        tool_context.state["procedure_type"] = procedure.upper()
        
        return result
        
    except Exception as e:
        tool_context.state["last_error"] = {
            "tool": "determine_license_requirements",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "status": "error",
            "message": f"Error determining license requirements: {str(e)}"
        }


def _determine_license_type(vehicle_type, cylinder_capacity):
    """Determine the specific license type based on vehicle characteristics."""
    
    if vehicle_type == "auto":
        return {
            "status": "success",
            "license_type": "LIC_A",
            "description": "License for private automobiles and motorcycles up to 400cc"
        }
    
    elif vehicle_type == "motorcycle":
        if cylinder_capacity is None:
            return {
                "status": "error",
                "message": "Cylinder capacity is required for motorcycles"
            }
        
        if cylinder_capacity <= 125:
            return {
                "status": "success", 
                "license_type": "LIC_A1",
                "description": "License for motorcycles from 125cc up to 400cc"
            }
        elif cylinder_capacity <= 400:
            return {
                "status": "success",
                "license_type": "LIC_A1", 
                "description": "License for motorcycles from 125cc up to 400cc"
            }
        else:  # > 400cc
            return {
                "status": "success",
                "license_type": "LIC_A2",
                "description": "License for motorcycles greater than 400cc"
            }
    
    return {
        "status": "error",
        "message": f"Unknown vehicle type: {vehicle_type}"
    }


def _get_cost_information(license_type, procedure):
    """Get detailed cost information for license and procedure."""
    
    # Base costs for each license type
    base_costs = {
        "LIC_A": 866.00,
        "LIC_A1": 651.00, 
        "LIC_A2": 1055.00
    }
    
    # Additional costs for procedures
    procedure_costs = {
        "expedition": 0.00,  # No additional cost for first time
        "renewal": 0.00,     # No additional cost for renewal
        "replacement": 158.00  # Additional cost for replacement
    }
    
    base_cost = base_costs.get(license_type, 0.00)
    additional_cost = procedure_costs.get(procedure.lower(), 0.00)
    total_cost = base_cost + additional_cost
    
    return {
        "base_cost": base_cost,
        "additional_cost": additional_cost,
        "total_cost": total_cost,
        "currency": "MXN",
        "cost_breakdown": {
            "license_fee": base_cost,
            "procedure_fee": additional_cost
        }
    }


def _get_requirements_information(license_type, procedure):
    """Get specific requirements for license type and procedure."""
    
    # Base requirements for all licenses
    base_requirements = [
        "Official identification (INE/Passport)",
        "CURP (Population Registry Code)",
        "Proof of address (not older than 3 months)",
        "Birth certificate (certified copy)",
        "Valid medical examination"
    ]
    
    # Specific requirements by license type
    license_specific = {
        "LIC_A": [
            "Driving course certificate (for expedition)",
            "RFC (Tax ID) if applicable"
        ],
        "LIC_A1": [
            "Motorcycle driving course certificate",
            "RFC (Tax ID) if applicable"
        ],
        "LIC_A2": [
            "Advanced motorcycle course certificate", 
            "Valid LIC_A1 (for upgrade)",
            "Advanced medical examination",
            "RFC (Tax ID) if applicable"
        ]
    }
    
    # Procedure-specific requirements
    procedure_specific = {
        "expedition": [
            "Driving course completion certificate",
            "Medical examination (specific for license type)"
        ],
        "renewal": [
            "Previous license (original)",
            "Updated medical examination"
        ],
        "replacement": [
            "Police report (in case of theft)",
            "Sworn statement of truth",
            "Additional identification document"
        ]
    }
    
    # Compile all requirements
    all_requirements = base_requirements.copy()
    all_requirements.extend(license_specific.get(license_type, []))
    all_requirements.extend(procedure_specific.get(procedure.lower(), []))
    
    # Remove duplicates while preserving order
    unique_requirements = []
    seen = set()
    for req in all_requirements:
        if req not in seen:
            unique_requirements.append(req)
            seen.add(req)
    
    return {
        "total_requirements": len(unique_requirements),
        "required_documents": unique_requirements,
        "base_requirements": base_requirements,
        "license_specific": license_specific.get(license_type, []),
        "procedure_specific": procedure_specific.get(procedure.lower(), [])
    }


def _validate_age_requirements(license_type, birth_date):
    """Validate age requirements for specific license type."""
    
    age_requirements = {
        "LIC_A": 18,   # 18+ for auto and basic motorcycle
        "LIC_A1": 18,  # 18+ for intermediate motorcycle
        "LIC_A2": 21   # 21+ for high-power motorcycle
    }
    
    if not birth_date:
        return {
            "status": "pending",
            "message": "Birth date required for age validation",
            "required_age": age_requirements.get(license_type, 18)
        }
    
    try:
        # Parse birth date
        birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
        today = date.today()
        
        # Calculate age
        age = today.year - birth_date_obj.year
        if today.month < birth_date_obj.month or \
           (today.month == birth_date_obj.month and today.day < birth_date_obj.day):
            age -= 1
        
        required_age = age_requirements.get(license_type, 18)
        is_eligible = age >= required_age
        
        return {
            "status": "validated",
            "current_age": age,
            "required_age": required_age,
            "is_eligible": is_eligible,
            "message": f"Age validation: {age} years old" + 
                      (f" (meets requirement of {required_age}+)" if is_eligible 
                       else f" (requires {required_age}+)")
        }
        
    except ValueError:
        return {
            "status": "error",
            "message": "Invalid birth date format. Please use YYYY-MM-DD format.",
            "required_age": age_requirements.get(license_type, 18)
        }


def calculate_total_cost(license_type: str, procedure_type: str, tool_context: ToolContext):
    """
    Calculate total cost for license and procedure.
    
    Args:
        tool_context: Tool context for state access
        license_type: Type of license (LICENSE_A, LICENSE_A1, LICENSE_A2)
        procedure_type: Type of procedure (EXPEDITION, RENEWAL, REPLACEMENT)
        
    Returns:
        Dict with detailed cost calculation
    """
    try:
        cost_info = _get_cost_information(license_type, procedure_type.lower())
        
        # Store cost calculation in state
        tool_context.state["cost_calculation"] = {
            **cost_info,
            "calculated_at": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "cost_details": cost_info,
            "message": f"Total cost: ${cost_info['total_cost']:.2f} MXN"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error calculating cost: {str(e)}"
        }


def get_specific_requirements(license_type: str, procedure_type: str, tool_context: ToolContext):
    """
    Get specific requirements list for given license and procedure.
    
    Args:
        tool_context: Tool context for state access
        license_type: Type of license
        procedure_type: Type of procedure
        
    Returns:
        Dict with specific requirements
    """
    try:
        requirements_info = _get_requirements_information(license_type, procedure_type.lower())
        
        # Format requirements for display
        formatted_requirements = []
        for i, req in enumerate(requirements_info["required_documents"], 1):
            formatted_requirements.append(f"{i}. {req}")
        
        return {
            "status": "success",
            "requirements": requirements_info,
            "formatted_list": formatted_requirements,
            "total_count": requirements_info["total_requirements"],
            "message": f"Found {requirements_info['total_requirements']} requirements for {license_type} {procedure_type}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting requirements: {str(e)}"
        }


def validate_age_requirements(license_type: str, birth_date: str, tool_context: ToolContext):
    """
    Validate age requirements for specific license type.
    
    Args:
        tool_context: Tool context for state access
        license_type: Type of license to validate age for
        birth_date: Birth date in YYYY-MM-DD format
        
    Returns:
        Dict with age validation results
    """
    try:
        validation_result = _validate_age_requirements(license_type, birth_date)
        
        # Store validation in state
        tool_context.state["age_validation"] = {
            **validation_result,
            "validated_at": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "validation": validation_result,
            "message": validation_result.get("message", "Age validation completed")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error validating age: {str(e)}"
        }