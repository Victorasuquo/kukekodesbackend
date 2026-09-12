"""
Notification schemas for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class NotificationTypeEnum(str, Enum):
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
# NOTIFICATION RESPONSES
# ============================================================================

class NotificationResponse(BaseModel):
    """Single notification response."""
    id: UUID
    title: str
    message: str
    type: NotificationTypeEnum
    is_read: bool
    related_entity_id: Optional[UUID] = None
    related_entity_type: Optional[str] = None
    icon_emoji: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """List of notifications with pagination."""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


class UnreadCountResponse(BaseModel):
    """Unread notification count."""
    unread_count: int


# ============================================================================
# NOTIFICATION ACTIONS
# ============================================================================

class MarkReadRequest(BaseModel):
    """Request to mark notifications as read."""
    notification_ids: List[UUID] = Field(..., min_length=1)


class MarkAllReadResponse(BaseModel):
    """Response for marking all as read."""
    marked_count: int
    message: str


# ============================================================================
# NOTIFICATION PREFERENCES
# ============================================================================

class NotificationPreferencesResponse(BaseModel):
    """User's notification preferences."""
    email_on_lesson_complete: bool = True
    email_on_course_complete: bool = True
    email_on_badge_earned: bool = True
    email_on_streak_milestone: bool = True
    email_on_course_update: bool = False
    email_on_reply: bool = True
    receive_weekly_summary: bool = True
    weekly_summary_day: str = "Sunday"
    all_emails_enabled: bool = True
    
    class Config:
        from_attributes = True


class UpdatePreferencesRequest(BaseModel):
    """Request to update notification preferences."""
    email_on_lesson_complete: Optional[bool] = None
    email_on_course_complete: Optional[bool] = None
    email_on_badge_earned: Optional[bool] = None
    email_on_streak_milestone: Optional[bool] = None
    email_on_course_update: Optional[bool] = None
    email_on_reply: Optional[bool] = None
    receive_weekly_summary: Optional[bool] = None
    weekly_summary_day: Optional[str] = None
    all_emails_enabled: Optional[bool] = None
