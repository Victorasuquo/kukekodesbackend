"""
SQLAlchemy models for the Kukekodes platform.
"""

# User models
from app.models.user import User, UserProfile, UserRole
from app.models.identity import (
    ConsentPurpose,
    ConsentRecord,
    Credential,
    GuardianRelationship,
    PasswordRecoveryToken,
    RefreshSession,
    SessionAudience,
)
from app.models.organization import (
    AssignmentState,
    Cohort,
    CohortMembership,
    CourseAssignment,
    MembershipStatus,
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    OrganizationRole,
    OrganizationStatus,
)

# Course models (includes Module and Lesson)
from app.models.course import Course, Module, Lesson, SkillLevel, CourseStatus, LessonStatus

# Enrollment models
from app.models.enrollment import Enrollment, UserProgress

# Progress/Gamification models
from app.models.progress import Streak, Badge, BadgeAward, Leaderboard

# Notification models
from app.models.notification import Notification, NotificationPreference, NotificationType
from app.models.assessment import Certificate, Quiz, QuizAnswer, QuizAttempt, QuizQuestion
from app.models.phase3 import LiveSession, LiveSessionAttendance, CodeExercise, CodeSubmission

# Community models (if exists)
from app.models.community import CommunityReport, CommunityBlock
from app.models.outbox import OutboxEvent

__all__ = [
    # User
    "User",
    "UserProfile",
    "UserRole",
    "Credential",
    "RefreshSession",
    "SessionAudience",
    "PasswordRecoveryToken",
    "GuardianRelationship",
    "ConsentRecord",
    "ConsentPurpose",
    "Organization",
    "OrganizationStatus",
    "OrganizationRole",
    "OrganizationMembership",
    "OrganizationInvitation",
    "MembershipStatus",
    "Cohort",
    "CohortMembership",
    "CourseAssignment",
    "AssignmentState",
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
    # Assessments and certificates
    "Quiz",
    "QuizQuestion",
    "QuizAnswer",
    "QuizAttempt",
    "Certificate",
    "CommunityReport",
    "OutboxEvent",
    "CommunityBlock",
    "LiveSession", "LiveSessionAttendance", "CodeExercise", "CodeSubmission",
]
