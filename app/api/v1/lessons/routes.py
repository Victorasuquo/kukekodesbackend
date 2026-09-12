"""
Lesson API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum

from app.db.postgres import get_db
from app.dependencies import get_instructor_user
from app.models.course import LessonStatus
from app.api.v1.lessons.service import LessonService

router = APIRouter(
    prefix="/api/v1/lessons",
    tags=["Lessons"],
)


# ============================================================================
# SCHEMAS
# ============================================================================

class LessonStatusEnum(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class LessonCreateRequest(BaseModel):
    module_id: str
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    youtube_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    resources: Optional[Dict] = None
    order: Optional[int] = None
    status: LessonStatusEnum = LessonStatusEnum.DRAFT


class LessonUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    youtube_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    resources: Optional[Dict] = None
    order: Optional[int] = None
    status: Optional[LessonStatusEnum] = None


class LessonResponse(BaseModel):
    id: str
    module_id: str
    title: str
    description: Optional[str]
    youtube_url: Optional[str]
    youtube_video_id: Optional[str]
    duration_minutes: Optional[int]
    order: int
    status: str
    created_at: str
    
    class Config:
        from_attributes = True


# ============================================================================
# ROUTES
# ============================================================================

@router.get("/{lesson_id}", response_model=dict)
async def get_lesson(
    lesson_id: str,
    db: Session = Depends(get_db),
):
    """Get lesson details including previous/next navigation."""
    return LessonService.get_lesson_detail(db, lesson_id)


@router.get("/module/{module_id}", response_model=List[LessonResponse])
async def get_module_lessons(
    module_id: str,
    db: Session = Depends(get_db),
):
    """Get all lessons for a module."""
    lessons = LessonService.get_lessons_by_module(db, module_id)
    return [
        LessonResponse(
            id=str(l.id),
            module_id=str(l.module_id),
            title=l.title,
            description=l.description,
            youtube_url=l.youtube_url,
            youtube_video_id=l.youtube_video_id,
            duration_minutes=l.duration_minutes,
            order=l.order,
            status=l.status.value,
            created_at=l.created_at.isoformat(),
        )
        for l in lessons
    ]


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    request: LessonCreateRequest,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
):
    """Create a new lesson (instructor only)."""
    lesson = LessonService.create_lesson(
        db=db,
        module_id=request.module_id,
        title=request.title,
        description=request.description,
        youtube_url=request.youtube_url,
        duration_minutes=request.duration_minutes,
        resources=request.resources,
        order=request.order,
        status=LessonStatus(request.status.value),
    )
    
    return LessonResponse(
        id=str(lesson.id),
        module_id=str(lesson.module_id),
        title=lesson.title,
        description=lesson.description,
        youtube_url=lesson.youtube_url,
        youtube_video_id=lesson.youtube_video_id,
        duration_minutes=lesson.duration_minutes,
        order=lesson.order,
        status=lesson.status.value,
        created_at=lesson.created_at.isoformat(),
    )


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: str,
    request: LessonUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
):
    """Update a lesson (instructor only)."""
    lesson = LessonService.update_lesson(
        db=db,
        lesson_id=lesson_id,
        title=request.title,
        description=request.description,
        youtube_url=request.youtube_url,
        duration_minutes=request.duration_minutes,
        resources=request.resources,
        order=request.order,
        status=LessonStatus(request.status.value) if request.status else None,
    )
    
    return LessonResponse(
        id=str(lesson.id),
        module_id=str(lesson.module_id),
        title=lesson.title,
        description=lesson.description,
        youtube_url=lesson.youtube_url,
        youtube_video_id=lesson.youtube_video_id,
        duration_minutes=lesson.duration_minutes,
        order=lesson.order,
        status=lesson.status.value,
        created_at=lesson.created_at.isoformat(),
    )


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: str,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
):
    """Delete a lesson (instructor only)."""
    LessonService.delete_lesson(db, lesson_id)


@router.post("/{lesson_id}/publish", response_model=LessonResponse)
async def publish_lesson(
    lesson_id: str,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
):
    """Publish a lesson (instructor only)."""
    lesson = LessonService.publish_lesson(db, lesson_id)
    
    return LessonResponse(
        id=str(lesson.id),
        module_id=str(lesson.module_id),
        title=lesson.title,
        description=lesson.description,
        youtube_url=lesson.youtube_url,
        youtube_video_id=lesson.youtube_video_id,
        duration_minutes=lesson.duration_minutes,
        order=lesson.order,
        status=lesson.status.value,
        created_at=lesson.created_at.isoformat(),
    )


@router.post("/{lesson_id}/unpublish", response_model=LessonResponse)
async def unpublish_lesson(
    lesson_id: str,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
):
    """Unpublish a lesson (instructor only)."""
    lesson = LessonService.unpublish_lesson(db, lesson_id)
    
    return LessonResponse(
        id=str(lesson.id),
        module_id=str(lesson.module_id),
        title=lesson.title,
        description=lesson.description,
        youtube_url=lesson.youtube_url,
        youtube_video_id=lesson.youtube_video_id,
        duration_minutes=lesson.duration_minutes,
        order=lesson.order,
        status=lesson.status.value,
        created_at=lesson.created_at.isoformat(),
    )
