"""
Pydantic models for user profiles and dashboard.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


# ============================================================================
# REQUEST MODELS
# ============================================================================

class UpdateProfileRequest(BaseModel):
    """Request to update user profile."""
    
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    preferred_language: Optional[str] = Field(None, max_length=10)
    
    class Config:
        example = {
            "first_name": "John",
            "last_name": "Doe",
            "bio": "Learning to code with Kukekodes!",
            "country": "Nigeria",
            "timezone": "Africa/Lagos",
            "preferred_language": "en",
        }


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class UserProfileResponse(BaseModel):
    """User profile response."""
    
    user_id: UUID
    email: str
    first_name: str
    last_name: str
    username: Optional[str]
    bio: Optional[str]
    profile_picture_url: Optional[str]
    country: Optional[str]
    timezone: str
    preferred_language: str
    role: str
    created_at: str
    last_login_at: Optional[str]
    is_email_verified: bool
    learning_goals: Optional[str]
    current_job_title: Optional[str]
    company: Optional[str]


class CourseProgressItem(BaseModel):
    """Course in dashboard."""
    
    course_id: UUID
    course_title: str
    cover_image_url: Optional[str]
    completion_percentage: float
    is_completed: bool
    enrolled_at: str


class BadgeItem(BaseModel):
    """Badge/achievement."""
    
    id: UUID
    name: str
    icon_url: Optional[str]


class StreakItem(BaseModel):
    """User streak."""
    
    current: int
    longest: int
    fire_emoji: str


class DashboardStatistics(BaseModel):
    """User statistics."""
    
    total_courses_enrolled: int
    total_courses_completed: int
    total_lessons_completed: int
    total_time_spent_hours: float
    badges_earned: int


class UserDashboardResponse(BaseModel):
    """Complete user dashboard."""
    
    user_id: UUID
    user_name: str
    profile_picture_url: Optional[str]
    in_progress_courses: int
    completed_courses: int
    enrolled_courses: List[CourseProgressItem]
    streak: StreakItem
    recent_achievements: List[BadgeItem]
    statistics: DashboardStatistics


class EnrolledCourseDetailResponse(BaseModel):
    """Detailed enrolled course."""
    
    course_id: UUID
    course_title: str
    course_description: str
    cover_image_url: Optional[str]
    skill_level: str
    completion_percentage: float
    is_completed: bool
    enrolled_at: str
    completed_at: Optional[str]
    current_module_id: Optional[str]
    current_lesson_id: Optional[str]
    lessons_completed: int
    total_lessons: int


class PublicProfileBadge(BaseModel):
    """Badge in public profile."""
    
    id: UUID
    name: str
    icon_url: Optional[str]


class PublicProfileResponse(BaseModel):
    """Public user profile."""
    
    user_id: UUID
    user_name: str
    profile_picture_url: Optional[str]
    bio: Optional[str]
    country: Optional[str]
    is_public: bool
    completed_courses: int
    current_streak_days: int
    longest_streak_days: int
    badges_earned: List[PublicProfileBadge]