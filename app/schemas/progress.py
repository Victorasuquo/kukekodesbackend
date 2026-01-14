"""
Pydantic models for progress tracking.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID


# ============================================================================
# REQUEST MODELS
# ============================================================================

class MarkLessonCompleteRequest(BaseModel):
    """Request to mark lesson complete."""
    
    time_spent_minutes: int = Field(
        default=0,
        ge=0,
        le=1440,
        description="Time spent on lesson in minutes (max 24 hours)"
    )
    quiz_score: Optional[float] = Field(None, ge=0, le=100)
    
    class Config:
        example = {
            "time_spent_minutes": 15,
            "quiz_score": 85.5,
        }


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class UserProgressResponse(BaseModel):
    """User progress for a single lesson."""
    
    lesson_id: UUID
    is_completed: bool
    time_spent_minutes: int
    quiz_score: Optional[float]
    quiz_attempts: int
    started_at: Optional[str]
    completed_at: Optional[str]


class LessonProgressItem(BaseModel):
    """Lesson in module progress view."""
    
    id: UUID
    title: str
    order: int
    is_completed: bool


class ModuleProgressResponse(BaseModel):
    """User progress for a module."""
    
    module_id: UUID
    module_title: str
    completion_percentage: float
    completed_lessons: int
    total_lessons: int
    lessons: List[LessonProgressItem]


class CourseModuleProgress(BaseModel):
    """Module progress in course view."""
    
    module_id: UUID
    module_title: str
    completion_percentage: float
    completed_lessons: int
    total_lessons: int


class CourseProgressResponse(BaseModel):
    """User progress for a course."""
    
    course_id: UUID
    course_title: str
    completion_percentage: float
    is_completed: bool
    enrolled_at: str
    completed_at: Optional[str]
    current_module_id: Optional[str]
    current_lesson_id: Optional[str]
    modules: List[CourseModuleProgress]
    total_lessons: int
    completed_lessons: int
    time_spent_minutes: int
    estimated_remaining_minutes: int
    total_estimated_duration: int


class CourseProgressItem(BaseModel):
    """Course in user's dashboard."""
    
    course_id: UUID
    course_title: str
    cover_image_url: Optional[str]
    completion_percentage: float
    is_completed: bool
    enrolled_at: str
    progress_bar: int


class BadgeItem(BaseModel):
    """Badge/achievement."""
    
    id: UUID
    name: str
    icon_url: Optional[str]


class StreakResponse(BaseModel):
    """User's streak data."""
    
    current: int
    longest: int


class DashboardStatistics(BaseModel):
    """User statistics for dashboard."""
    
    total_courses_enrolled: int
    total_courses_completed: int
    total_lessons_completed: int
    total_time_spent_minutes: int
    badges_earned: int


class UserProgressDashboardResponse(BaseModel):
    """Complete user learning dashboard."""
    
    user_id: UUID
    user_name: str
    profile_picture_url: Optional[str]
    enrolled_courses: List[CourseProgressItem]
    streak: StreakResponse
    recent_badges: List[BadgeItem]
    statistics: DashboardStatistics


class UserStatsResponse(BaseModel):
    """User learning statistics."""
    
    total_courses_enrolled: int
    total_courses_completed: int
    total_lessons_completed: int
    total_time_spent_hours: float
    current_streak_days: int
    longest_streak_days: int
    total_badges: int
    xp_points: int


class LearningHistoryItem(BaseModel):
    """Single learning activity."""
    
    lesson_id: UUID
    lesson_title: str
    course_id: UUID
    course_title: str
    completed_at: Optional[str]
    time_spent_minutes: int


class LearningHistoryResponse(BaseModel):
    """User's learning activity history."""
    
    activities: List[LearningHistoryItem]
    total: int
    skip: int
    limit: int