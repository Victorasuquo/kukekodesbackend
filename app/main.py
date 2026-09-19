"""
Kukekodes FastAPI application entry point.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from contextlib import asynccontextmanager
import logging
import uuid

from app.config import settings
from app.db.postgres import init_db, engine
from app.db.mongodb import connect_mongodb, disconnect_mongodb, get_mongodb
from app.security import CORS_CONFIG, SECURITY_HEADERS
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.accountability import router as accountability_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# LIFESPAN EVENTS
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    
    # === STARTUP ===
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    try:
        # Initialize PostgreSQL
        logger.info("Initializing PostgreSQL...")
        init_db()
        logger.info("PostgreSQL initialized")
        
        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        connect_mongodb()
        logger.info("MongoDB connected")
        
        logger.info(f"{settings.APP_NAME} started successfully")
    
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        if settings.is_production:
            raise
        logger.warning("Continuing startup in degraded development mode")
    
    yield
    
    # === SHUTDOWN ===
    logger.info(f"Shutting down {settings.APP_NAME}")
    
    try:
        disconnect_mongodb()
        logger.info("MongoDB disconnected")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")
    
    logger.info(f"{settings.APP_NAME} shut down")


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    description="Global learning platform for coding and AI skills",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_CONFIG["allow_origins"],
    allow_credentials=CORS_CONFIG["allow_credentials"],
    allow_methods=CORS_CONFIG["allow_methods"],
    allow_headers=CORS_CONFIG["allow_headers"],
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.TRUSTED_HOSTS,
)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.exception("Unhandled exception", extra={"request_id": request_id})
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "internal_error",
            "message": "Internal server error",
            "request_id": request_id,
        },
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "code": "not_found",
            "message": "Resource not found",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# ============================================================================
# RESPONSE MIDDLEWARE (Add security headers)
# ============================================================================

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    response.headers["X-Request-ID"] = request_id
    
    return response


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/livez", tags=["Health"])
async def livez():
    """Process liveness check that does not depend on external services."""
    return {
        "status": "live",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/readyz", tags=["Health"])
async def readyz():
    """Readiness check for required runtime dependencies."""
    checks: dict[str, str] = {}
    overall_status = status.HTTP_200_OK

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:
        logger.warning("PostgreSQL readiness check failed: %s", exc)
        checks["postgres"] = "failed"
        overall_status = status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        get_mongodb().command("ping")
        checks["mongodb"] = "ok"
    except Exception as exc:
        logger.warning("MongoDB readiness check failed: %s", exc)
        checks["mongodb"] = "failed"
        overall_status = status.HTTP_503_SERVICE_UNAVAILABLE

    if settings.REDIS_URL:
        try:
            import redis
            redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2).ping()
            checks["redis"] = "ok"
        except Exception as exc:
            logger.warning("Redis readiness check failed: %s", exc)
            checks["redis"] = "failed"
            if settings.is_production:
                overall_status = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        checks["redis"] = "missing"
        if settings.is_production:
            overall_status = status.HTTP_503_SERVICE_UNAVAILABLE

    checks["configuration"] = "ok"
    payload = {
        "status": "ready" if overall_status == status.HTTP_200_OK else "not_ready",
        "checks": checks,
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
    if overall_status != status.HTTP_200_OK:
        return JSONResponse(status_code=overall_status, content=payload)
    return payload


@app.get("/health", tags=["Health"], include_in_schema=False)
async def health_check():
    """Backward-compatible liveness alias."""
    return await livez()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

# Import routes
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.admin.auth_routes import router as admin_auth_router
from app.api.v1.admin.routes import router as admin_router
from app.api.v1.courses.routes import router as courses_router
from app.api.v1.modules.routes import router as modules_router
from app.api.v1.lessons.routes import router as lessons_router
from app.api.v1.organizations.routes import router as organizations_router
from app.api.v1.enrollments.routes import router as enrollments_router
from app.api.v1.progress.routes import router as progress_router
from app.api.v1.users.routes import router as users_router
from app.api.v1.gamification.routes import router as gamification_router
from app.api.v1.notifications.routes import router as notifications_router
from app.api.v1.quizzes.routes import router as quizzes_router
from app.api.v1.community.routes import router as community_router
from app.api.v1.ai.routes import router as ai_router
from app.api.v1.live.routes import router as live_router
from app.api.v1.exercises.routes import router as exercises_router

# Include routers
app.include_router(auth_router)
app.include_router(admin_auth_router)
app.include_router(admin_router)
app.include_router(courses_router)
app.include_router(modules_router)
app.include_router(lessons_router)
app.include_router(organizations_router)
app.include_router(enrollments_router)
app.include_router(progress_router)
app.include_router(users_router)
app.include_router(gamification_router)
app.include_router(quizzes_router)
app.include_router(community_router)
app.include_router(ai_router)
app.include_router(live_router)
app.include_router(exercises_router)
app.include_router(notifications_router)
app.include_router(webhooks_router)
app.include_router(accountability_router)


# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
