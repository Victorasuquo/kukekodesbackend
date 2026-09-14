"""
Pydantic models for course, module, and lesson endpoints.
"""

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Any, Dict, Optional, List
from uuid import UUID
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class SkillLevelEnum(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseStatusEnum(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class LessonStatusEnum(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


# ============================================================================
# LESSON SCHEMAS
# ============================================================================

class LessonCreateRequest(BaseModel):
    """Request to create a lesson."""
    
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    youtube_url: str = Field(..., description="Full YouTube URL")
    duration_minutes: Optional[int] = Field(None, ge=0)
    transcript: Optional[str] = None
    resources: Optional[Dict[str, Any]] = None
    order: int = Field(..., ge=1, description="Order within module")
    
    class Config:
        example = {
            "title": "What is Machine Learning?",
            "description": "Introduction to ML concepts",
            "youtube_url": "https://www.youtube.com/watch?v=something",
            "order": 1,
        }


class LessonUpdateRequest(BaseModel):
    """Request to update a lesson."""
    
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    youtube_url: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    transcript: Optional[str] = None
    resources: Optional[Dict[str, Any]] = None
    order: Optional[int] = Field(None, ge=1)
    expected_version: Optional[int] = Field(None, ge=1)


class LessonResponse(BaseModel):
    """Lesson response."""
    
    id: UUID
    module_id: UUID
    title: str
    description: Optional[str]
    youtube_url: Optional[str]
    youtube_video_id: Optional[str]
    duration_minutes: Optional[int]
    thumbnail_url: Optional[str]
    transcript: Optional[str] = None
    resources: Optional[Dict[str, Any]] = None
    order: int
    status: str
    created_at: str
    version: int = 1
    lesson_count: int = 0
    
    class Config:
        from_attributes = True


class LessonDetailResponse(LessonResponse):
    """Lesson response with full details."""
    
    transcript: Optional[str] = None
    resources: Optional[dict] = None


# ============================================================================
# MODULE SCHEMAS
# ============================================================================

class ModuleCreateRequest(BaseModel):
    """Request to create a module."""
    
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    order: int = Field(..., ge=1)
    
    class Config:
        example = {
            "title": "Module 1: Fundamentals",
            "description": "Learn the basics of ML",
            "order": 1,
        }


class ModuleUpdateRequest(BaseModel):
    """Request to update a module."""
    
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    order: Optional[int] = Field(None, ge=1)
    expected_version: Optional[int] = Field(None, ge=1)


class ModuleResponse(BaseModel):
    """Module response."""
    
    id: UUID
    course_id: UUID
    title: str
    description: Optional[str]
    order: int
    lessons: List[LessonResponse] = []
    created_at: str
    version: int = 1
    
    class Config:
        from_attributes = True


# ============================================================================
# COURSE SCHEMAS
# ============================================================================

class CourseCreateRequest(BaseModel):
    """Request to create a course."""
    
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10, max_length=2000)
    tags: Optional[List[str]] = Field(None, max_items=10)
    skill_level: SkillLevelEnum = SkillLevelEnum.BEGINNER
    category: Optional[str] = Field(None, max_length=100)
    is_free: bool = True
    
    @validator("tags")
    def validate_tags(cls, v):
        """Ensure tags are valid."""
        if v:
            return [tag.strip().lower()[:50] for tag in v if tag.strip()]
        return v
    
    class Config:
        example = {
            "title": "Machine Learning for Beginners",
            "description": "A comprehensive guide to machine learning...",
            "tags": ["ML", "AI", "Python", "Beginner"],
            "skill_level": "beginner",
            "category": "Artificial Intelligence",
            "is_free": True,
        }


class CourseUpdateRequest(BaseModel):
    """Request to update a course."""
    
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    tags: Optional[List[str]] = None
    skill_level: Optional[SkillLevelEnum] = None
    category: Optional[str] = None
    is_free: Optional[bool] = None
    is_featured: Optional[bool] = None
    cover_image_url: Optional[str] = None
    expected_version: Optional[int] = Field(None, ge=1)


class CourseResponse(BaseModel):
    """Course response."""
    
    id: UUID
    title: str
    description: str
    tags: Optional[List[str]]
    skill_level: str
    category: Optional[str]
    instructor_id: UUID
    status: str
    is_free: bool
    total_enrollments: int
    created_at: str
    published_at: Optional[str]
    version: int = 1
    
    class Config:
        from_attributes = True


class CourseDetailResponse(CourseResponse):
    """Course response with full details."""
    
    cover_image_url: Optional[str]
    thumbnail_url: Optional[str]
    is_featured: bool
    average_rating: Optional[str]
    total_reviews: int
    total_estimated_hours: Optional[int]
    modules: List[ModuleResponse] = []
    
    class Config:
        from_attributes = True


class CoursePreviewResponse(BaseModel):
    """Course preview response (structure without full content)."""
    
    id: UUID
    title: str
    description: str
    modules_count: int
    lessons_count: int
    total_duration_minutes: int
    status: str
    is_publishable: bool
    validation_errors: List[str] = []


class CoursePublishRequest(BaseModel):
    """Request to publish a course."""
    
    pass  # No additional fields needed


class CoursePublishResponse(BaseModel):
    """Course publish response."""
    
    id: UUID
    title: str
    status: str
    published_at: str
    message: str = "Course published successfully"


# ============================================================================
# BULK OPERATIONS
# ============================================================================

class ReorderModulesRequest(BaseModel):
    """Request to reorder modules."""
    
    module_orders: List[dict] = Field(..., description="List of {id, order}")
    
    class Config:
        example = {
            "module_orders": [
                {"id": "uuid-1", "order": 1},
                {"id": "uuid-2", "order": 2},
            ]
        }


class ReorderLessonsRequest(BaseModel):
    """Request to reorder lessons within a module."""
    
    lesson_orders: List[dict] = Field(..., description="List of {id, order}")
    
    class Config:
        example = {
            "lesson_orders": [
                {"id": "uuid-1", "order": 1},
                {"id": "uuid-2", "order": 2},
            ]
        }


# ============================================================================
# LIST/PAGINATION RESPONSES
# ============================================================================

class PaginationMeta(BaseModel):
    """Pagination metadata."""
    
    total: int
    page: int
    page_size: int
    total_pages: int


class CourseListResponse(BaseModel):
    """Course list response with pagination."""
    
    data: List[CourseResponse]
    meta: PaginationMeta


class ModuleListResponse(BaseModel):
    """Module list response with pagination."""
    
    data: List[ModuleResponse]
    meta: PaginationMeta


class LessonListResponse(BaseModel):
    """Lesson list response with pagination."""
    
    data: List[LessonResponse]
    meta: PaginationMeta
