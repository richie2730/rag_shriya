"""
Cleanup utilities for temporary files and directories.
"""

import logging
import os
import shutil
import stat
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def cleanup_directory(directory_path: str, force: bool = True) -> None:
    """
    Clean up a directory and all its contents.

    Args:
        directory_path: Path to directory to clean up
        force: If True, remove read-only files as well

    Raises:
        OSError: If cleanup fails
    """
    try:
        path = Path(directory_path)
        
        if not path.exists():
            logger.debug(f"Directory does not exist: {directory_path}")
            return

        if not path.is_dir():
            logger.warning(f"Path is not a directory: {directory_path}")
            return

        # Handle Windows read-only files
        if force and os.name == 'nt':  # Windows
            _handle_readonly_files(path)

        # Remove the directory
        shutil.rmtree(path, ignore_errors=not force)
        
        logger.info(f"Successfully cleaned up directory: {directory_path}")

    except Exception as e:
        logger.error(f"Failed to cleanup directory {directory_path}: {str(e)}")
        raise


def cleanup_file(file_path: str, force: bool = True) -> None:
    """
    Clean up a single file.

    Args:
        file_path: Path to file to clean up
        force: If True, remove read-only files as well

    Raises:
        OSError: If cleanup fails
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            logger.debug(f"File does not exist: {file_path}")
            return

        if not path.is_file():
            logger.warning(f"Path is not a file: {file_path}")
            return

        # Handle Windows read-only files
        if force and os.name == 'nt':  # Windows
            if not os.access(path, os.W_OK):
                os.chmod(path, stat.S_IWRITE)

        # Remove the file
        path.unlink()
        
        logger.info(f"Successfully cleaned up file: {file_path}")

    except Exception as e:
        logger.error(f"Failed to cleanup file {file_path}: {str(e)}")
        raise


def _handle_readonly_files(directory: Path) -> None:
    """
    Handle read-only files on Windows.

    Args:
        directory: Directory to process
    """
    try:
        for root, dirs, files in os.walk(directory):
            # Handle files
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if not os.access(file_path, os.W_OK):
                        os.chmod(file_path, stat.S_IWRITE)
                except (OSError, IOError):
                    pass  # Ignore errors, shutil.rmtree will handle

            # Handle directories
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.access(dir_path, os.W_OK):
                        os.chmod(dir_path, stat.S_IWRITE)
                except (OSError, IOError):
                    pass  # Ignore errors

    except Exception as e:
        logger.warning(f"Failed to handle read-only files: {str(e)}")


def get_directory_size(directory_path: str) -> int:
    """
    Get the total size of a directory in bytes.

    Args:
        directory_path: Path to directory

    Returns:
        Total size in bytes
    """
    try:
        total_size = 0
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            return 0

        for file_path in path.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except (OSError, IOError):
                    continue  # Skip files that can't be accessed

        return total_size

    except Exception as e:
        logger.error(f"Failed to get directory size for {directory_path}: {str(e)}")
        return 0


def cleanup_temp_directories(base_temp_dir: str, max_age_hours: int = 24) -> int:
    """
    Clean up old temporary directories.

    Args:
        base_temp_dir: Base temporary directory path
        max_age_hours: Maximum age in hours before cleanup

    Returns:
        Number of directories cleaned up
    """
    try:
        import time
        
        cleaned_count = 0
        base_path = Path(base_temp_dir)
        
        if not base_path.exists():
            return 0

        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        for item in base_path.iterdir():
            if item.is_dir():
                try:
                    # Check directory age
                    dir_age = current_time - item.stat().st_mtime
                    
                    if dir_age > max_age_seconds:
                        cleanup_directory(str(item))
                        cleaned_count += 1
                        logger.info(f"Cleaned up old temp directory: {item}")

                except Exception as e:
                    logger.warning(f"Failed to cleanup temp directory {item}: {str(e)}")
                    continue

        return cleaned_count

    except Exception as e:
        logger.error(f"Failed to cleanup temp directories: {str(e)}")
        return 0


def ensure_directory_writable(directory_path: str) -> None:
    """
    Ensure a directory is writable.

    Args:
        directory_path: Path to directory

    Raises:
        OSError: If directory cannot be made writable
    """
    try:
        path = Path(directory_path)
        
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

        # Check if writable
        if not os.access(path, os.W_OK):
            # Try to make writable
            if os.name == 'nt':  # Windows
                os.chmod(path, stat.S_IWRITE)
            else:  # Unix-like
                os.chmod(path, stat.S_IRWXU)

        # Verify it's now writable
        if not os.access(path, os.W_OK):
            raise OSError(f"Directory is not writable: {directory_path}")

    except Exception as e:
        logger.error(f"Failed to ensure directory is writable {directory_path}: {str(e)}")
        raise