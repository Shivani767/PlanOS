"""PlanOS main application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from planos.app.api.routes import agents, auth, plans, runs, scenarios
from planos.app.core.config import settings
from planos.app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    PlanOSError,
    TenantIsolationError,
    UnauthorizedError,
    ValidationError,
)
from planos.app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    configure_logging()
    logger.info("PlanOS starting", environment=settings.app_env)
    yield
    logger.info("PlanOS shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="PlanOS",
        description="A Reliable Agent Runtime for Enterprise Planning",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(PlanOSError)
    async def planos_error_handler(request: Request, exc: PlanOSError) -> JSONResponse:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        if isinstance(exc, NotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, UnauthorizedError):
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, (ForbiddenError, TenantIsolationError)):
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, ValidationError):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(exc, ConflictError):
            status_code = status.HTTP_409_CONFLICT

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred" if not settings.debug else str(exc),
                }
            },
        )

    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        return {
            "status": "healthy",
            "version": "0.1.0",
            "environment": settings.app_env,
        }

    # Include routers
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(plans.router, prefix="/api/v1")
    app.include_router(scenarios.router, prefix="/api/v1")
    app.include_router(runs.router, prefix="/api/v1")

    return app


app = create_app()
