"""Custom exception types and error handlers."""

from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application exception with error code support."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        """Initialize AppError.

        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code.
            status_code: HTTP status code to return.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "INTERNAL_ERROR"
        self.status_code = status_code


class ConfigurationError(AppError):
    """Configuration or initialization error."""

    def __init__(self, message: str) -> None:
        """Initialize ConfigurationError."""
        super().__init__(
            message,
            error_code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class LLMInvocationError(AppError):
    """Error during LLM invocation after retries exhausted."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize LLMInvocationError.

        Args:
            message: Error message.
            original_error: The underlying exception that caused this error.
        """
        super().__init__(
            message,
            error_code="LLM_INVOCATION_FAILED",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.original_error = original_error


class ValidationError(AppError):
    """Request validation error."""

    def __init__(self, message: str) -> None:
        """Initialize ValidationError."""
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle AppError exceptions with structured JSON response.

    Args:
        request: The FastAPI request.
        exc: The AppError exception.

    Returns:
        JSONResponse with error details.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "path": str(request.url.path),
            }
        },
    )
