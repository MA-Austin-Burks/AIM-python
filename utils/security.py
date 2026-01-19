"""Security utilities for input validation and sanitization."""

from typing import Any, Callable


# Maximum length for search input to prevent DoS attacks
MAX_SEARCH_INPUT_LENGTH = 500


def validate_search_input(search_text: str | None) -> str | None:
    """Validate and sanitize search input.
    
    Args:
        search_text: Raw search input from user
        
    Returns:
        Sanitized search text (trimmed, length-limited) or None if invalid
        
    Raises:
        ValueError: If input exceeds maximum length
    """
    if not search_text:
        return None
    
    # Strip whitespace
    sanitized = search_text.strip()
    
    # Check length limit
    if len(sanitized) > MAX_SEARCH_INPUT_LENGTH:
        raise ValueError(
            f"Search input exceeds maximum length of {MAX_SEARCH_INPUT_LENGTH} characters"
        )
    
    return sanitized if sanitized else None


def sanitize_url_for_logging(url: str, max_length: int = 50) -> str:
    """Sanitize URL for logging to prevent exposing sensitive tokens.
    
    Only shows the domain and path, not query parameters or fragments.
    
    Args:
        url: Full URL that may contain sensitive tokens
        max_length: Maximum length of sanitized URL to show
        
    Returns:
        Sanitized URL safe for logging
    """
    try:
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        # Only show scheme, netloc, and path - exclude query and fragment
        safe_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        if len(safe_url) > max_length:
            return safe_url[:max_length] + "..."
        return safe_url
    except Exception:
        # If parsing fails, return a generic message
        return "[URL parsing failed]"


def validate_session_state_value(
    key: str, 
    value: Any, 
    expected_type: type | tuple[type, ...],
    validator: Callable[[Any], bool] | None = None
) -> bool:
    """Validate a session state value.
    
    Args:
        key: Session state key name
        value: Value to validate
        expected_type: Expected type(s) for the value
        validator: Optional custom validation function
        
    Returns:
        True if value is valid, False otherwise
    """
    # Check type
    if not isinstance(value, expected_type):
        return False
    
    # Run custom validator if provided
    if validator is not None:
        try:
            return validator(value)
        except Exception:
            return False
    
    return True
