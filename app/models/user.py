"""
SQLAlchemy models for User and Profile management.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from app.db.postgres import Base


class UserRole(str, PyEnum):
    """User roles in the system."""
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


class User(Base):
    """User account model."""
    
    __tablename__ = "users"
    
    # === PRIMARY KEY ===
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # === AUTHENTICATION ===
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # === PROFILE ===
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    bio = Column(Text, nullable=True)
    profile_picture_url = Column(String(500), nullable=True)  # Cloudinary URL
    
    # === LOCATION & PREFERENCES ===
    country = Column(String(100), nullable=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    preferred_language = Column(String(10), default="en", nullable=False)
    
    # === ROLE & PERMISSIONS ===
    role = Column(
        Enum(UserRole),
        default=UserRole.STUDENT,
        nullable=False,
        index=True,
    )
    
    # === ACCOUNT STATUS ===
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    
    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    # === RELATIONSHIPS ===
    courses = relationship("Course", back_populates="instructor", foreign_keys="Course.instructor_id")
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("Badge", secondary="user_badges", back_populates="users")
    forum_threads = relationship("ForumThread", back_populates="user", cascade="all, delete-orphan")
    forum_replies = relationship("ForumReply", back_populates="user", cascade="all, delete-orphan")
    
    # === INDEXES ===
    __table_args__ = (
        Index("idx_user_email_active", "email", "is_active"),
        Index("idx_user_role", "role"),
        Index("idx_user_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
    
    def get_full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email
    
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
    
    def is_instructor(self) -> bool:
        """Check if user is instructor."""
        return self.role == UserRole.INSTRUCTOR
    
    def is_student(self) -> bool:
        """Check if user is student."""
        return self.role == UserRole.STUDENT


class UserProfile(Base):
    """Extended user profile information (optional, for future use)."""
    
    __tablename__ = "user_profiles"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
    )
    
    # === PROFESSIONAL INFO ===
    current_job_title = Column(String(200), nullable=True)
    company = Column(String(200), nullable=True)
    years_of_experience = Column(String(50), nullable=True)
    
    # === LEARNING GOALS ===
    learning_goals = Column(Text, nullable=True)  # JSON array as text
    target_career = Column(String(200), nullable=True)
    
    # === NOTIFICATION PREFERENCES ===
    email_notifications_enabled = Column(Boolean, default=True, nullable=False)
    receive_weekly_summary = Column(Boolean, default=True, nullable=False)
    receive_achievement_notifications = Column(Boolean, default=True, nullable=False)
    
    # === PRIVACY ===
    profile_is_public = Column(Boolean, default=False, nullable=False)
    show_badges_publicly = Column(Boolean, default=False, nullable=False)
    
    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<UserProfile {self.user_id}>"