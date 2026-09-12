"""
Progress tracking schemas for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class MarkLessonCompleteRequest(BaseModel):
    """Request to mark a lesson as complete."""
    time_spent_minutes: int = Field(default=0, ge=0, description="Time spent on lesson in minutes")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ProgressResponse(BaseModel):
    """General progress response."""
    user_id: UUID
    course_id: Optional[UUID] = None
    module_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    is_completed: bool
    completion_percentage: float
    time_spent_minutes: int = 0


class UserProgressResponse(BaseModel):
    """User progress for a specific lesson."""
    user_id: UUID
    lesson_id: UUID
    module_id: UUID
    course_id: UUID
    is_completed: bool
    completed_at: Optional[datetime] = None
    time_spent_minutes: int = 0
    
    class Config:
        from_attributes = True


class ModuleProgressResponse(BaseModel):
    """User progress for a module."""
    module_id: UUID
    module_title: str
    total_lessons: int
    completed_lessons: int
    completion_percentage: float
    lessons: List[Dict[str, Any]] = []


class CourseProgressResponse(BaseModel):
    """User progress for a course."""
    user_id: UUID
    course_id: UUID
    course_title: str
    total_modules: int
    completed_modules: int
    total_lessons: int
    completed_lessons: int
    completion_percentage: float
    is_completed: bool
    current_module: Optional[Dict[str, Any]] = None
    current_lesson: Optional[Dict[str, Any]] = None
    estimated_time_remaining_hours: Optional[float] = None
    modules: List[ModuleProgressResponse] = []


class EnrolledCourseItem(BaseModel):
    """Enrolled course in dashboard."""
    course_id: UUID
    course_title: str
    cover_image_url: Optional[str] = None
    completion_percentage: float
    is_completed: bool
    enrolled_at: datetime


class StreakData(BaseModel):
    """User streak information."""
    current: int
    longest: int
    fire_emoji: str = "🔲"


class BadgeItem(BaseModel):
    """Badge information."""
    id: UUID
    name: str
    icon_url: Optional[str] = None
    earned_at: Optional[datetime] = None


class StatsData(BaseModel):
    """User statistics."""
    total_courses_enrolled: int
    total_courses_completed: int
    total_lessons_completed: int
    total_time_spent_hours: float
    badges_earned: int


class UserProgressDashboardResponse(BaseModel):
    """Complete user progress dashboard."""
    user_id: UUID
    user_name: str
    profile_picture_url: Optional[str] = None
    enrolled_courses: List[Dict[str, Any]] = []
    streak: StreakData
    recent_badges: List[Dict[str, Any]] = []
    statistics: StatsData


class LearningHistoryItem(BaseModel):
    """Single learning history item."""
    lesson_id: UUID
    lesson_title: str
    course_title: str
    completed_at: datetime
    time_spent_minutes: int


class LearningHistoryResponse(BaseModel):
    """Paginated learning history."""
    total: int
    page: int
    page_size: int
    items: List[LearningHistoryItem]
