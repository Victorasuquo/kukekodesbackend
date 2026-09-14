"""
SQLAlchemy models for Enrollment and Progress tracking.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.postgres import Base


# ============================================================================
# ENROLLMENT MODEL
# ============================================================================

class Enrollment(Base):
    """User enrollment in a course."""
    
    __tablename__ = "enrollments"
    
    # === PRIMARY KEY ===
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # === FOREIGN KEYS ===
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # === PROGRESS TRACKING ===
    completion_percentage = Column(Float, default=0.0, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False, index=True)
    
    # === CURRENT POSITION ===
    current_module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    current_lesson_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # === TIME TRACKING ===
    total_time_spent_minutes = Column(Integer, default=0, nullable=False)
    
    # === TIMESTAMPS ===
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # === RELATIONSHIPS ===
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    
    # === CONSTRAINTS ===
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_user_course_enrollment"),
        Index("idx_enrollment_user_completed", "user_id", "is_completed"),
        Index("idx_enrollment_course_enrolled", "course_id", "enrolled_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Enrollment {self.user_id} -> {self.course_id}>"
    
    def update_progress(self, completed_lessons: int, total_lessons: int) -> None:
        """Update enrollment progress percentage."""
        if total_lessons > 0:
            self.completion_percentage = (completed_lessons / total_lessons) * 100
            self.is_completed = self.completion_percentage >= 100.0
            if self.is_completed and not self.completed_at:
                self.completed_at = datetime.utcnow()


# ============================================================================
# USER PROGRESS MODEL
# ============================================================================

class UserProgress(Base):
    """Track user's progress through individual lessons."""
    
    __tablename__ = "user_progress"
    
    # === PRIMARY KEY ===
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # === FOREIGN KEYS ===
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    lesson_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # === COMPLETION TRACKING ===
    is_completed = Column(Boolean, default=False, nullable=False, index=True)
    
    # === TIME TRACKING ===
    time_spent_minutes = Column(Integer, default=0, nullable=False)
    resume_position_seconds = Column(Integer, default=0, nullable=False)
    last_idempotency_key = Column(String(128), nullable=True)
    
    # === QUIZ/ASSESSMENT TRACKING ===
    quiz_score = Column(Float, nullable=True)  # Percentage: 0-100
    quiz_attempts = Column(Integer, default=0, nullable=False)
    
    # === TIMESTAMPS ===
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    watched_at = Column(DateTime, nullable=True)  # When user first watched
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # === RELATIONSHIPS ===
    user = relationship("User", back_populates="progress")
    lesson = relationship("Lesson", back_populates="progress")
    course = relationship("Course", back_populates="progress")
    
    # === CONSTRAINTS ===
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),
        Index("idx_progress_user_course_completed", "user_id", "course_id", "is_completed"),
        Index("idx_progress_lesson_completed", "lesson_id", "is_completed"),
        Index("idx_progress_user_idempotency", "user_id", "last_idempotency_key"),
    )
    
    def __repr__(self) -> str:
        return f"<UserProgress {self.user_id} -> {self.lesson_id}>"
    
    def mark_complete(self, time_spent: int = 0) -> None:
        """Mark lesson as complete."""
        self.is_completed = True
        self.completed_at = datetime.utcnow()
        if time_spent > 0:
            self.time_spent_minutes = time_spent
    
    def get_status_emoji(self) -> str:
        """Get emoji representation of progress."""
        if self.is_completed:
            return "✅"
        elif self.watched_at:
            return "🕐"
        else:
            return "🔲"
