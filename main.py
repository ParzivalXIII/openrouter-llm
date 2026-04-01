"""FastAPI application factory and entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.exceptions import AppError, app_error_handler
from app.router import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance.

    Yields:
        Control to the application.
    """
    # Startup
    logger.info("Starting OpenRouter FastAPI Service...")
    settings = get_settings()
    logger.info(f"Configured model: {settings.model_id}")
    logger.info(f"Environment: {settings.environment}")

    yield

    # Shutdown
    logger.info("Shutting down OpenRouter FastAPI Service...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_title,
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to known origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    app.add_exception_handler(AppError, app_error_handler)

    # Include routers
    app.include_router(router)

    # Top-level health check (duplicate for convenience)
    @app.get("/health")
    async def root_health():
        """Root-level health check endpoint."""
        return {
            "status": "healthy",
            "service": settings.app_title,
            "model": settings.model_id,
        }

    return app


# Create application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
