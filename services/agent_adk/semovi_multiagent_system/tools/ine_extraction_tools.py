# Copyright 2024 SEMOVI Multiagent System

"""Tools for INE document extraction using Gemini Flash multimodal capabilities."""

import base64
import re
import json
from datetime import datetime

from google.adk.tools.tool_context import ToolContext


def extract_ine_data_with_vision(tool_context: ToolContext, extracted_data: dict):
    """
    Process and store INE data extracted by the agent's vision capabilities.
    
    Args:
        tool_context: Context for accessing session state
        extracted_data: Dictionary containing extracted INE information
        
    Returns:
        Dict containing processing results
    """
    try:
        # Clean and validate extracted data
        cleaned_data = _clean_extracted_data(extracted_data)
        
        # Validate extracted data
        validation_result = _validate_extracted_data(cleaned_data)
        
        if validation_result["is_valid"]:
            # Store in session state
            tool_context.state["user_data"] = {
                **cleaned_data,
                "extraction_timestamp": datetime.now().isoformat(),
                "extraction_method": "gemini_flash"
            }
            tool_context.state["process_stage"] = "ine_extracted"
            
            return {
                "status": "success",
                "message": "Datos del INE procesados y almacenados exitosamente",
                "extracted_data": cleaned_data,
                "confidence_score": validation_result["confidence"],
                "fields_extracted": [k for k, v in cleaned_data.items() if v and v.strip()]
            }
        else:
            return {
                "status": "partial_success",
                "message": "Algunos datos extraídos requieren validación",
                "extracted_data": cleaned_data,
                "missing_fields": validation_result["missing_fields"],
                "validation_errors": validation_result["errors"]
            }
            
    except Exception as e:
        # Log error to session state
        tool_context.state["last_error"] = {
            "tool": "extract_ine_data_with_vision",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "status": "error",
            "message": f"Error procesando datos del INE: {str(e)}"
        }


def _clean_extracted_data(raw_data: dict):
    """
    Clean and normalize extracted data from Gemini response.
    
    Args:
        raw_data: Raw extracted data from Gemini
        
    Returns:
        Cleaned and normalized data
    """
    cleaned = {
        "full_name": "",
        "curp": "",
        "address": "",
        "postal_code": "",
        "birth_date": ""
    }
    
    for key in cleaned.keys():
        if key in raw_data and raw_data[key]:
            value = str(raw_data[key]).strip().upper()
            
            # Special cleaning for each field
            if key == "full_name":
                # Remove extra spaces and ensure proper format
                value = " ".join(value.split())
            elif key == "curp":
                # Ensure CURP is uppercase and alphanumeric
                value = "".join(c for c in value if c.isalnum()).upper()
            elif key == "address":
                # Keep address formatting but clean extra spaces
                value = " ".join(value.split())
            elif key == "postal_code":
                # Ensure postal code is numeric
                value = "".join(c for c in value if c.isdigit())
            elif key == "birth_date":
                # Validate date format
                value = value.lower()
                if len(value) == 10 and value.count('-') == 2:
                    try:
                        # Validate date can be parsed
                        datetime.strptime(value, "%Y-%m-%d")
                    except:
                        value = ""
            
            cleaned[key] = value
    
    return cleaned


def _extract_ine_fields(text):
    """
    Extract specific fields from INE text using pattern matching.
    
    Args:
        text: Full text extracted from INE
        
    Returns:
        Dict with extracted fields
    """
    extracted = {
        "full_name": "",
        "curp": "",
        "address": "",
        "postal_code": "",
        "birth_date": ""
    }
    
    # Clean text for better matching
    text = text.upper().replace('\n', ' ').replace('\r', ' ')
    
    # Extract CURP (18 character alphanumeric code)
    curp_pattern = r'\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]{2}\b'
    curp_match = re.search(curp_pattern, text)
    if curp_match:
        extracted["curp"] = curp_match.group()
    
    # Extract birth date from CURP if found
    if extracted["curp"]:
        curp = extracted["curp"]
        year_str = curp[4:6]
        month_str = curp[6:8]
        day_str = curp[8:10]
        
        # Determine century (assume 20th century for years > 30, 21st for <= 30)
        year = int(year_str)
        if year > 30:
            year += 1900
        else:
            year += 2000
            
        extracted["birth_date"] = f"{year}-{month_str}-{day_str}"
    
    # Extract postal code (5 digits)
    postal_pattern = r'\b\d{5}\b'
    postal_matches = re.findall(postal_pattern, text)
    if postal_matches:
        # Take the first 5-digit number that's not part of CURP
        for postal in postal_matches:
            if postal not in extracted["curp"]:
                extracted["postal_code"] = postal
                break
    
    # Extract name (appears after "NOMBRE" or similar keywords)
    name_patterns = [
        r'NOMBRE[:\s]+([A-Z\s]+?)(?:DOMICILIO|DIRECCION|CURP|$)',
        r'APELLIDOS[:\s]+([A-Z\s]+?)(?:NOMBRE|DOMICILIO|$)',
    ]
    
    name_parts = []
    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            name_part = match.group(1).strip()
            if name_part and len(name_part) > 2:
                name_parts.append(name_part)
    
    if name_parts:
        extracted["full_name"] = " ".join(name_parts[:2])  # First two parts
    
    # Extract address (appears after "DOMICILIO" or "DIRECCION")
    address_patterns = [
        r'DOMICILIO[:\s]+([A-Z0-9\s,\.]+?)(?:EDAD|CLAVE|CURP|ESTADO|$)',
        r'DIRECCION[:\s]+([A-Z0-9\s,\.]+?)(?:EDAD|CLAVE|CURP|ESTADO|$)',
    ]
    
    for pattern in address_patterns:
        match = re.search(pattern, text)
        if match:
            address = match.group(1).strip()
            if address and len(address) > 10:
                extracted["address"] = address[:100]  # Limit length
                break
    
    return extracted


def _validate_extracted_data(data: dict):
    """
    Validate extracted INE data for completeness and format.
    
    Args:
        data: Extracted data dictionary
        
    Returns:
        Dict with validation results
    """
    required_fields = ["full_name", "curp", "postal_code"]
    missing_fields = []
    errors = []
    
    # Check required fields
    for field in required_fields:
        if not data.get(field, "").strip():
            missing_fields.append(field)
    
    # Validate CURP format
    if data.get("curp"):
        curp = data["curp"]
        if len(curp) != 18:
            errors.append("CURP must be 18 characters long")
        elif not re.match(r'^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]{2}$', curp):
            errors.append("CURP format is invalid")
    
    # Validate postal code
    if data.get("postal_code"):
        postal = data["postal_code"]
        if not re.match(r'^\d{5}$', postal):
            errors.append("Postal code must be 5 digits")
    
    # Validate name
    if data.get("full_name"):
        name = data["full_name"]
        if len(name) < 5:
            errors.append("Name seems too short")
        elif not re.match(r'^[A-Z\s]+$', name):
            errors.append("Name contains invalid characters")
    
    # Calculate confidence score
    total_fields = len(required_fields) + 2  # +2 for optional fields
    filled_fields = sum(1 for field in data.values() if field.strip())
    confidence = min(filled_fields / total_fields, 1.0) if total_fields > 0 else 0.0
    
    # Reduce confidence for errors
    if errors:
        confidence *= 0.7
    
    is_valid = len(missing_fields) == 0 and len(errors) == 0
    
    return {
        "is_valid": is_valid,
        "confidence": round(confidence, 2),
        "missing_fields": missing_fields,
        "errors": errors,
        "total_fields": total_fields,
        "filled_fields": filled_fields
    }


def validate_extracted_data(tool_context: ToolContext, extracted_data: dict):
    """
    Standalone validation tool for extracted INE data.
    
    Args:
        tool_context: Tool context for state access
        extracted_data: Dictionary with extracted INE data
        
    Returns:
        Dict with validation results
    """
    try:
        validation_result = _validate_extracted_data(extracted_data)
        
        # Update session state with validation info
        tool_context.state["validation_results"] = validation_result
        
        return {
            "status": "success",
            "validation": validation_result,
            "message": "Validation completed successfully"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Validation error: {str(e)}"
        }


def request_missing_information(tool_context: ToolContext, missing_fields: list[str]):
    """
    Request missing information from user when extraction is incomplete.
    
    Args:
        tool_context: Tool context for state access
        missing_fields: List of missing field names
        
    Returns:
        Dict with request information
    """
    field_descriptions = {
        "full_name": "your full name as it appears on your INE",
        "curp": "your CURP (18-character code)",
        "address": "your complete address",
        "postal_code": "your 5-digit postal code",
        "birth_date": "your birth date (YYYY-MM-DD)"
    }
    
    request_messages = []
    for field in missing_fields:
        description = field_descriptions.get(field, field)
        request_messages.append(f"- Please provide {description}")
    
    # Store missing information request in state
    tool_context.state["missing_info_request"] = {
        "fields": missing_fields,
        "timestamp": datetime.now().isoformat(),
        "status": "pending"
    }
    
    return {
        "status": "info_required",
        "missing_fields": missing_fields,
        "message": "I need some additional information to complete your profile:\n" + 
                  "\n".join(request_messages) + 
                  "\n\nPlease provide this information or try uploading a clearer image of your INE."
    }