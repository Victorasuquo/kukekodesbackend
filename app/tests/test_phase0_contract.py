import asyncio

from fastapi import HTTPException

from app.config import Settings
from app.main import app
from app.api.v1.auth.service import AuthService
from app.security import create_access_token, get_current_admin, verify_token


def test_openapi_has_canonical_phase0_routes() -> None:
    schema = app.openapi()
    paths = schema["paths"]

    for path in [
        "/livez",
        "/readyz",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/session",
        "/api/v1/auth/recovery/request",
        "/api/v1/admin/auth/login",
        "/api/v1/organizations",
        "/api/v1/organizations/{organization_id}/memberships",
        "/api/v1/organizations/{organization_id}/memberships/by-learner-id",
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


def test_admin_dependency_requires_admin_audience() -> None:
    token = create_access_token(
        user_id="u1",
        email="admin@example.com",
        role="admin",
        audience="learner",
    )
    payload = asyncio.run(verify_token(token))

    try:
        asyncio.run(get_current_admin(payload))
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("platform admins must use admin-audience sessions")


def test_admin_dependency_accepts_admin_audience() -> None:
    token = create_access_token(
        user_id="u1",
        email="admin@example.com",
        role="admin",
        audience="admin",
    )
    payload = asyncio.run(verify_token(token))

    assert asyncio.run(get_current_admin(payload))["aud"] == "admin"


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


def test_token_hash_is_deterministic_and_not_plaintext() -> None:
    raw_token = "not-the-value-stored-in-the-database"
    token_hash = AuthService.token_hash(raw_token)

    assert token_hash == AuthService.token_hash(raw_token)
    assert token_hash != raw_token
    assert len(token_hash) == 64


def test_recovery_contract_requires_learner_id_and_contact_email() -> None:
    schema = app.openapi()
    recovery_schema = schema["components"]["schemas"]["PasswordResetRequest"]

    assert set(recovery_schema["required"]) == {"contact_email", "learner_id"}
