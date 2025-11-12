"""Validation utilities for the governmental agent."""

import re
import urllib.parse
from typing import Optional
from pathlib import Path


def validate_url(url: str) -> bool:
    """Validate if a string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_css_selector(selector: str) -> bool:
    """Validate if a string is a valid CSS selector.
    
    Args:
        selector: CSS selector string to validate
        
    Returns:
        True if selector appears valid, False otherwise
    """
    if not selector or not isinstance(selector, str):
        return False
    
    # Basic validation - check for common patterns
    # This is a simplified validation, real CSS selector validation is complex
    invalid_chars = ["<", ">", "{", "}", "@"]
    if any(char in selector for char in invalid_chars):
        return False
    
    # Must not be just whitespace
    if selector.strip() == "":
        return False
    
    # Some basic patterns that should be valid
    valid_patterns = [
        r'^[#.]?[\w-]+$',  # Simple class/id/tag selectors
        r'^[\w-]+\[[\w-]+(=["\']?[\w-]+["\']?)?\]$',  # Attribute selectors
        r'^[\w-]+\s+[\w-]+$',  # Descendant selectors
        r'^[\w-]+\s*>\s*[\w-]+$',  # Child selectors
    ]
    
    # If it matches any basic pattern, consider it valid
    # For more complex selectors, we'll trust the user/LLM
    if any(re.match(pattern, selector.strip()) for pattern in valid_patterns):
        return True
    
    # For complex selectors, do a basic sanity check
    if len(selector) > 500:  # Arbitrarily long selectors are suspicious
        return False
    
    # If brackets/quotes are balanced, likely valid
    if selector.count("(") == selector.count(")") and \
       selector.count("[") == selector.count("]") and \
       selector.count('"') % 2 == 0 and \
       selector.count("'") % 2 == 0:
        return True
    
    return False


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize a filename for safe file system usage.
    
    Args:
        filename: Original filename
        max_length: Maximum allowed filename length
        
    Returns:
        Sanitized filename safe for file system usage
    """
    if not filename:
        return "unnamed_file"
    
    # Remove or replace invalid characters
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    
    # Replace multiple underscores with single underscore
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure it's not empty after cleaning
    if not filename:
        filename = "unnamed_file"
    
    # Truncate if too long, but preserve extension
    if len(filename) > max_length:
        path = Path(filename)
        name = path.stem
        ext = path.suffix
        
        # Calculate how much space we have for the name
        max_name_length = max_length - len(ext)
        
        if max_name_length > 0:
            filename = name[:max_name_length] + ext
        else:
            # Extension is too long, just truncate everything
            filename = filename[:max_length]
    
    return filename


def validate_ruc(ruc: str) -> bool:
    """Validate Peruvian RUC (Registro Único de Contribuyentes).
    
    Args:
        ruc: RUC string to validate
        
    Returns:
        True if RUC is valid, False otherwise
    """
    if not ruc or not isinstance(ruc, str):
        return False
    
    # Remove any spaces or separators
    ruc = re.sub(r'[^0-9]', '', ruc)
    
    # RUC must be exactly 11 digits
    if len(ruc) != 11:
        return False
    
    # Must be all digits
    if not ruc.isdigit():
        return False
    
    # Basic validation based on first two digits
    # 10: Natural persons
    # 15: Non-resident natural persons  
    # 17: Non-resident legal entities
    # 20: Legal entities
    valid_prefixes = ["10", "15", "17", "20"]
    if not any(ruc.startswith(prefix) for prefix in valid_prefixes):
        return False
    
    return True


def validate_dni(dni: str) -> bool:
    """Validate Peruvian DNI (Documento Nacional de Identidad).
    
    Args:
        dni: DNI string to validate
        
    Returns:
        True if DNI is valid, False otherwise
    """
    if not dni or not isinstance(dni, str):
        return False
    
    # Remove any spaces or separators
    dni = re.sub(r'[^0-9]', '', dni)
    
    # DNI must be exactly 8 digits
    if len(dni) != 8:
        return False
    
    # Must be all digits
    if not dni.isdigit():
        return False
    
    # Cannot be all the same digit
    if len(set(dni)) == 1:
        return False
    
    return True


def validate_email(email: str) -> bool:
    """Validate email address format.
    
    Args:
        email: Email string to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return bool(re.match(pattern, email.strip()))


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format (flexible for international formats).
    
    Args:
        phone: Phone number string to validate
        
    Returns:
        True if phone number appears valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove common separators and spaces
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Must be digits only after cleaning
    if not cleaned.isdigit():
        return False
    
    # Reasonable length range for phone numbers
    if len(cleaned) < 7 or len(cleaned) > 15:
        return False
    
    return True