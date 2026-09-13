"""Fail CI when the FastAPI application cannot produce a valid API contract."""

from app.main import app


REQUIRED_PATHS = {
    "/livez",
    "/readyz",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
    "/api/v1/auth/logout-all",
    "/api/v1/auth/recovery/request",
    "/api/v1/auth/recovery/confirm",
    "/api/v1/auth/session",
    "/api/v1/admin/auth/login",
    "/api/v1/admin/auth/refresh",
    "/api/v1/admin/auth/logout",
    "/api/v1/admin/dashboard/overview",
    "/api/v1/organizations",
    "/api/v1/organizations/{organization_id}/memberships",
    "/api/v1/organizations/{organization_id}/memberships/by-learner-id",
    "/api/v1/organizations/{organization_id}/invitations",
    "/api/v1/organizations/{organization_id}/cohorts",
    "/api/v1/organizations/{organization_id}/assignments",
    "/api/v1/courses",
    "/api/v1/modules",
    "/api/v1/lessons",
}


def main() -> None:
    schema = app.openapi()
    paths = schema.get("paths", {})
    missing = sorted(REQUIRED_PATHS.difference(paths))
    if missing:
        raise SystemExit(f"OpenAPI contract is missing required paths: {missing}")

    operation_ids: list[str] = []
    for operations in paths.values():
        for operation in operations.values():
            if isinstance(operation, dict) and operation.get("operationId"):
                operation_ids.append(operation["operationId"])

    duplicates = sorted(
        operation_id
        for operation_id in set(operation_ids)
        if operation_ids.count(operation_id) > 1
    )
    if duplicates:
        raise SystemExit(f"OpenAPI contract has duplicate operation IDs: {duplicates}")

    print(f"OpenAPI contract OK: {len(paths)} paths, {len(operation_ids)} operations")


if __name__ == "__main__":
    main()
