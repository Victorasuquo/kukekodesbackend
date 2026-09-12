"""
SQLAlchemy models for the Kukekodes platform.
"""

# User models
from app.models.user import User, UserProfile, UserRole

# Course models (includes Module and Lesson)
from app.models.course import Course, Module, Lesson, SkillLevel, CourseStatus, LessonStatus

# Enrollment models
from app.models.enrollment import Enrollment, UserProgress

# Progress/Gamification models
from app.models.progress import Streak, Badge, BadgeAward, Leaderboard

# Notification models
from app.models.notification import Notification, NotificationPreference, NotificationType

# Community models (if exists)
try:
    from app.models.community import ForumThread, ForumReply
except ImportError:
    pass

__all__ = [
    # User
    "User",
    "UserProfile",
    "UserRole",
    # Course
    "Course",
    "Module",
    "Lesson",
    "SkillLevel",
    "CourseStatus",
    "LessonStatus",
    # Enrollment
    "Enrollment",
    "UserProgress",
    # Gamification
    "Streak",
    "Badge",
    "BadgeAward",
    "Leaderboard",
    # Notifications
    "Notification",
    "NotificationPreference",
    "NotificationType",
]
