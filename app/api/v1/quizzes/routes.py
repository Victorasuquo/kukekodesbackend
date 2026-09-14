"""Mounted quiz endpoints for authors and enrolled learners."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.quizzes.schemas import (
    QuizAttemptRequest,
    QuizAttemptResponse,
    QuizCreateRequest,
    QuizResponse,
    QuizSummaryResponse,
)
from app.api.v1.quizzes.service import QuizService
from app.db.postgres import get_db
from app.dependencies import get_instructor_user, get_student_user


router = APIRouter(prefix="/api/v1/quizzes", tags=["Quizzes"])


@router.post("", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    request: QuizCreateRequest,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
):
    return QuizService.serialize(QuizService.create(db, request, current_user), include_correct=True)


@router.get("/course/{course_id}", response_model=List[QuizSummaryResponse])
async def list_course_quizzes(
    course_id: str,
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    QuizService.require_course_access(db, course_id, current_user)
    quizzes = QuizService.list_for_course(db, course_id)
    return [
        {
            "id": str(quiz.id),
            "course_id": str(quiz.course_id),
            "title": quiz.title,
            "passing_score": quiz.passing_score,
            "is_published": quiz.is_published,
            "question_count": len(quiz.questions),
        }
        for quiz in quizzes
    ]


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: str,
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    quiz = QuizService.get_for_learner(db, quiz_id)
    QuizService.require_course_access(db, str(quiz.course_id), current_user)
    return QuizService.serialize(quiz, include_correct=False)


@router.post("/{quiz_id}/attempts", response_model=QuizAttemptResponse, status_code=status.HTTP_201_CREATED)
async def submit_quiz_attempt(
    quiz_id: str,
    request: QuizAttemptRequest,
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    return QuizService.submit(db, quiz_id, current_user.get("sub"), request.answers)
