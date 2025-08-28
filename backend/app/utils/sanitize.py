"""
ASCII-only text sanitization utilities.

This module provides functions to ensure all text content contains only ASCII characters,
replacing em dashes, en dashes, smart quotes, and removing emojis.
"""

import re
import unicodedata
from typing import Any, Dict, List, Union


def sanitize_text(text: str) -> str:
    """
    Sanitize text to contain only ASCII characters.
    
    Replaces:
    - Em dashes (U+2014) and en dashes (U+2013) with " - "
    - Smart quotes with straight quotes
    - Removes emojis and any non-ASCII characters
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized ASCII-only text
    """
    if not isinstance(text, str):
        return str(text)
    
    # Replace em dashes and en dashes with " - "
    text = text.replace('\u2014', ' - ')  # em dash
    text = text.replace('\u2013', ' - ')  # en dash
    
    # Replace smart quotes with straight quotes
    text = text.replace('\u201c', '"')  # left double quotation mark
    text = text.replace('\u201d', '"')  # right double quotation mark
    text = text.replace('\u2018', "'")  # left single quotation mark
    text = text.replace('\u2019', "'")  # right single quotation mark
    
    # Remove emojis and other non-ASCII characters
    # Keep only printable ASCII characters (32-126)
    sanitized = ''
    for char in text:
        if ord(char) < 128 and char.isprintable():
            sanitized += char
        elif char.isspace():
            sanitized += ' '  # Replace non-ASCII whitespace with space
    
    # Clean up multiple spaces
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def sanitize_dict(obj: Any) -> Any:
    """
    Recursively sanitize all string values in a dictionary or other data structure.
    
    Args:
        obj: Object to sanitize (dict, list, str, or other)
        
    Returns:
        Sanitized object with ASCII-only string values
    """
    if isinstance(obj, dict):
        return {key: sanitize_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_dict(item) for item in obj]
    elif isinstance(obj, str):
        return sanitize_text(obj)
    else:
        return obj


def validate_ascii_only(text: str) -> bool:
    """
    Validate that text contains only ASCII characters.
    
    Args:
        text: Text to validate
        
    Returns:
        True if text is ASCII-only, False otherwise
    """
    try:
        text.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False


def find_non_ascii_chars(text: str) -> List[str]:
    """
    Find all non-ASCII characters in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of non-ASCII characters found
    """
    non_ascii = []
    for char in text:
        if ord(char) >= 128:
            non_ascii.append(char)
    return non_ascii


# Blocked character patterns for pre-commit hooks
BLOCKED_PATTERNS = [
    r'\xE2\x80\x94',  # em dash
    r'\xE2\x80\x93',  # en dash
    r'[\xF0\x9F\x80-\xF0\x9F\xBF]',  # emoji range 1
    r'[\xF0\x9F\x8C-\xF0\x9F\xA6]',  # emoji range 2
    r'[\xF0\x9F\xAA-\xF0\x9F\xBF]',  # emoji range 3
]


def check_blocked_patterns(text: str) -> List[str]:
    """
    Check for blocked character patterns in text.
    
    Args:
        text: Text to check
        
    Returns:
        List of blocked patterns found
    """
    found_patterns = []
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, text):
            found_patterns.append(pattern)
    return found_patterns
