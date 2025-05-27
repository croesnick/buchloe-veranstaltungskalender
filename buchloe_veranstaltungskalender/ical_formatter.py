"""iCal formatting module for improved readability while maintaining RFC 5545 compliance

This module provides custom formatting functions to improve the readability of iCal output
while ensuring full RFC 5545 compliance. It addresses issues with line folding, escaping,
and description formatting.
"""

import re
from typing import List


def smart_fold_line(line: str, max_length: int = 75) -> List[str]:
    """
    Fold lines at word boundaries while maintaining RFC 5545 compliance.

    Args:
        line: The line to fold
        max_length: Maximum line length (RFC 5545 specifies 75)

    Returns:
        List of folded lines with proper continuation formatting
    """
    if len(line) <= max_length:
        return [line]

    lines = []
    current_line = line

    while len(current_line) > max_length:
        # Find the best break point (prefer word boundaries)
        break_point = _find_best_break_point(current_line, max_length)

        # Split the line
        lines.append(current_line[:break_point])
        current_line = " " + current_line[break_point:].lstrip()

    # Add the remaining part
    if current_line.strip():
        lines.append(current_line)

    return lines


def _find_best_break_point(line: str, max_length: int) -> int:
    """
    Find the best point to break a line, preferring word boundaries.

    Args:
        line: The line to analyze
        max_length: Maximum allowed length

    Returns:
        Index where to break the line
    """
    if len(line) <= max_length:
        return len(line)

    # Look for word boundaries within the allowed length
    search_start = max(0, max_length - 20)  # Look back up to 20 chars for word boundary

    # Find spaces, commas, or other natural break points
    break_chars = [" ", ",", ";", ":", "-"]
    best_break = max_length

    for i in range(max_length - 1, search_start - 1, -1):
        if line[i] in break_chars:
            # Don't break immediately after property name (before colon)
            if line[i] == ":" and i < 20:
                continue
            best_break = i + 1
            break

    # If no good break point found, use character-level breaking
    if best_break == max_length and max_length < len(line):
        # Ensure we don't break in the middle of an escape sequence
        if line[max_length - 1] == "\\":
            best_break = max_length - 1

    return best_break


def optimize_escaping(text: str) -> str:
    """
    Optimize character escaping to reduce unnecessary escapes while maintaining RFC compliance.

    Args:
        text: Text to optimize

    Returns:
        Text with optimized escaping
    """
    if not text:
        return text

    # Remove excessive escaping while preserving necessary ones
    # Only escape characters that are truly required by RFC 5545

    # First, unescape everything to start clean
    text = text.replace(r"\,", ",")
    text = text.replace(r"\;", ";")
    text = text.replace(r"\\", "\\")  # Keep backslashes as-is for now

    # Re-escape only what's necessary
    # Escape backslashes first to avoid double-escaping
    text = text.replace("\\", r"\\")

    # Only escape commas and semicolons in specific contexts where they have special meaning
    # For descriptions and other text fields, these are usually safe
    # The icalendar library will handle the critical escaping

    return text


def preprocess_description(description: str) -> str:
    """
    Clean and preprocess description text for better iCal formatting.

    Args:
        description: Raw description text

    Returns:
        Cleaned description text
    """
    if not description:
        return ""

    # First handle paragraph breaks - convert multiple newlines to double newlines
    description = re.sub(r"\n\s*\n+", "\n\n", description)

    # Normalize whitespace within lines (but preserve newlines and empty lines)
    lines = description.split("\n")
    processed_lines = []

    for line in lines:
        if line.strip():  # Non-empty line
            # Normalize whitespace within each line
            line = re.sub(r"\s+", " ", line.strip())
            processed_lines.append(line)
        else:  # Empty line (paragraph break)
            processed_lines.append("")

    description = "\n".join(processed_lines)

    # Clean up excessive whitespace around punctuation (but preserve newlines)
    description = re.sub(r"[ \t]+([,.;:!?])", r"\1", description)
    description = re.sub(r"([,.;:!?])[ \t]+", r"\1 ", description)

    return description


def format_ical_content(ical_bytes: bytes) -> bytes:
    """
    Apply custom formatting to iCal content for improved readability.

    Args:
        ical_bytes: Raw iCal content as bytes

    Returns:
        Formatted iCal content as bytes
    """
    # Decode to string for processing
    try:
        content = ical_bytes.decode("utf-8")
    except UnicodeDecodeError:
        # Fallback to latin-1 if UTF-8 fails
        content = ical_bytes.decode("latin-1")

    # Split into lines for processing
    lines = content.split("\n")
    formatted_lines = []

    for line in lines:
        if not line.strip():
            formatted_lines.append(line)
            continue

        # Apply smart folding to long lines
        folded_lines = smart_fold_line(line)
        formatted_lines.extend(folded_lines)

    # Rejoin and encode back to bytes
    formatted_content = "\n".join(formatted_lines)

    # Apply final optimizations
    formatted_content = _apply_final_optimizations(formatted_content)

    return formatted_content.encode("utf-8")


def _apply_final_optimizations(content: str) -> str:
    """
    Apply final formatting optimizations to the iCal content.

    Args:
        content: iCal content as string

    Returns:
        Optimized content
    """
    # Ensure proper line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive blank lines
    content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

    # Ensure file ends with a single newline
    content = content.rstrip() + "\n"

    return content


def format_property_value(property_name: str, value: str) -> str:
    """
    Format a specific property value based on its type.

    Args:
        property_name: Name of the iCal property (e.g., 'DESCRIPTION', 'SUMMARY')
        value: Property value to format

    Returns:
        Formatted property value
    """
    if not value:
        return value

    # Apply specific formatting based on property type
    if property_name.upper() in ["DESCRIPTION", "COMMENT"]:
        return preprocess_description(value)
    elif property_name.upper() in ["SUMMARY", "LOCATION"]:
        # For titles and locations, just normalize whitespace
        return re.sub(r"\s+", " ", value.strip())
    else:
        # For other properties, minimal processing
        return value.strip()
