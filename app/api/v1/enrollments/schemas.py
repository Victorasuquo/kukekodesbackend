"""
Enrollment schemas for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class EnrollCourseRequest(BaseModel):
    """Request to enroll in a course."""
    course_id: str = Field(..., description="Course ID to enroll in")


class UnenrollRequest(BaseModel):
    """Request to unenroll from a course."""
    course_id: str = Field(..., description="Course ID to unenroll from")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class EnrollmentResponse(BaseModel):
    """Single enrollment response."""
    id: UUID
    user_id: UUID
    course_id: UUID
    course_title: str
    course_cover_url: Optional[str] = None
    enrolled_at: datetime
    is_completed: bool = False
    completion_percentage: float = 0.0
    completed_at: Optional[datetime] = None
    current_module_id: Optional[UUID] = None
    current_lesson_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class EnrollmentListItem(BaseModel):
    """Enrollment item in list."""
    id: UUID
    course_id: UUID
    course_title: str
    course_cover_url: Optional[str] = None
    enrolled_at: datetime
    is_completed: bool
    completion_percentage: float
    completed_at: Optional[datetime] = None


class UserEnrollmentsResponse(BaseModel):
    """List of user's enrollments."""
    user_id: UUID
    total_enrollments: int
    in_progress_count: int
    completed_count: int
    enrollments: List[EnrollmentListItem]


class EnrollmentStatusResponse(BaseModel):
    """Enrollment status for a specific course."""
    is_enrolled: bool
    enrollment: Optional[EnrollmentResponse] = None
    can_enroll: bool = True
    message: Optional[str] = None
