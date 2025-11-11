"""Formatting utilities for the governmental agent."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import ActionResult, ExecutionSummary


def format_execution_summary(results: List[ActionResult]) -> str:
    """Format execution results into a human-readable summary.
    
    Args:
        results: List of action results
        
    Returns:
        Formatted summary string
    """
    if not results:
        return "No actions executed."
    
    total_actions = len(results)
    successful_actions = sum(1 for result in results if result.success)
    failed_actions = total_actions - successful_actions
    
    total_time = sum(result.execution_time for result in results)
    success_rate = (successful_actions / total_actions) * 100
    
    summary = f"""Execution Summary:
================
Total Actions: {total_actions}
Successful: {successful_actions}
Failed: {failed_actions}
Success Rate: {success_rate:.1f}%
Total Time: {format_duration(total_time)}

"""
    
    if failed_actions > 0:
        summary += "Failed Actions:\n"
        for result in results:
            if not result.success:
                summary += f"- {result.action_id}: {result.error_message}\n"
        summary += "\n"
    
    if any(result.data_extracted for result in results):
        summary += "Data Extracted:\n"
        for result in results:
            if result.data_extracted:
                summary += f"- {result.action_id}: {len(result.data_extracted)} items\n"
    
    return summary


def format_error_report(error: Exception, context: Dict[str, Any]) -> str:
    """Format an error into a detailed report.
    
    Args:
        error: Exception that occurred
        context: Additional context information
        
    Returns:
        Formatted error report
    """
    report = f"""Error Report:
============
Error Type: {type(error).__name__}
Error Message: {str(error)}
Timestamp: {datetime.now().isoformat()}

Context:
"""
    
    for key, value in context.items():
        if key == "stack_trace":
            continue  # Handle stack trace separately
        
        if isinstance(value, dict):
            report += f"- {key}: {json.dumps(value, indent=2)}\n"
        else:
            report += f"- {key}: {value}\n"
    
    if "stack_trace" in context and context["stack_trace"]:
        report += f"\nStack Trace:\n{context['stack_trace']}"
    
    return report


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Human-readable duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.0f}s"
    else:
        hours = int(seconds // 3600)
        remaining_seconds = seconds % 3600
        minutes = int(remaining_seconds // 60)
        remaining_seconds = remaining_seconds % 60
        return f"{hours}h {minutes}m {remaining_seconds:.0f}s"


def format_timestamp(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format timestamp to string.
    
    Args:
        dt: Datetime object. If None, uses current time
        format_str: Format string for strftime
        
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    
    return dt.strftime(format_str)


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def format_progress_bar(
    current: int, 
    total: int, 
    width: int = 50, 
    fill: str = "█", 
    empty: str = "░"
) -> str:
    """Create a text progress bar.
    
    Args:
        current: Current progress value
        total: Total progress value
        width: Width of progress bar in characters
        fill: Character for filled portion
        empty: Character for empty portion
        
    Returns:
        Formatted progress bar string
    """
    if total == 0:
        percentage = 100
        filled_width = width
    else:
        percentage = min(100, (current / total) * 100)
        filled_width = int(width * current // total)
    
    bar = fill * filled_width + empty * (width - filled_width)
    return f"[{bar}] {percentage:.1f}% ({current}/{total})"


def format_table(
    data: List[Dict[str, Any]], 
    headers: Optional[List[str]] = None,
    max_width: int = 80
) -> str:
    """Format data as a simple text table.
    
    Args:
        data: List of dictionaries representing rows
        headers: List of column headers. If None, uses keys from first row
        max_width: Maximum width for each column
        
    Returns:
        Formatted table string
    """
    if not data:
        return "No data to display."
    
    if headers is None:
        headers = list(data[0].keys())
    
    # Calculate column widths
    col_widths = {}
    for header in headers:
        col_widths[header] = len(header)
        
        for row in data:
            value = str(row.get(header, ""))
            col_widths[header] = max(col_widths[header], len(value))
        
        # Limit column width
        col_widths[header] = min(col_widths[header], max_width)
    
    # Create table
    lines = []
    
    # Header
    header_line = " | ".join(h.ljust(col_widths[h]) for h in headers)
    lines.append(header_line)
    lines.append("-" * len(header_line))
    
    # Data rows
    for row in data:
        row_line = " | ".join(
            str(row.get(h, "")).ljust(col_widths[h])[:col_widths[h]] 
            for h in headers
        )
        lines.append(row_line)
    
    return "\n".join(lines)


def format_json_pretty(data: Any, indent: int = 2) -> str:
    """Format data as pretty-printed JSON.
    
    Args:
        data: Data to format
        indent: Indentation level
        
    Returns:
        Pretty-printed JSON string
    """
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    except TypeError as e:
        return f"Error formatting JSON: {e}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_execution_log(
    session_id: str,
    action_id: str,
    action_type: str,
    status: str,
    duration: float,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format execution log entry.
    
    Args:
        session_id: Session identifier
        action_id: Action identifier
        action_type: Type of action
        status: Execution status
        duration: Execution duration in seconds
        details: Additional details
        
    Returns:
        Formatted log entry
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "action_id": action_id,
        "action_type": action_type,
        "status": status,
        "duration_ms": round(duration * 1000),
        "duration_human": format_duration(duration)
    }
    
    if details:
        log_entry["details"] = details
    
    return log_entry