"""
SQLAlchemy models for Notifications.
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from app.db.postgres import Base


# ============================================================================
# NOTIFICATION TYPES
# ============================================================================

class NotificationType(str, PyEnum):
    """Types of notifications."""
    LESSON_COMPLETED = "lesson_completed"
    COURSE_COMPLETED = "course_completed"
    BADGE_EARNED = "badge_earned"
    STREAK_MILESTONE = "streak_milestone"
    ASSIGNMENT_DUE = "assignment_due"
    NEW_REPLY = "new_reply"
    COURSE_UPDATE = "course_update"
    REMINDER = "reminder"
    ACHIEVEMENT = "achievement"
    ENROLLMENT = "enrollment"
    OTHER = "other"


# ============================================================================
# NOTIFICATION MODEL
# ============================================================================

class Notification(Base):
    """User notifications."""
    
    __tablename__ = "notifications"
    
    # === PRIMARY KEY ===
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # === FOREIGN KEY ===
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # === NOTIFICATION CONTENT ===
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # === NOTIFICATION TYPE ===
    type = Column(
        SqlEnum(NotificationType),
        default=NotificationType.OTHER,
        nullable=False,
    )
    
    # === RELATED ENTITY (Optional) ===
    related_entity_id = Column(UUID(as_uuid=True), nullable=True)
    related_entity_type = Column(String(50), nullable=True)  # "course", "lesson", "badge"
    
    # === STATUS ===
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    is_sent = Column(Boolean, default=False, nullable=False)
    email_sent = Column(Boolean, default=False, nullable=False)
    
    # === EXTRA DATA ===
    extra_data = Column(JSON, nullable=True)  # Additional context (renamed from 'metadata' which is reserved)
    
    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # === INDEXES ===
    __table_args__ = (
        Index("idx_notification_user_read", "user_id", "is_read"),
        Index("idx_notification_created", "created_at"),
        Index("idx_notification_type", "type"),
    )
    
    # === RELATIONSHIPS ===
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self) -> str:
        return f"<Notification {self.title}>"
    
    def mark_as_read(self) -> None:
        """Mark notification as read."""
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def get_icon_emoji(self) -> str:
        """Get emoji for notification type."""
        emoji_map = {
            NotificationType.LESSON_COMPLETED: "✅",
            NotificationType.COURSE_COMPLETED: "🏆",
            NotificationType.BADGE_EARNED: "🎖️",
            NotificationType.STREAK_MILESTONE: "🔥",
            NotificationType.ASSIGNMENT_DUE: "⏰",
            NotificationType.NEW_REPLY: "💬",
            NotificationType.COURSE_UPDATE: "📢",
            NotificationType.REMINDER: "🔔",
            NotificationType.ACHIEVEMENT: "⭐",
            NotificationType.ENROLLMENT: "📚",
            NotificationType.OTHER: "📌",
        }
        return emoji_map.get(self.type, "📌")


# ============================================================================
# NOTIFICATION PREFERENCE MODEL
# ============================================================================

class NotificationPreference(Base):
    """User's notification preferences."""
    
    __tablename__ = "notification_preferences"
    
    # === PRIMARY KEY ===
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # === FOREIGN KEY ===
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    
    # === EMAIL NOTIFICATION PREFERENCES ===
    email_on_lesson_complete = Column(Boolean, default=True, nullable=False)
    email_on_course_complete = Column(Boolean, default=True, nullable=False)
    email_on_badge_earned = Column(Boolean, default=True, nullable=False)
    email_on_streak_milestone = Column(Boolean, default=True, nullable=False)
    email_on_course_update = Column(Boolean, default=False, nullable=False)
    email_on_reply = Column(Boolean, default=True, nullable=False)
    
    # === SUMMARY EMAILS ===
    receive_weekly_summary = Column(Boolean, default=True, nullable=False)
    weekly_summary_day = Column(String(10), default="Sunday", nullable=False)
    
    # === GENERAL SETTINGS ===
    all_emails_enabled = Column(Boolean, default=True, nullable=False)
    
    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # === RELATIONSHIPS ===
    user = relationship("User", back_populates="notification_preferences")
    
    def __repr__(self) -> str:
        return f"<NotificationPreference {self.user_id}>"
    
    def should_send_email(self, notification_type: NotificationType) -> bool:
        """Determine if email should be sent based on user preference."""
        if not self.all_emails_enabled:
            return False
        
        type_map = {
            NotificationType.LESSON_COMPLETED: self.email_on_lesson_complete,
            NotificationType.COURSE_COMPLETED: self.email_on_course_complete,
            NotificationType.BADGE_EARNED: self.email_on_badge_earned,
            NotificationType.STREAK_MILESTONE: self.email_on_streak_milestone,
            NotificationType.COURSE_UPDATE: self.email_on_course_update,
            NotificationType.NEW_REPLY: self.email_on_reply,
        }
        
        return type_map.get(notification_type, True)
