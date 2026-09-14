"""Phase 2 contract checks that do not require external services."""

import pytest
from pydantic import ValidationError

from app.api.v1.quizzes.schemas import QuizCreateRequest
from app.main import app


def test_openapi_exposes_complete_learning_journey() -> None:
    paths = app.openapi()["paths"]

    required_paths = {
        "/api/v1/admin/courses",
        "/api/v1/courses",
        "/api/v1/courses/{course_id}",
        "/api/v1/courses/{course_id}/publish",
        "/api/v1/modules",
        "/api/v1/lessons",
        "/api/v1/enrollments",
        "/api/v1/enrollments/check/{course_id}",
        "/api/v1/progress/course/{course_id}",
        "/api/v1/progress/mark-lesson-complete/{lesson_id}",
        "/api/v1/quizzes",
        "/api/v1/quizzes/course/{course_id}",
        "/api/v1/quizzes/{quiz_id}",
        "/api/v1/quizzes/{quiz_id}/attempts",
        "/api/v1/progress/certificate/{course_id}",
        "/api/v1/progress/verify-certificate/{verification_code}",
    }

    assert required_paths.issubset(paths)


def test_learner_quiz_contract_does_not_require_correct_answers() -> None:
    schema = app.openapi()["components"]["schemas"]["QuizAnswerResponse"]

    assert "is_correct" not in schema.get("required", [])


def test_quiz_authoring_requires_a_correct_answer() -> None:
    with pytest.raises(ValidationError, match="at least one correct answer"):
        QuizCreateRequest.model_validate(
            {
                "course_id": "00000000-0000-0000-0000-000000000001",
                "title": "Course check",
                "questions": [
                    {
                        "question_text": "Which choice is correct?",
                        "answers": [
                            {"answer_text": "First", "is_correct": False},
                            {"answer_text": "Second", "is_correct": False},
                        ],
                    }
                ],
            }
        )


def test_quiz_passing_score_is_bounded() -> None:
    with pytest.raises(ValidationError):
        QuizCreateRequest.model_validate(
            {
                "course_id": "00000000-0000-0000-0000-000000000001",
                "title": "Course check",
                "passing_score": 101,
                "questions": [
                    {
                        "question_text": "Which choice is correct?",
                        "answers": [
                            {"answer_text": "First", "is_correct": True},
                            {"answer_text": "Second", "is_correct": False},
                        ],
                    }
                ],
            }
        )
