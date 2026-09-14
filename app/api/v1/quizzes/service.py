"""Quiz authoring, delivery, and scoring services."""

from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.assessment import Quiz, QuizAnswer, QuizAttempt, QuizQuestion
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.utils.exceptions import NotFoundError, ValidationError


class QuizService:
    @staticmethod
    def _uuid(value: str) -> UUID:
        try:
            return UUID(str(value))
        except (TypeError, ValueError) as exc:
            raise ValidationError("Invalid identifier") from exc

    @staticmethod
    def _get(db: Session, quiz_id: str) -> Quiz:
        quiz = (
            db.query(Quiz)
            .options(joinedload(Quiz.questions).joinedload(QuizQuestion.answers))
            .filter(Quiz.id == QuizService._uuid(quiz_id))
            .first()
        )
        if not quiz:
            raise NotFoundError(f"Quiz with ID {quiz_id} not found")
        return quiz

    @staticmethod
    def serialize(quiz: Quiz, include_correct: bool = False) -> Dict[str, Any]:
        return {
            "id": str(quiz.id),
            "course_id": str(quiz.course_id),
            "title": quiz.title,
            "passing_score": quiz.passing_score,
            "is_published": quiz.is_published,
            "created_at": quiz.created_at,
            "questions": [
                {
                    "id": str(question.id),
                    "question_text": question.question_text,
                    "order": question.order,
                    "answers": [
                        {
                            "id": str(answer.id),
                            "answer_text": answer.answer_text,
                            "is_correct": answer.is_correct if include_correct else None,
                        }
                        for answer in question.answers
                    ],
                }
                for question in sorted(quiz.questions, key=lambda item: item.order)
            ],
        }

    @staticmethod
    def create(db: Session, payload, actor: Dict[str, Any]) -> Quiz:
        course = db.query(Course).filter(Course.id == QuizService._uuid(payload.course_id)).first()
        if not course:
            raise NotFoundError(f"Course with ID {payload.course_id} not found")
        if actor.get("role") != "admin" and str(course.instructor_id) != str(actor.get("sub")):
            raise ValidationError("You can only add quizzes to courses you manage")

        quiz = Quiz(
            course_id=course.id,
            title=payload.title,
            passing_score=payload.passing_score,
            is_published=payload.is_published,
        )
        db.add(quiz)
        db.flush()
        for question_order, question_payload in enumerate(payload.questions, start=1):
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=question_payload.question_text,
                order=question_order,
            )
            db.add(question)
            db.flush()
            for answer_payload in question_payload.answers:
                db.add(QuizAnswer(
                    question_id=question.id,
                    answer_text=answer_payload.answer_text,
                    is_correct=answer_payload.is_correct,
                ))
        db.commit()
        return QuizService._get(db, str(quiz.id))

    @staticmethod
    def get_for_learner(db: Session, quiz_id: str) -> Quiz:
        quiz = QuizService._get(db, quiz_id)
        if not quiz.is_published:
            raise NotFoundError(f"Quiz with ID {quiz_id} not found")
        return quiz

    @staticmethod
    def list_for_course(db: Session, course_id: str, include_drafts: bool = False) -> List[Quiz]:
        query = db.query(Quiz).filter(Quiz.course_id == QuizService._uuid(course_id))
        if not include_drafts:
            query = query.filter(Quiz.is_published.is_(True))
        return query.order_by(Quiz.created_at).all()

    @staticmethod
    def require_course_access(db: Session, course_id: str, actor: Dict[str, Any]) -> None:
        course = db.query(Course).filter(Course.id == QuizService._uuid(course_id)).first()
        if not course:
            raise NotFoundError(f"Course with ID {course_id} not found")
        if actor.get("role") == "admin" or str(course.instructor_id) == str(actor.get("sub")):
            return
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == QuizService._uuid(actor.get("sub")),
            Enrollment.course_id == course.id,
        ).first()
        if not enrollment:
            raise ValidationError("Enroll in this course before viewing its quizzes")

    @staticmethod
    def all_required_passed(db: Session, user_id: str, course_id: str) -> bool:
        quizzes = QuizService.list_for_course(db, course_id)
        return all(
            db.query(QuizAttempt).filter(
                QuizAttempt.quiz_id == quiz.id,
                QuizAttempt.user_id == QuizService._uuid(user_id),
                QuizAttempt.passed.is_(True),
            ).first() is not None
            for quiz in quizzes
        )

    @staticmethod
    def submit(db: Session, quiz_id: str, user_id: str, submitted_answers: Dict[str, str]) -> Dict[str, Any]:
        quiz = QuizService.get_for_learner(db, quiz_id)
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == QuizService._uuid(user_id),
            Enrollment.course_id == quiz.course_id,
        ).first()
        if not enrollment:
            raise ValidationError("Enroll in this course before submitting its quiz")

        correct_count = 0
        normalized_answers: Dict[str, str] = {}
        for question in quiz.questions:
            question_id = str(question.id)
            selected_id = submitted_answers.get(question_id)
            if not selected_id:
                raise ValidationError("Every quiz question must be answered")
            selected = next((answer for answer in question.answers if str(answer.id) == selected_id), None)
            if not selected:
                raise ValidationError("An answer does not belong to its question")
            normalized_answers[question_id] = selected_id
            if selected.is_correct:
                correct_count += 1

        total = len(quiz.questions)
        score = round((correct_count / total) * 100, 2) if total else 0.0
        attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_id=QuizService._uuid(user_id),
            answers=normalized_answers,
            score=score,
            passed=score >= quiz.passing_score,
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return {
            "id": str(attempt.id),
            "quiz_id": str(quiz.id),
            "score": attempt.score,
            "passed": attempt.passed,
            "correct_count": correct_count,
            "total_questions": total,
            "submitted_at": attempt.submitted_at,
            "certificate_available": enrollment.is_completed and QuizService.all_required_passed(db, user_id, str(quiz.course_id)),
        }
