"""
Input sanitization utilities for EchoNote.

Phase 4: Security Hardening - Input sanitization to prevent XSS and injection attacks

This module provides utilities to sanitize user input:
- Text input sanitization (HTML cleaning)
- Filename sanitization (path traversal prevention)
"""

import os
import re
from typing import Optional
import bleach


# Allowed HTML tags for text input (very restrictive)
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'b', 'i',
    'ul', 'ol', 'li', 'a', 'code', 'pre'
]

# Allowed HTML attributes
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'code': ['class'],
}

# Allowed URL protocols
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_text_input(text: str, strip_all_html: bool = False) -> str:
    """
    Sanitize text input to prevent XSS attacks.

    By default, allows safe HTML tags (p, br, strong, em, etc.).
    Can optionally strip all HTML tags completely.

    Args:
        text: The text to sanitize
        strip_all_html: If True, removes all HTML tags. If False, allows safe tags.

    Returns:
        Sanitized text string

    Examples:
        >>> sanitize_text_input("<script>alert('xss')</script>Hello")
        "Hello"

        >>> sanitize_text_input("<p>Hello <strong>world</strong></p>")
        "<p>Hello <strong>world</strong></p>"

        >>> sanitize_text_input("<p>Hello</p>", strip_all_html=True)
        "Hello"
    """
    if not text:
        return ""

    if strip_all_html:
        # Strip all HTML tags
        return bleach.clean(text, tags=[], strip=True)
    else:
        # Allow safe HTML tags only
        return bleach.clean(
            text,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True
        )


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to prevent path traversal attacks and filesystem issues.

    This function:
    - Removes path separators (/ and \\)
    - Removes null bytes
    - Removes leading/trailing dots and spaces
    - Limits length to prevent filesystem issues
    - Ensures only safe characters are used

    Args:
        filename: The filename to sanitize
        max_length: Maximum allowed filename length (default: 255)

    Returns:
        Sanitized filename string

    Raises:
        ValueError: If filename is empty after sanitization

    Examples:
        >>> sanitize_filename("../../../etc/passwd")
        "etcpasswd"

        >>> sanitize_filename("test file.txt")
        "test_file.txt"

        >>> sanitize_filename("file\x00.txt")
        "file.txt"
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    # Remove null bytes
    filename = filename.replace('\x00', '')

    # Get just the filename (remove any path components)
    filename = os.path.basename(filename)

    # Remove or replace dangerous characters
    # Allow: alphanumeric, dash, underscore, dot
    filename = re.sub(r'[^\w\-.]', '_', filename)

    # Remove leading/trailing dots and underscores (security risk)
    filename = filename.strip('._')

    # Limit length
    if len(filename) > max_length:
        # Try to preserve extension
        name, ext = os.path.splitext(filename)
        if ext:
            max_name_length = max_length - len(ext)
            filename = name[:max_name_length] + ext
        else:
            filename = filename[:max_length]

    # Ensure filename is not empty after sanitization
    if not filename:
        raise ValueError("Filename is invalid after sanitization")

    return filename


def sanitize_url(url: str) -> Optional[str]:
    """
    Sanitize URL to ensure it uses safe protocols.

    Only allows http:// and https:// protocols.
    Rejects javascript:, data:, file:, and other dangerous protocols.

    Args:
        url: The URL to sanitize

    Returns:
        Sanitized URL if valid, None if invalid

    Examples:
        >>> sanitize_url("https://example.com")
        "https://example.com"

        >>> sanitize_url("javascript:alert('xss')")
        None

        >>> sanitize_url("data:text/html,<script>alert('xss')</script>")
        None
    """
    if not url:
        return None

    # Remove whitespace
    url = url.strip()

    # Check protocol
    url_lower = url.lower()
    if url_lower.startswith(('http://', 'https://')):
        return url
    else:
        # Reject URLs with dangerous protocols or no protocol
        return None


def sanitize_username(username: str) -> str:
    """
    Sanitize username to ensure only safe characters.

    Allows: letters, numbers, hyphens, and underscores.
    This matches the validation in UserCreate model.

    Args:
        username: The username to sanitize

    Returns:
        Sanitized username

    Raises:
        ValueError: If username contains invalid characters

    Examples:
        >>> sanitize_username("user_name-123")
        "user_name-123"

        >>> sanitize_username("user@example")
        ValueError: Username contains invalid characters
    """
    if not username:
        raise ValueError("Username cannot be empty")

    # Check if username contains only allowed characters
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise ValueError("Username contains invalid characters")

    return username


def sanitize_email(email: str) -> str:
    """
    Sanitize email address.

    Converts to lowercase and validates basic format.

    Args:
        email: The email to sanitize

    Returns:
        Sanitized email (lowercase)

    Raises:
        ValueError: If email format is invalid

    Examples:
        >>> sanitize_email("User@Example.COM")
        "user@example.com"

        >>> sanitize_email("invalid-email")
        ValueError: Invalid email format
    """
    if not email:
        raise ValueError("Email cannot be empty")

    # Convert to lowercase
    email = email.lower().strip()

    # Basic email validation
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        raise ValueError("Invalid email format")

    return email
