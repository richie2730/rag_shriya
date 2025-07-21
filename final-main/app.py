"""
FastAPI application for automated code documentation generation.
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Optional, Any, List

import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, HttpUrl, field_validator

from core.config import get_settings
from core.exceptions import CodeDocumentationError, handle_exceptions
from services.documentation_service import DocumentationService
from modules.vector_db_factory import list_available_providers as list_vector_providers
from modules.llm_factory import list_available_llm_providers, get_configured_providers
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Application state
app_state: Dict[str, Any] = {"documentation_service": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting Code Documentation API...")

    # Initialize services
    settings = get_settings()
    app_state["documentation_service"] = DocumentationService(settings)

    yield

    logger.info("Shutting down Code Documentation API...")


# Initialize FastAPI app with proper security documentation
app = FastAPI(
    title="Code Documentation Generator API",
    description="AI-powered automatic code documentation generation service",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    # Configure security for Swagger UI
    openapi_tags=[
        {"name": "health", "description": "Health check operations"},
        {
            "name": "documentation",
            "description": "Code documentation generation operations",
        },
    ],
)

# Add exception handlers
handle_exceptions(app)


# Request/Response models
class DocumentationRequest(BaseModel):
    """Request model for documentation generation."""

    repo_url: HttpUrl
    repo_name: Optional[str] = None
    include_diagrams: bool = True
    file_extensions: list[str] = [
        ".py",
        ".java",
        ".js",
        ".ts",
        ".go",
        ".cpp",
        ".c",
        ".rs",
    ]

    # Provider selection
    vector_db_provider: str = "pinecone"  # "pinecone", "faiss", "qdrant"
    llm_provider: str = "gemini"  # "gemini", "openai", "azure_openai"

    @field_validator("repo_url")
    @classmethod
    def validate_repo_url(cls, v):
        """Validate repository URL."""
        url_str = str(v)
        allowed_hosts = ["github.com", "gitlab.com", "bitbucket.org"]

        # Security: Check for dangerous patterns
        import re

        dangerous_patterns = [r"[;&|`$]", r"\.\.", r"[<>]"]
        for pattern in dangerous_patterns:
            if re.search(pattern, url_str):
                raise ValueError("Invalid characters detected in repository URL")

        if not any(host in url_str for host in allowed_hosts):
            raise ValueError(
                "Only GitHub, GitLab, and Bitbucket repositories are supported"
            )

        # Security: Ensure HTTPS
        if not url_str.startswith("https://"):
            raise ValueError("Only HTTPS URLs are allowed for security")

        if not url_str.endswith(".git"):
            return url_str + ".git"

        return url_str

    @field_validator("file_extensions")
    @classmethod
    def validate_file_extensions(cls, v):
        """Validate file extensions."""
        if not v:
            raise ValueError("At least one file extension must be specified")

        valid_extensions = {
            ".py",
            ".java",
            ".js",
            ".ts",
            ".go",
            ".cpp",
            ".c",
            ".rs",
            ".php",
            ".rb",
        }
        for ext in v:
            if ext not in valid_extensions:
                raise ValueError(f"Unsupported file extension: {ext}")

        return v

    @field_validator("vector_db_provider")
    @classmethod
    def validate_vector_db_provider(cls, v):
        """Validate vector database provider."""
        valid_providers = {"pinecone", "faiss", "qdrant"}
        if v not in valid_providers:
            raise ValueError(
                f"Unsupported vector database provider: {v}. Valid options: {valid_providers}"
            )
        return v

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v):
        """Validate LLM provider."""
        valid_providers = {"gemini", "openai", "azure_openai"}
        if v not in valid_providers:
            raise ValueError(
                f"Unsupported LLM provider: {v}. Valid options: {valid_providers}"
            )
        return v


class DocumentationResponse(BaseModel):
    """Response model for documentation generation."""

    task_id: str
    status: str
    message: str
    documentation: Optional[str] = None
    repo_name: Optional[str] = None
    processing_time: Optional[float] = None
    doc_file_path: Optional[str] = None
    storage_info: Optional[Dict[str, str]] = None


class DocumentationListResponse(BaseModel):
    """Response model for listing saved documentation."""

    total_count: int
    documentation_files: List[Dict[str, Any]]


class SavedDocumentationResponse(BaseModel):
    """Response model for retrieving saved documentation."""

    repo_name: str
    documentation: Optional[str] = None
    found: bool


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    timestamp: str


# API Routes
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health Check",
    description="Check if the API service is running and healthy",
)
async def health_check():
    """Health check endpoint."""
    from datetime import datetime

    return HealthResponse(
        status="healthy", version="1.0.0", timestamp=datetime.utcnow().isoformat()
    )


@app.get(
    "/providers",
    tags=["documentation"],
    summary="Get available providers",
    description="Get information about available vector database and LLM providers",
)
async def get_providers():
    """Get available vector database and LLM providers."""
    try:
        vector_providers = list_vector_providers()
        llm_providers = list_available_llm_providers()
        configured_llm_providers = get_configured_providers()

        return {
            "vector_databases": {
                "available": vector_providers,
                "supported": ["pinecone", "faiss", "qdrant"],
                "descriptions": {
                    "pinecone": "Cloud-based vector database with advanced features",
                    "faiss": "Local vector database for fast similarity search",
                    "qdrant": "Open-source vector database with API and UI",
                },
            },
            "llm_providers": {
                "available": llm_providers,
                "configured": configured_llm_providers,
                "supported": ["gemini", "openai", "azure_openai"],
                "descriptions": {
                    "gemini": "Google's Gemini Pro model with advanced reasoning",
                    "openai": "OpenAI's GPT models (GPT-3.5, GPT-4)",
                    "azure_openai": "Microsoft Azure OpenAI service",
                },
            },
            "requirements": {
                "pinecone": "PINECONE_API_KEY environment variable",
                "faiss": "No external dependencies (local storage)",
                "qdrant": "QDRANT_URL and optional QDRANT_API_KEY",
                "gemini": "GEMINI_API_KEY environment variable",
                "openai": "OPENAI_API_KEY environment variable",
                "azure_openai": "AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME",
            },
        }

    except Exception as e:
        logger.error(f"Failed to get providers info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve providers information",
        )


@app.post(
    "/generate-documentation",
    response_model=DocumentationResponse,
    tags=["documentation"],
    summary="Generate Documentation",
    description="Generate AI-powered documentation for a given repository",
)
async def generate_documentation(request: DocumentationRequest):
    """
    Generate documentation for a given repository.

    Args:
        request: Documentation generation request
        background_tasks: FastAPI background tasks
        api_key: API key for authentication

    Returns:
        DocumentationResponse with task details
    """
    task_id = str(uuid.uuid4())
    logger.info(
        f"Starting documentation generation task {task_id} for {request.repo_url}"
    )

    try:
        # Extract repo name if not provided
        repo_name = request.repo_name or _extract_repo_name(str(request.repo_url))

        # Generate documentation
        documentation_service = app_state["documentation_service"]
        result = await documentation_service.generate_documentation(
            repo_url=str(request.repo_url),
            repo_name=repo_name,
            task_id=task_id,
            file_extensions=request.file_extensions,
            include_diagrams=request.include_diagrams,
            vector_db_provider=request.vector_db_provider,
            llm_provider=request.llm_provider,
        )

        return DocumentationResponse(
            task_id=task_id,
            status="completed",
            message="Documentation generated successfully",
            documentation=result["documentation"],
            repo_name=repo_name,
            processing_time=result["processing_time"],
            doc_file_path=result.get("storage_info", {}).get("doc_file"),
            storage_info=result.get("storage_info"),
        )

    except CodeDocumentationError as e:
        logger.error(f"Documentation generation failed for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Documentation generation failed: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error in task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred",
        )


@app.get(
    "/documentation/list",
    response_model=DocumentationListResponse,
    tags=["documentation"],
    summary="List all saved documentation",
    description="Get a list of all previously generated documentation files with metadata",
)
async def list_documentation():
    """List all saved documentation files."""
    try:
        documentation_service = app_state["documentation_service"]
        docs_list = documentation_service.list_all_documentation()

        return DocumentationListResponse(
            total_count=len(docs_list), documentation_files=docs_list
        )

    except Exception as e:
        logger.error(f"Failed to list documentation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documentation list",
        )


@app.get(
    "/documentation/{repo_name}",
    response_model=SavedDocumentationResponse,
    tags=["documentation"],
    summary="Get saved documentation for a repository",
    description="Retrieve the latest saved documentation for a specific repository",
)
async def get_saved_documentation(repo_name: str):
    """Get saved documentation for a specific repository."""
    try:
        documentation_service = app_state["documentation_service"]
        documentation = documentation_service.get_saved_documentation(repo_name)

        return SavedDocumentationResponse(
            repo_name=repo_name,
            documentation=documentation,
            found=documentation is not None,
        )

    except Exception as e:
        logger.error(f"Failed to get documentation for {repo_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documentation for {repo_name}",
        )


@app.get(
    "/diagnostic/windows",
    tags=["diagnostic"],
    summary="Windows Git diagnostic",
    description="Diagnose Windows-specific Git networking issues and provide solutions",
)
async def windows_git_diagnostic():
    """Diagnose Windows Git networking issues."""
    try:
        from modules.clone_repo import diagnose_windows_git_issues

        diagnostic_result = diagnose_windows_git_issues()

        return {
            "status": "success",
            "diagnostic": diagnostic_result,
            "message": "Diagnostic completed. Check suggestions for any issues found.",
        }

    except Exception as e:
        logger.error(f"Failed to run Windows diagnostic: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run diagnostic",
        )


@app.delete(
    "/documentation/cleanup",
    tags=["documentation"],
    summary="Clean up old documentation files",
    description="Remove old documentation files, keeping only recent versions",
)
async def cleanup_documentation(keep_versions: int = 3):
    """Clean up old documentation files."""
    try:
        documentation_service = app_state["documentation_service"]
        cleaned_count = documentation_service.cleanup_old_documentation(keep_versions)

        return {
            "status": "success",
            "message": f"Cleaned up {cleaned_count} old documentation files",
            "files_removed": cleaned_count,
            "versions_kept": keep_versions,
        }

    except Exception as e:
        logger.error(f"Failed to cleanup documentation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup documentation files",
        )


def _extract_repo_name(repo_url: str) -> str:
    """Extract repository name from URL."""
    from urllib.parse import urlparse

    parsed_url = urlparse(repo_url)
    path_parts = parsed_url.path.strip("/").split("/")

    if len(path_parts) >= 2:
        repo_name = path_parts[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        return repo_name

    raise ValueError("Invalid repository URL format")


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )
