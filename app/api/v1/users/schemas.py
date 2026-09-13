"""
User profile schemas for API endpoints.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class UpdateProfileRequest(BaseModel):
    """Request to update user profile."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    preferred_language: Optional[str] = Field(None, max_length=10)
    profile_picture_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Request to change password."""
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class NotificationPreferencesRequest(BaseModel):
    """Request to update notification preferences."""
    all_emails_enabled: Optional[bool] = None
    email_on_lesson_complete: Optional[bool] = None
    email_on_course_complete: Optional[bool] = None
    email_on_badge_earned: Optional[bool] = None
    email_on_streak_milestone: Optional[bool] = None
    receive_weekly_summary: Optional[bool] = None
    weekly_summary_day: Optional[str] = None


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class UserProfileResponse(BaseModel):
    """User profile response."""
    user_id: str
    learner_id: str
    email: str
    contact_email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None
    country: Optional[str] = None
    timezone: str = "UTC"
    preferred_language: str = "en"
    role: str
    created_at: str
    last_login_at: Optional[str] = None
    is_email_verified: bool = False
    learning_goals: Optional[str] = None
    current_job_title: Optional[str] = None
    company: Optional[str] = None


class EnrolledCourseItem(BaseModel):
    """Enrolled course in dashboard."""
    course_id: str
    course_title: str
    cover_image_url: Optional[str] = None
    completion_percentage: float
    is_completed: bool
    enrolled_at: str


class BadgeItem(BaseModel):
    """Badge item."""
    id: str
    name: str
    icon_url: Optional[str] = None
    earned_at: Optional[str] = None


class StreakInfo(BaseModel):
    """User streak information."""
    current: int
    longest: int
    fire_emoji: str = "🔲"


class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_courses_enrolled: int
    total_courses_completed: int
    total_lessons_completed: int
    total_time_spent_hours: float
    badges_earned: int


class UserDashboardResponse(BaseModel):
    """User dashboard response."""
    user_id: str
    user_name: str
    profile_picture_url: Optional[str] = None
    in_progress_courses: int
    completed_courses: int
    enrolled_courses: List[EnrolledCourseItem]
    streak: StreakInfo
    recent_achievements: List[BadgeItem]
    statistics: DashboardStats


class PublicProfileResponse(BaseModel):
    """Public user profile."""
    user_id: str
    user_name: str
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    is_public: bool
    completed_courses: Optional[int] = None
    current_streak_days: Optional[int] = None
    longest_streak_days: Optional[int] = None
    badges_earned: Optional[List[BadgeItem]] = None
    message: Optional[str] = None


class NotificationPreferencesResponse(BaseModel):
    """Notification preferences response."""
    all_emails_enabled: bool = True
    email_on_lesson_complete: bool = True
    email_on_course_complete: bool = True
    email_on_badge_earned: bool = True
    email_on_streak_milestone: bool = True
    email_on_course_update: bool = False
    email_on_reply: bool = True
    receive_weekly_summary: bool = True
    weekly_summary_day: str = "Sunday"
