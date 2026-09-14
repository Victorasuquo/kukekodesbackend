"""Request and response contracts for course quizzes."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class QuizAnswerCreateRequest(BaseModel):
    answer_text: str = Field(..., min_length=1, max_length=1000)
    is_correct: bool = False


class QuizQuestionCreateRequest(BaseModel):
    question_text: str = Field(..., min_length=3, max_length=2000)
    answers: List[QuizAnswerCreateRequest] = Field(..., min_length=2)

    @model_validator(mode="after")
    def require_correct_answer(self):
        if not any(answer.is_correct for answer in self.answers):
            raise ValueError("Each question must contain at least one correct answer")
        return self


class QuizCreateRequest(BaseModel):
    course_id: str
    title: str = Field(..., min_length=3, max_length=255)
    passing_score: int = Field(default=70, ge=0, le=100)
    is_published: bool = True
    questions: List[QuizQuestionCreateRequest] = Field(..., min_length=1)


class QuizAnswerResponse(BaseModel):
    id: str
    answer_text: str
    is_correct: Optional[bool] = None


class QuizQuestionResponse(BaseModel):
    id: str
    question_text: str
    order: int
    answers: List[QuizAnswerResponse]


class QuizResponse(BaseModel):
    id: str
    course_id: str
    title: str
    passing_score: int
    is_published: bool
    questions: List[QuizQuestionResponse]
    created_at: datetime


class QuizSummaryResponse(BaseModel):
    id: str
    course_id: str
    title: str
    passing_score: int
    is_published: bool
    question_count: int


class QuizAttemptRequest(BaseModel):
    answers: Dict[str, str] = Field(..., description="Map of question ID to selected answer ID")


class QuizAttemptResponse(BaseModel):
    id: str
    quiz_id: str
    score: float
    passed: bool
    correct_count: int
    total_questions: int
    submitted_at: datetime
    certificate_available: bool
