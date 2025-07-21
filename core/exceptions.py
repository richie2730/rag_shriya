"""
Custom exceptions and error handling for the application.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class CodeDocumentationError(Exception):
    """Base exception for code documentation errors."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code or "DOCUMENTATION_ERROR"
        super().__init__(self.message)


class RepositoryError(CodeDocumentationError):
    """Exception raised for repository-related errors."""

    def __init__(self, message: str):
        super().__init__(message, "REPOSITORY_ERROR")


class ProcessingError(CodeDocumentationError):
    """Exception raised for processing-related errors."""

    def __init__(self, message: str):
        super().__init__(message, "PROCESSING_ERROR")


class VectorDatabaseError(CodeDocumentationError):
    """Exception raised for vector database errors."""

    def __init__(self, message: str):
        super().__init__(message, "VECTOR_DB_ERROR")


class LLMError(CodeDocumentationError):
    """Exception raised for LLM-related errors."""

    def __init__(self, message: str):
        super().__init__(message, "LLM_ERROR")


class SecurityError(CodeDocumentationError):
    """Exception raised for security-related errors."""

    def __init__(self, message: str):
        super().__init__(message, "SECURITY_ERROR")


def create_error_response(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """
    Create standardized error response.

    Args:
        status_code: HTTP status code
        message: Error message
        error_code: Application-specific error code
        details: Additional error details

    Returns:
        JSONResponse: Formatted error response
    """
    content = {
        "error": {
            "message": message,
            "code": error_code or "UNKNOWN_ERROR",
            "status_code": status_code,
        }
    }

    if details:
        content["error"]["details"] = details

    return JSONResponse(status_code=status_code, content=content)


def handle_exceptions(app: FastAPI) -> None:
    """
    Register exception handlers for the FastAPI application.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(CodeDocumentationError)
    async def code_documentation_exception_handler(
        request: Request, exc: CodeDocumentationError
    ):
        """Handle custom code documentation errors."""
        logger.error(f"Code documentation error: {exc.message}")

        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=exc.message,
            error_code=exc.error_code,
        )

    @app.exception_handler(RepositoryError)
    async def repository_exception_handler(request: Request, exc: RepositoryError):
        """Handle repository-related errors."""
        logger.error(f"Repository error: {exc.message}")

        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=exc.message,
            error_code=exc.error_code,
        )

    @app.exception_handler(ProcessingError)
    async def processing_exception_handler(request: Request, exc: ProcessingError):
        """Handle processing-related errors."""
        logger.error(f"Processing error: {exc.message}")

        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=exc.message,
            error_code=exc.error_code,
        )

    @app.exception_handler(VectorDatabaseError)
    async def vector_db_exception_handler(request: Request, exc: VectorDatabaseError):
        """Handle vector database errors."""
        logger.error(f"Vector database error: {exc.message}")

        return create_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=exc.message,
            error_code=exc.error_code,
        )

    @app.exception_handler(LLMError)
    async def llm_exception_handler(request: Request, exc: LLMError):
        """Handle LLM-related errors."""
        logger.error(f"LLM error: {exc.message}")

        return create_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=exc.message,
            error_code=exc.error_code,
        )

    @app.exception_handler(SecurityError)
    async def security_exception_handler(request: Request, exc: SecurityError):
        """Handle security-related errors."""
        logger.warning(f"Security error: {exc.message}")

        return create_error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            message=exc.message,
            error_code=exc.error_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle request validation errors."""
        logger.warning(f"Validation error: {exc.errors()}")

        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Request validation failed",
            error_code="VALIDATION_ERROR",
            details={"validation_errors": exc.errors()},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions."""
        logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")

        return create_error_response(
            status_code=exc.status_code, message=exc.detail, error_code="HTTP_ERROR"
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected errors."""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)

        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            error_code="INTERNAL_ERROR",
        )
