"""
Platform-independent Git repository cloning with Windows support.
"""

import logging
import os
import platform
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def clone_repo(repo_url: str, clone_path: str = "./repo") -> str:
    """
    Clone a Git repository with Windows compatibility and security.

    Args:
        repo_url: URL of the Git repository to clone
        clone_path: Local path where the repository should be cloned

    Returns:
        str: Absolute path to the cloned repository
    """
    logger.info("🚀 Starting repository clone...")

    # Validate inputs
    if not repo_url or not repo_url.strip():
        raise ValueError("Repository URL cannot be empty")

    # Basic URL validation
    if not _is_valid_repo_url(repo_url):
        raise ValueError("Invalid repository URL or unsupported provider")

    # Prepare clone path
    clone_path_obj = Path(clone_path).resolve()

    # Ensure Git is available and configured for Windows
    _ensure_git_ready()

    # Clean and prepare directory
    if clone_path_obj.exists():
        logger.info(f"Cleaning existing directory: {clone_path_obj}")
        shutil.rmtree(clone_path_obj, ignore_errors=True)

    clone_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Perform clone with Windows compatibility
    _git_clone_with_fallback(repo_url, clone_path_obj)

    logger.info(f"✅ Repository cloned successfully to: {clone_path_obj}")
    return str(clone_path_obj)


def _is_valid_repo_url(repo_url: str) -> bool:
    """Simple URL validation for Git repositories."""
    try:
        parsed = urlparse(repo_url)

        # Basic checks
        if not parsed.scheme or not parsed.netloc:
            return False

        # Only allow HTTPS and Git protocols
        if parsed.scheme not in ["https", "git"]:
            return False

        # Only allow trusted hosts
        trusted_hosts = ["github.com", "gitlab.com", "bitbucket.org"]
        return any(host in parsed.netloc.lower() for host in trusted_hosts)

    except Exception:
        return False


def _ensure_git_ready() -> None:
    """Ensure Git is available and configure for Windows if needed."""
    try:
        # Check if Git is available
        result = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, timeout=10, check=True
        )
        logger.debug(f"Git version: {result.stdout.strip()}")

        # Configure Git for Windows
        if platform.system().lower() == "windows":
            _setup_windows_git()

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        raise RuntimeError("Git is not installed or not available in PATH")


def _setup_windows_git() -> None:
    """Configure Git for Windows compatibility."""
    logger.debug("🪟 Setting up Git for Windows...")

    # Essential Windows Git configurations
    configs = [
        ("http.postBuffer", "524288000"),  # Large buffer for stability
        ("http.lowSpeedLimit", "0"),  # Disable speed limits
        ("http.lowSpeedTime", "999999"),  # Disable timeouts
        ("http.version", "HTTP/1.1"),  # Force HTTP/1.1
        ("core.fscache", "true"),  # Enable file system cache
    ]

    for key, value in configs:
        try:
            subprocess.run(
                ["git", "config", "--global", key, value],
                capture_output=True,
                timeout=10,
                check=False,
            )
        except Exception:
            pass  # Ignore config errors


def _git_clone_with_fallback(repo_url: str, clone_path: Path) -> None:
    """Clone repository with Windows fallback support."""
    is_windows = platform.system().lower() == "windows"

    # Standard clone command
    cmd = [
        "git",
        "clone",
        "--depth",
        "1",  # Shallow clone
        "--single-branch",  # Only default branch
        repo_url,
        str(clone_path),
    ]

    # Windows-specific configurations
    if is_windows:
        logger.info("🪟 Using Windows-optimized clone...")
        cmd.extend(
            [
                "--config",
                "http.postBuffer=524288000",
                "--config",
                "http.version=HTTP/1.1",
                "--config",
                "core.symlinks=false",
            ]
        )

    # Setup environment
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"  # No interactive prompts

    try:
        # First attempt
        logger.debug(f"Executing: {' '.join(shlex.quote(arg) for arg in cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300, check=True, env=env
        )
        logger.debug("✅ Clone successful")

    except subprocess.CalledProcessError as e:
        # Windows fallback for networking issues
        if is_windows and _is_network_error(e.stderr):
            logger.warning("🔄 Network issue detected, trying fallback...")
            _windows_fallback_clone(repo_url, clone_path, env)
        else:
            error_msg = (
                f"Git clone failed: {e.stderr.strip() if e.stderr else 'Unknown error'}"
            )
            raise RuntimeError(error_msg)

    except subprocess.TimeoutExpired:
        raise RuntimeError("Git clone timed out after 5 minutes")


def _is_network_error(stderr: str) -> bool:
    """Check if error is a Windows networking issue."""
    if not stderr:
        return False

    network_errors = [
        "getaddrinfo() thread failed to start",
        "unable to access",
        "connection timed out",
        "could not resolve host",
    ]

    return any(error in stderr.lower() for error in network_errors)


def _windows_fallback_clone(repo_url: str, clone_path: Path, env: dict) -> None:
    """Simplified Windows fallback clone."""
    logger.info("🔧 Using Windows fallback method...")

    fallback_cmd = [
        "git",
        "clone",
        "--config",
        "http.version=HTTP/1.1",
        "--config",
        "http.postBuffer=1048576",  # 1MB buffer
        "--depth",
        "1",
        repo_url,
        str(clone_path),
    ]

    try:
        subprocess.run(
            fallback_cmd,
            capture_output=True,
            text=True,
            timeout=600,
            check=True,
            env=env,
        )
        logger.info("✅ Fallback clone successful")

    except subprocess.CalledProcessError as e:
        # Provide helpful error message
        suggestions = [
            "1. Check internet connection",
            "2. Try using Git Bash instead of Command Prompt",
            "3. Configure proxy if behind corporate firewall",
            "4. Temporarily disable Windows Defender",
            f"5. Manual clone: git clone {repo_url}",
        ]

        error_msg = f"Clone failed. Suggestions:\n" + "\n".join(suggestions)
        raise RuntimeError(error_msg)


def diagnose_windows_git_issues() -> dict:
    """Diagnose Windows Git issues and provide solutions."""
    if platform.system().lower() != "windows":
        return {"message": "This diagnostic is for Windows systems only."}

    logger.info("🔍 Running Windows Git diagnostic...")

    diagnostic = {
        "platform": platform.platform(),
        "git_version": "Not found",
        "connectivity": {},
        "suggestions": [],
    }

    # Check Git
    try:
        result = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, timeout=10, check=True
        )
        diagnostic["git_version"] = result.stdout.strip()
    except Exception:
        diagnostic["suggestions"].append("Install Git for Windows")

    # Test connectivity
    hosts = ["github.com", "8.8.8.8"]
    for host in hosts:
        try:
            subprocess.run(
                ["ping", "-n", "1", host], capture_output=True, timeout=10, check=True
            )
            diagnostic["connectivity"][host] = "✅ Reachable"
        except Exception:
            diagnostic["connectivity"][host] = "❌ Unreachable"
            diagnostic["suggestions"].append(f"Check connectivity to {host}")

    # Add general suggestions
    if any("❌" in status for status in diagnostic["connectivity"].values()):
        diagnostic["suggestions"].extend(
            [
                "Try using Git Bash instead of Command Prompt",
                "Temporarily disable Windows Defender",
                "Check firewall/proxy settings",
                "Use mobile hotspot to test",
            ]
        )

    return diagnostic


def get_repo_info(clone_path: str) -> Optional[dict]:
    """Get basic repository information."""
    repo_path = Path(clone_path).resolve()

    if not repo_path.exists() or not (repo_path / ".git").exists():
        return None

    try:
        # Get basic Git info
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout.strip()

        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout.strip()

        remote = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout.strip()

        return {
            "branch": branch,
            "commit": commit[:8],  # Short commit hash
            "remote_url": remote,
            "path": str(repo_path),
        }

    except Exception as e:
        logger.warning(f"Could not get repo info: {e}")
        return None
