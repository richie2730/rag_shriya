"""
Validation utilities for repository processing.
"""

import logging
import os
from pathlib import Path
from typing import List, Set

from core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


async def validate_repository_size(repo_path: str, max_size_mb: int) -> None:
    """
    Validate that repository size is within limits.

    Args:
        repo_path: Path to repository
        max_size_mb: Maximum size in megabytes

    Raises:
        ProcessingError: If repository is too large
    """
    try:
        total_size = 0
        path = Path(repo_path)

        for file_path in path.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except (OSError, IOError):
                    # Skip files that can't be accessed
                    continue

        size_mb = total_size / (1024 * 1024)

        if size_mb > max_size_mb:
            raise ProcessingError(
                f"Repository size ({size_mb:.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
            )

        logger.info(f"Repository size validation passed: {size_mb:.2f} MB")

    except ProcessingError:
        raise
    except Exception as e:
        raise ProcessingError(f"Failed to validate repository size: {str(e)}")


async def validate_file_types(
    repo_path: str, allowed_extensions: List[str], max_file_size_mb: int
) -> None:
    """
    Validate file types and sizes in repository.

    Args:
        repo_path: Path to repository
        allowed_extensions: List of allowed file extensions
        max_file_size_mb: Maximum file size in megabytes

    Raises:
        ProcessingError: If validation fails
    """
    try:
        path = Path(repo_path)
        processable_files = 0
        large_files = []

        # Normalize extensions (ensure they start with '.')
        normalized_extensions = set()
        for ext in allowed_extensions:
            if not ext.startswith("."):
                ext = "." + ext
            normalized_extensions.add(ext.lower())

        for file_path in path.rglob("*"):
            if file_path.is_file():
                # Check file extension
                if file_path.suffix.lower() in normalized_extensions:
                    processable_files += 1

                    # Check file size
                    try:
                        file_size_mb = file_path.stat().st_size / (1024 * 1024)
                        if file_size_mb > max_file_size_mb:
                            large_files.append((str(file_path), file_size_mb))
                    except (OSError, IOError):
                        # Skip files that can't be accessed
                        continue

        if processable_files == 0:
            raise ProcessingError(
                f"No processable files found with extensions: {', '.join(allowed_extensions)}"
            )

        if large_files:
            large_files_info = [
                f"{path} ({size:.2f} MB)" for path, size in large_files[:5]
            ]
            raise ProcessingError(
                f"Files exceed maximum size ({max_file_size_mb} MB): {', '.join(large_files_info)}"
            )

        logger.info(
            f"File validation passed: {processable_files} processable files found"
        )

    except ProcessingError:
        raise
    except Exception as e:
        raise ProcessingError(f"Failed to validate file types: {str(e)}")


def validate_repository_url(repo_url: str) -> None:
    """
    Validate repository URL format and security.

    Args:
        repo_url: Repository URL to validate

    Raises:
        ProcessingError: If URL is invalid or unsafe
    """
    try:
        from urllib.parse import urlparse
        import re

        # Parse URL
        parsed = urlparse(repo_url)

        # Check scheme
        if parsed.scheme not in ["http", "https"]:
            raise ProcessingError("Repository URL must use HTTP or HTTPS protocol")

        # Check for supported hosts
        supported_hosts = ["github.com", "gitlab.com", "bitbucket.org"]
        if not any(host in parsed.netloc.lower() for host in supported_hosts):
            raise ProcessingError(
                f"Unsupported repository host. Supported: {', '.join(supported_hosts)}"
            )

        # Check for suspicious patterns
        suspicious_patterns = [
            r"[;&|`$]",  # Command injection characters
            r"\.\.",  # Directory traversal
            r"[<>]",  # Redirection operators
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, repo_url):
                raise ProcessingError(f"Suspicious pattern detected in URL: {pattern}")

        # Check URL length
        if len(repo_url) > 2048:
            raise ProcessingError("Repository URL is too long")

        logger.info(f"Repository URL validation passed: {repo_url}")

    except ProcessingError:
        raise
    except Exception as e:
        raise ProcessingError(f"Failed to validate repository URL: {str(e)}")


def validate_repository_structure(repo_path: str) -> None:
    """
    Validate repository has a valid structure.

    Args:
        repo_path: Path to repository

    Raises:
        ProcessingError: If repository structure is invalid
    """
    try:
        path = Path(repo_path)

        if not path.exists():
            raise ProcessingError("Repository path does not exist")

        if not path.is_dir():
            raise ProcessingError("Repository path is not a directory")

        # Check if it's a Git repository
        git_dir = path / ".git"
        if not git_dir.exists():
            logger.warning("Repository does not contain .git directory")

        # Check for common repository files
        common_files = ["README.md", "README.txt", "readme.md", "README"]
        has_readme = any((path / filename).exists() for filename in common_files)

        if not has_readme:
            logger.warning("Repository does not contain a README file")

        # Count total files
        total_files = sum(1 for _ in path.rglob("*") if _.is_file())

        if total_files == 0:
            raise ProcessingError("Repository contains no files")

        if total_files > 50000:  # Arbitrary large number
            raise ProcessingError(f"Repository contains too many files ({total_files})")

        logger.info(
            f"Repository structure validation passed: {total_files} files found"
        )

    except ProcessingError:
        raise
    except Exception as e:
        raise ProcessingError(f"Failed to validate repository structure: {str(e)}")


def get_repository_stats(repo_path: str) -> dict:
    """
    Get statistics about repository content.

    Args:
        repo_path: Path to repository

    Returns:
        dict: Repository statistics
    """
    try:
        path = Path(repo_path)
        stats = {
            "total_files": 0,
            "total_size_mb": 0.0,
            "file_types": {},
            "largest_files": [],
        }

        file_sizes = []

        for file_path in path.rglob("*"):
            if file_path.is_file():
                try:
                    file_size = file_path.stat().st_size
                    file_ext = file_path.suffix.lower() or "no_extension"

                    stats["total_files"] += 1
                    stats["total_size_mb"] += file_size / (1024 * 1024)

                    # Count file types
                    stats["file_types"][file_ext] = (
                        stats["file_types"].get(file_ext, 0) + 1
                    )

                    # Track largest files
                    file_sizes.append((str(file_path), file_size))

                except (OSError, IOError):
                    continue

        # Get top 10 largest files
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        stats["largest_files"] = [
            {"path": path, "size_mb": size / (1024 * 1024)}
            for path, size in file_sizes[:10]
        ]

        return stats

    except Exception as e:
        logger.error(f"Failed to get repository stats: {str(e)}")
        return {}
