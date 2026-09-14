"""
SQLAlchemy models for Courses, Modules, and Lessons.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, Enum, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from app.db.postgres import Base


class SkillLevel(str, PyEnum):
    """Course skill level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseStatus(str, PyEnum):
    """Course publication status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class LessonStatus(str, PyEnum):
    """Lesson publication status."""
    DRAFT = "draft"
    PUBLISHED = "published"


class Course(Base):
    """Course model."""
    
    __tablename__ = "courses"
    
    # === PRIMARY KEY ===
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # === BASIC INFO ===
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    slug = Column(String(255), unique=True, nullable=True, index=True)
    
    # === METADATA ===
    tags = Column(ARRAY(String(50)), nullable=True)  # ["Python", "Beginner", "AI"]
    skill_level = Column(
        Enum(SkillLevel),
        default=SkillLevel.BEGINNER,
        nullable=False,
    )
    category = Column(String(100), nullable=True, index=True)
    
    # === INSTRUCTOR ===
    instructor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # === MEDIA ===
    cover_image_url = Column(String(500), nullable=True)  # Cloudinary URL
    thumbnail_url = Column(String(500), nullable=True)
    
    # === STATUS & VISIBILITY ===
    status = Column(
        Enum(CourseStatus),
        default=CourseStatus.DRAFT,
        nullable=False,
        index=True,
    )
    is_free = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # === CONTENT REQUIREMENTS ===
    required_modules_count = Column(Integer, default=0, nullable=False)
    required_lessons_count = Column(Integer, default=0, nullable=False)
    total_estimated_hours = Column(Integer, nullable=True)
    
    # === STATS ===
    total_enrollments = Column(Integer, default=0, nullable=False)
    average_rating = Column(String(5), nullable=True)  # "4.5"
    total_reviews = Column(Integer, default=0, nullable=False)
    
    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    
    # === RELATIONSHIPS ===
    instructor = relationship("User", back_populates="courses", foreign_keys=[instructor_id])
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    progress = relationship("UserProgress", back_populates="course", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="course", cascade="all, delete-orphan")
    
    # === INDEXES ===
    __table_args__ = (
        Index("idx_course_instructor_status", "instructor_id", "status"),
        Index("idx_course_status_created", "status", "created_at"),
        Index("idx_course_skill_level", "skill_level"),
    )
    
    def __repr__(self) -> str:
        return f"<Course {self.title} ({self.status})>"
    
    def is_published(self) -> bool:
        """Check if course is published."""
        return self.status == CourseStatus.PUBLISHED
    
    def can_publish(self) -> bool:
        """Check if course has minimum requirements to publish."""
        return (
            self.title and
            self.description and
            len(self.modules) >= 1 and
            any(len(m.lessons) >= 1 for m in self.modules)
        )


class Module(Base):
    """Module (Unit) within a course."""
    
    __tablename__ = "modules"
    
    # === PRIMARY KEY ===
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # === FOREIGN KEY ===
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # === CONTENT ===
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # === ORDERING ===
    order = Column(Integer, nullable=False)  # Sequence within course
    
    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    
    # === RELATIONSHIPS ===
    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan")
    
    # === INDEXES ===
    __table_args__ = (
        Index("idx_module_course_order", "course_id", "order"),
    )
    
    def __repr__(self) -> str:
        return f"<Module {self.title}>"


class Lesson(Base):
    """Individual lesson/video within a module."""
    
    __tablename__ = "lessons"
    
    # === PRIMARY KEY ===
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # === FOREIGN KEY ===
    module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # === CONTENT ===
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # === YOUTUBE VIDEO ===
    youtube_url = Column(String(500), nullable=True)  # Full YouTube URL
    youtube_video_id = Column(String(50), nullable=True, index=True)  # Extracted video ID
    duration_minutes = Column(Integer, nullable=True)  # Auto-fetched from YouTube
    thumbnail_url = Column(String(500), nullable=True)  # YouTube thumbnail
    transcript = Column(Text, nullable=True)  # Optional transcript
    
    # === RESOURCES ===
    resources = Column(JSON, nullable=True)  # {"links": [...], "files": [...]}
    
    # === ORDERING ===
    order = Column(Integer, nullable=False)  # Sequence within module
    
    # === STATUS ===
    status = Column(
        Enum(LessonStatus),
        default=LessonStatus.DRAFT,
        nullable=False,
    )
    
    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    
    # === RELATIONSHIPS ===
    module = relationship("Module", back_populates="lessons")
    progress = relationship("UserProgress", back_populates="lesson", cascade="all, delete-orphan")
    
    # === INDEXES ===
    __table_args__ = (
        Index("idx_lesson_module_order", "module_id", "order"),
        Index("idx_lesson_youtube_id", "youtube_video_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Lesson {self.title}>"
    
    def is_published(self) -> bool:
        """Check if lesson is published."""
        return self.status == LessonStatus.PUBLISHED
