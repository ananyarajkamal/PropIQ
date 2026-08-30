"""FastAPI Main Application Entry Point for PropIQ Backend.

Initializes FastAPI framework, configures restricted CORS middleware, registers security headers,
includes API routes, initializes local embedding models, and configures safe exception handlers.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import Config
from app.api.routes import (
    health,
    proposals,
    retrieval,
    analysis,
    comparison,
    risks,
    clarifications,
    scoring,
    recommendation,
)
from app.services.embedding_service import get_embedding_service
from app.services.rate_limiter import RateLimitExceededError, OperationInProgressError

# Configure backend logging format (Safe Logging Policy: No secrets, no full text!)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("propiq_backend")

# Initialize FastAPI application instance
app = FastAPI(
    title=Config.APP_NAME,
    version=Config.APP_VERSION,
    description="PropIQ AI Proposal Intelligence Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS Middleware for Frontend SPA access (Rule 27: Restricted origins!)
allowed_origins = list({
    Config.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
})
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all outgoing responses (Rule 77)."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Register API Routers
app.include_router(health.router, prefix="/api", tags=["System Health"])
app.include_router(proposals.router, prefix="/api/proposals", tags=["Proposal Processing"])
app.include_router(retrieval.router, prefix="/api/retrieval", tags=["Evidence Retrieval"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Requirements & Extraction"])
app.include_router(comparison.router, prefix="/api/comparison", tags=["Deterministic Comparison"])
app.include_router(risks.router, prefix="/api/risks", tags=["Risks & Contradictions"])
app.include_router(clarifications.router, prefix="/api/clarifications", tags=["Vendor Clarifications"])
app.include_router(scoring.router, prefix="/api/scoring", tags=["Deterministic Vendor Scoring"])
app.include_router(recommendation.router, prefix="/api/recommendation", tags=["Executive Recommendation"])


@app.on_event("startup")
async def startup_event():
    """Application startup handler initializing local sentence-transformer embedding model."""
    logger.info("PropIQ FastAPI Backend initializing...")
    logger.info("Configuration check completed. Groq API key status: %s", "Configured" if Config.is_groq_configured() else "Not configured")

    # Warm up local embedding model
    try:
        embedder = get_embedding_service()
        logger.info("Local embedding model '%s' initialized successfully.", embedder.model_name)
    except Exception as err:
        logger.error("Failed to initialize local embedding model: %s", str(err))


@app.exception_handler(RateLimitExceededError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceededError):
    """Handler for HTTP 429 Rate Limit Exceeded (Rule 54)."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error_code": "RATE_LIMITED",
            "message": str(exc),
            "retryable": True,
        },
    )


@app.exception_handler(OperationInProgressError)
async def operation_in_progress_exception_handler(request: Request, exc: OperationInProgressError):
    """Handler for HTTP 409 Operation In Progress (Rule 57)."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error_code": "OPERATION_IN_PROGRESS",
            "message": str(exc),
            "retryable": True,
        },
    )


@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    """Handler for client validation value errors (HTTP 400 Bad Request)."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error_code": "INVALID_INPUT",
            "message": str(exc),
            "retryable": False,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global unhandled exception handler returning safe non-sensitive error responses (Rule 28 & 30)."""
    logger.error("Unhandled server exception on %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "Something went wrong while processing this request. Please retry.",
            "retryable": True,
        },
    )
