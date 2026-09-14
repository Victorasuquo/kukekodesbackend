"""Phase 3 API boundary checks.

These tests intentionally exercise only the public contract.  They let the
backend and frontend workstreams converge on the same routes before a
provider (MongoDB, Gemini, or YouTube) is available in CI.
"""

from app.main import app


def test_openapi_exposes_phase3_product_routes() -> None:
    paths = app.openapi()["paths"]
    required_paths = {
        "/api/v1/community/threads",
        "/api/v1/community/threads/{thread_id}",
        "/api/v1/community/threads/{thread_id}/replies",
        "/api/v1/community/reports",
        "/api/v1/community/blocks",
        "/api/v1/ai/coach",
        "/api/v1/live-sessions",
        "/api/v1/live-sessions/{session_id}/join",
        "/api/v1/live-sessions/{session_id}/attendance",
        "/api/v1/code/submissions",
        "/api/v1/code/submissions/{submission_id}",
    }

    assert required_paths.issubset(paths)


def test_phase3_operation_ids_remain_unique() -> None:
    operations = [
        operation.get("operationId")
        for path in app.openapi()["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and operation.get("operationId")
    ]

    assert len(operations) == len(set(operations))

