import asyncio

from fastapi import HTTPException

from app.config import Settings
from app.main import app
from app.security import get_current_admin


def test_openapi_has_canonical_phase0_routes() -> None:
    schema = app.openapi()
    paths = schema["paths"]

    for path in [
        "/livez",
        "/readyz",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/courses",
        "/api/v1/modules",
        "/api/v1/lessons",
    ]:
        assert path in paths


def test_operation_ids_are_unique() -> None:
    schema = app.openapi()
    operation_ids = []
    for operations in schema["paths"].values():
        for operation in operations.values():
            if isinstance(operation, dict) and operation.get("operationId"):
                operation_ids.append(operation["operationId"])

    assert len(operation_ids) == len(set(operation_ids))


def test_admin_dependency_rejects_instructors() -> None:
    try:
        asyncio.run(get_current_admin({"sub": "u1", "role": "instructor"}))
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("instructors must not pass platform-admin dependency")


def test_production_config_rejects_development_secrets() -> None:
    try:
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="postgresql://user:password@localhost:5432/kukekodes",
            MONGODB_URI="mongodb://localhost:27017",
            JWT_SECRET="your-secret-key-change-in-production",
            AUTO_CREATE_TABLES=True,
            REDIS_URL=None,
            RESEND_API_KEY="",
            GEMINI_API_KEY="",
        )
    except ValueError as exc:
        assert "Invalid production configuration" in str(exc)
    else:
        raise AssertionError("production settings should reject development defaults")
