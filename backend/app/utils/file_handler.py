"""
File handling utilities.
"""

import os
from pathlib import Path
from typing import Optional
from app.core.logger import logger

def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory_path: Path to the directory

    Returns:
        True if directory exists or was created successfully
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {e}")
        return False

def get_file_size(file_path: str) -> Optional[int]:
    """
    Get the size of a file in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes, or None if file doesn't exist
    """
    try:
        return os.path.getsize(file_path)
    except OSError:
        return None

def is_valid_file_type(filename: str, allowed_extensions: set) -> bool:
    """
    Check if file has a valid extension.

    Args:
        filename: Filename to check
        allowed_extensions: Set of allowed extensions (with dots)

    Returns:
        True if file type is allowed
    """
    if not filename:
        return False

    file_ext = Path(filename).suffix.lower()
    return file_ext in allowed_extensions

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path separators and other dangerous characters
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    sanitized = filename

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')

    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext

    return sanitized

def cleanup_old_files(directory: str, max_age_days: int = 30) -> int:
    """
    Clean up old files from a directory.

    Args:
        directory: Directory to clean
        max_age_days: Maximum age of files to keep

    Returns:
        Number of files deleted
    """
    import time

    deleted_count = 0
    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)

    try:
        for file_path in Path(directory).rglob('*'):
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1

    except Exception as e:
        logger.error(f"Error cleaning up old files in {directory}: {e}")

    return deleted_count
