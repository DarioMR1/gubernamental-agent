# Copyright 2024 SEMOVI Multiagent System

"""Tools for finding and managing SEMOVI office locations."""

import math
from datetime import datetime

from google.adk.tools.tool_context import ToolContext
from .supabase_connection import execute_supabase_query


def find_nearby_offices(postal_code: str, tool_context: ToolContext):
    """
    Find SEMOVI offices near the given postal code using Supabase.
    
    Args:
        tool_context: Context for accessing session state
        postal_code: 5-digit postal code to search around
        
    Returns:
        Dict with found offices and their details
    """
    try:
        # Validate postal code format
        if not postal_code or not postal_code.isdigit() or len(postal_code) != 5:
            return {
                "status": "error",
                "message": "Postal code must be a 5-digit number"
            }
        
        # Query offices from Supabase, ordered by proximity to postal code
        query_result = execute_supabase_query(
            tool_context,
            endpoint="offices?select=*&is_active=eq.true&order=postal_code",
            method="GET"
        )
        
        if query_result["status"] != "success":
            return {
                "status": "error",
                "message": f"Failed to query offices: {query_result.get('message', 'Unknown error')}"
            }
        
        all_offices = query_result["data"]
        
        if not all_offices:
            return {
                "status": "not_found",
                "message": f"No SEMOVI offices found. Please contact support.",
                "searched_postal_code": postal_code
            }
        
        # Calculate distances and sort by proximity
        user_postal = int(postal_code)
        offices_with_distance = []
        
        for office in all_offices:
            office_postal = int(office["postal_code"])
            # Simple distance calculation based on postal code difference
            distance_km = abs(user_postal - office_postal) / 1000 + 2.0
            
            office["distance_km"] = round(distance_km, 1)
            offices_with_distance.append(office)
        
        # Sort by distance and take top 5
        sorted_offices = sorted(offices_with_distance, key=lambda x: x["distance_km"])[:5]
        
        # Process and enrich office information
        enriched_offices = []
        for office in sorted_offices:
            enriched_office = _enrich_office_information(office, postal_code)
            enriched_offices.append(enriched_office)
        
        # Store search results in session state
        tool_context.state["office_search"] = {
            "search_postal_code": postal_code,
            "found_offices": enriched_offices,
            "search_timestamp": datetime.now().isoformat(),
            "total_found": len(enriched_offices)
        }
        tool_context.state["process_stage"] = "offices_found"
        
        return {
            "status": "success",
            "offices": enriched_offices,
            "search_postal_code": postal_code,
            "total_found": len(enriched_offices),
            "message": f"Found {len(enriched_offices)} SEMOVI offices near postal code {postal_code}"
        }
        
    except Exception as e:
        tool_context.state["last_error"] = {
            "tool": "find_nearby_offices",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "status": "error",
            "message": f"Error finding offices: {str(e)}"
        }


def _enrich_office_information(office: dict, user_postal_code):
    """Enrich office information with additional details and formatting."""
    
    # Calculate approximate distance (simplified)
    distance_km = office.get("distance_km", 0.0)
    
    # Format operating hours for display
    hours = office.get("operating_hours", {})
    formatted_hours = _format_operating_hours(hours)
    
    # Determine if office is currently open
    is_open = _is_office_currently_open(hours)
    
    return {
        "id": office["id"],
        "name": office["name"],
        "address": office["address"],
        "postal_code": office["postal_code"],
        "distance_km": round(distance_km, 1),
        "contact": {
            "phone": office.get("phone", ""),
            "email": office.get("email", "")
        },
        "operating_hours": hours,
        "formatted_hours": formatted_hours,
        "is_currently_open": is_open,
        "services_available": office.get("services_available", True),
        "accessibility": {
            "wheelchair_accessible": True,  # Assume all government offices are accessible
            "public_transport": True
        }
    }


def _format_operating_hours(hours):
    """Format operating hours for user-friendly display."""
    if not hours:
        return "Hours not available"
    
    # Check if all weekdays have the same hours
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    weekday_hours = []
    
    for day in weekdays:
        day_info = hours.get(day, {})
        if day_info.get("closed"):
            continue
        start = day_info.get("start", "")
        end = day_info.get("end", "")
        if start and end:
            weekday_hours.append(f"{start}-{end}")
    
    # If all weekdays have same hours, show simplified format
    if weekday_hours and all(h == weekday_hours[0] for h in weekday_hours):
        time_range = weekday_hours[0]
        weekend_info = ""
        
        saturday = hours.get("saturday", {})
        sunday = hours.get("sunday", {})
        
        if saturday.get("closed") and sunday.get("closed"):
            weekend_info = " (Closed weekends)"
        
        return f"Monday-Friday {time_range}{weekend_info}"
    
    # Otherwise, show detailed format
    formatted_days = []
    for day, day_info in hours.items():
        if day_info.get("closed"):
            formatted_days.append(f"{day.capitalize()}: Closed")
        else:
            start = day_info.get("start", "")
            end = day_info.get("end", "")
            if start and end:
                formatted_days.append(f"{day.capitalize()}: {start}-{end}")
    
    return ", ".join(formatted_days) if formatted_days else "Hours not available"


def _is_office_currently_open(hours):
    """Check if office is currently open based on operating hours."""
    if not hours:
        return False
    
    now = datetime.now()
    current_day = now.strftime("%A").lower()
    current_time = now.time()
    
    day_hours = hours.get(current_day, {})
    
    if day_hours.get("closed"):
        return False
    
    start_time_str = day_hours.get("start")
    end_time_str = day_hours.get("end")
    
    if not start_time_str or not end_time_str:
        return False
    
    try:
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
        
        return start_time <= current_time <= end_time
    except:
        return False


def calculate_distance(postal_code_1: str, postal_code_2: str, tool_context: ToolContext):
    """
    Calculate approximate distance between two postal codes.
    
    Args:
        tool_context: Tool context for state access
        postal_code_1: First postal code
        postal_code_2: Second postal code
        
    Returns:
        Dict with distance calculation
    """
    try:
        # Simple distance calculation based on postal code difference
        # In production, use proper geocoding and distance calculation
        pc1 = int(postal_code_1)
        pc2 = int(postal_code_2)
        
        # Approximate calculation: postal code difference to km
        postal_diff = abs(pc1 - pc2)
        estimated_km = (postal_diff / 1000) + 2.0  # Base 2km + proportional distance
        
        return {
            "status": "success",
            "distance_km": round(estimated_km, 1),
            "from_postal": postal_code_1,
            "to_postal": postal_code_2,
            "calculation_method": "estimated",
            "message": f"Estimated distance: {round(estimated_km, 1)} km"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error calculating distance: {str(e)}"
        }


def verify_office_services(
    office_id: int, 
    license_type: str, 
    procedure_type: str,
    tool_context: ToolContext
):
    """
    Verify that an office provides the specific service needed.
    
    Args:
        tool_context: Tool context for state access
        office_id: ID of the office to verify
        license_type: Type of license needed
        procedure_type: Type of procedure needed
        
    Returns:
        Dict with service availability verification
    """
    try:
        # For this implementation, all SEMOVI offices provide all services
        # In production, check office_services table in database
        
        office_search = tool_context.state.get("office_search", {})
        found_offices = office_search.get("found_offices", [])
        
        # Find the specific office
        target_office = None
        for office in found_offices:
            if office["id"] == office_id:
                target_office = office
                break
        
        if not target_office:
            return {
                "status": "not_found",
                "message": f"Office with ID {office_id} not found in search results"
            }
        
        # Check service availability
        services_available = target_office.get("services_available", True)
        
        if services_available:
            return {
                "status": "available",
                "office_id": office_id,
                "office_name": target_office["name"],
                "license_type": license_type,
                "procedure_type": procedure_type,
                "message": f"{target_office['name']} provides {license_type} {procedure_type} service",
                "estimated_wait_time": "30-45 minutes",
                "appointment_required": True
            }
        else:
            return {
                "status": "unavailable",
                "office_id": office_id,
                "office_name": target_office["name"],
                "message": f"{target_office['name']} does not currently provide {license_type} {procedure_type} service",
                "alternative_offices": _suggest_alternative_offices(found_offices, license_type, procedure_type)
            }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error verifying office services: {str(e)}"
        }


def _suggest_alternative_offices(offices: list, license_type, procedure_type):
    """Suggest alternative offices that provide the required service."""
    alternatives = []
    
    for office in offices[:3]:  # Suggest top 3 alternatives
        if office.get("services_available", True):
            alternatives.append({
                "id": office["id"],
                "name": office["name"],
                "distance_km": office.get("distance_km", 0),
                "address": office["address"]
            })
    
    return alternatives


def get_office_details(office_id: int, tool_context: ToolContext):
    """
    Get detailed information about a specific office.
    
    Args:
        tool_context: Tool context for state access
        office_id: ID of the office to get details for
        
    Returns:
        Dict with detailed office information
    """
    try:
        office_search = tool_context.state.get("office_search", {})
        found_offices = office_search.get("found_offices", [])
        
        # Find the specific office
        target_office = None
        for office in found_offices:
            if office["id"] == office_id:
                target_office = office
                break
        
        if not target_office:
            return {
                "status": "not_found", 
                "message": f"Office with ID {office_id} not found"
            }
        
        # Get additional details
        details = {
            **target_office,
            "directions": _get_directions_info(target_office),
            "parking": _get_parking_info(target_office),
            "public_transport": _get_public_transport_info(target_office),
            "amenities": _get_amenities_info(target_office)
        }
        
        return {
            "status": "success",
            "office_details": details,
            "message": f"Retrieved details for {target_office['name']}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting office details: {str(e)}"
        }


def _get_directions_info(office: dict):
    """Get directions information for the office."""
    return {
        "address": office["address"],
        "google_maps_link": f"https://maps.google.com/search/{office['address'].replace(' ', '+')}",
        "metro_stations_nearby": ["Centro Historico", "Allende", "Zocalo"],  # Mock data
        "bus_routes": ["1", "2", "4", "17", "76"]  # Mock data
    }


def _get_parking_info(office: dict):
    """Get parking information for the office."""
    return {
        "parking_available": True,
        "parking_cost": "Free for first 2 hours",
        "parking_spaces": 50,
        "accessibility_parking": True
    }


def _get_public_transport_info(office: dict):
    """Get public transport information for the office."""
    return {
        "metro_distance": "300 meters",
        "bus_stops": ["Main Street", "Central Plaza"],
        "accessibility": "Wheelchair accessible",
        "metrobus_nearby": True
    }


def _get_amenities_info(office: dict):
    """Get amenities information for the office."""
    return {
        "wheelchair_accessible": True,
        "waiting_area": True,
        "restrooms": True,
        "water_fountain": True,
        "wifi_available": False,
        "air_conditioning": True,
        "document_printing": True
    }