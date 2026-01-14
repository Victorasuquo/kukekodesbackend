"""
Pydantic models for enrollment.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


# ============================================================================
# REQUEST MODELS
# ============================================================================

class EnrollCourseRequest(BaseModel):
    """Request to enroll in course."""
    
    course_id: str = Field(..., description="Course ID")
    
    class Config:
        example = {
            "course_id": "uuid-here"
        }


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class EnrollmentResponse(BaseModel):
    """Enrollment response."""
    
    id: UUID
    user_id: UUID
    course_id: UUID
    course_title: str
    completion_percentage: float
    is_completed: bool
    enrolled_at: str
    completed_at: Optional[str]


class UserEnrollmentsResponse(BaseModel):
    """User's enrollments list."""
    
    data: List[EnrollmentResponse]
    total: int
    page: int
    page_size: int