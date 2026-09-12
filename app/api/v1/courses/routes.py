"""
Course management API endpoints.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.api.v1.courses.service import CourseService
from app.api.v1.courses.schemas import (
    CourseCreateRequest,
    CourseUpdateRequest,
    CourseResponse,
    CourseDetailResponse,
    CourseListResponse,
    CoursePreviewResponse,
    CoursePublishRequest,
    CoursePublishResponse,
    ModuleCreateRequest,
    ModuleResponse,
    ModuleUpdateRequest,
    LessonCreateRequest,
    LessonResponse,
    LessonUpdateRequest,
    PaginationMeta,
)
from app.dependencies import (
    get_db,
    get_admin_user,
    get_instructor_user,
    get_student_user,
    get_pagination,
    PaginationParams,
    check_resource_ownership,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Courses"])


# ============================================================================
# COURSE ENDPOINTS (ADMIN/INSTRUCTOR)
# ============================================================================

@router.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create course",
    description="Create a new course (admin/instructor only)",
)
async def create_course(
    request: CourseCreateRequest,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
) -> CourseResponse:
    """
    Create a new course in draft status.
    
    The course will be created but not published yet. You'll need to add
    modules and lessons before publishing.
    """
    try:
        course = CourseService.create_course(
            db=db,
            instructor_id=current_user.get("sub"),
            title=request.title,
            description=request.description,
            tags=request.tags,
            skill_level=request.skill_level.value,
            category=request.category,
            is_free=request.is_free,
        )
        
        return CourseResponse(
            id=course.id,
            title=course.title,
            description=course.description,
            tags=course.tags,
            skill_level=course.skill_level.value,
            category=course.category,
            instructor_id=course.instructor_id,
            status=course.status.value,
            is_free=course.is_free,
            total_enrollments=course.total_enrollments,
            created_at=course.created_at.isoformat(),
            published_at=course.published_at.isoformat() if course.published_at else None,
        )
    
    except Exception as e:
        logger.error(f"Error creating course: {str(e)}")
        raise


@router.get(
    "/courses/{course_id}",
    response_model=CourseDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get course details",
)
async def get_course(
    course_id: str,
    db: Session = Depends(get_db),
) -> CourseDetailResponse:
    """Get course details with all modules and lessons."""
    try:
        course = CourseService.get_course(db, course_id)
        
        modules = [
            ModuleResponse(
                id=m.id,
                course_id=m.course_id,
                title=m.title,
                description=m.description,
                order=m.order,
                lessons=[
                    LessonResponse(
                        id=l.id,
                        module_id=l.module_id,
                        title=l.title,
                        description=l.description,
                        youtube_url=l.youtube_url,
                        youtube_video_id=l.youtube_video_id,
                        duration_minutes=l.duration_minutes,
                        thumbnail_url=l.thumbnail_url,
                        order=l.order,
                        status=l.status.value,
                        created_at=l.created_at.isoformat(),
                    )
                    for l in sorted(m.lessons, key=lambda x: x.order)
                ],
                created_at=m.created_at.isoformat(),
            )
            for m in sorted(course.modules, key=lambda x: x.order)
        ]
        
        return CourseDetailResponse(
            id=course.id,
            title=course.title,
            description=course.description,
            tags=course.tags,
            skill_level=course.skill_level.value,
            category=course.category,
            instructor_id=course.instructor_id,
            status=course.status.value,
            is_free=course.is_free,
            total_enrollments=course.total_enrollments,
            cover_image_url=course.cover_image_url,
            thumbnail_url=course.thumbnail_url,
            is_featured=course.is_featured,
            average_rating=course.average_rating,
            total_reviews=course.total_reviews,
            total_estimated_hours=course.total_estimated_hours,
            modules=modules,
            created_at=course.created_at.isoformat(),
            published_at=course.published_at.isoformat() if course.published_at else None,
        )
    
    except Exception as e:
        logger.error(f"Error fetching course: {str(e)}")
        raise


@router.put(
    "/courses/{course_id}",
    response_model=CourseResponse,
    status_code=status.HTTP_200_OK,
    summary="Update course",
)
async def update_course(
    course_id: str,
    request: CourseUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
) -> CourseResponse:
    """Update course details (draft courses only)."""
    try:
        course = CourseService.update_course(
            db=db,
            course_id=course_id,
            instructor_id=current_user.get("sub"),
            title=request.title,
            description=request.description,
            tags=request.tags,
            skill_level=request.skill_level.value if request.skill_level else None,
            category=request.category,
            is_free=request.is_free,
            is_featured=request.is_featured,
            cover_image_url=request.cover_image_url,
        )
        
        return CourseResponse(
            id=course.id,
            title=course.title,
            description=course.description,
            tags=course.tags,
            skill_level=course.skill_level.value,
            category=course.category,
            instructor_id=course.instructor_id,
            status=course.status.value,
            is_free=course.is_free,
            total_enrollments=course.total_enrollments,
            created_at=course.created_at.isoformat(),
            published_at=course.published_at.isoformat() if course.published_at else None,
        )
    
    except Exception as e:
        logger.error(f"Error updating course: {str(e)}")
        raise


@router.delete(
    "/courses/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete course",
)
async def delete_course(
    course_id: str,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
):
    """Delete a course (draft only)."""
    try:
        CourseService.delete_course(
            db=db,
            course_id=course_id,
            instructor_id=current_user.get("sub"),
        )
        return {"message": "Course deleted"}
    except Exception as e:
        logger.error(f"Error deleting course: {str(e)}")
        raise


@router.get(
    "/courses/{course_id}/preview",
    response_model=CoursePreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview course",
    description="Get course structure and validation before publishing",
)
async def preview_course(
    course_id: str,
    db: Session = Depends(get_db),
):
    """Preview course structure and get validation errors."""
    try:
        preview = CourseService.get_course_preview(db, course_id)
        return CoursePreviewResponse(**preview)
    except Exception as e:
        logger.error(f"Error previewing course: {str(e)}")
        raise


@router.post(
    "/courses/{course_id}/publish",
    response_model=CoursePublishResponse,
    status_code=status.HTTP_200_OK,
    summary="Publish course",
    description="Publish a course (move from draft to published)",
)
async def publish_course(
    course_id: str,
    request: CoursePublishRequest,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
) -> CoursePublishResponse:
    """
    Publish a course.
    
    Validates:
    - Course has at least 1 module
    - Each module has at least 1 lesson
    - All lessons have YouTube URLs
    """
    try:
        course = CourseService.publish_course(
            db=db,
            course_id=course_id,
            instructor_id=current_user.get("sub"),
        )
        
        return CoursePublishResponse(
            id=course.id,
            title=course.title,
            status=course.status.value,
            published_at=course.published_at.isoformat(),
            message="Course published successfully",
        )
    except Exception as e:
        logger.error(f"Error publishing course: {str(e)}")
        raise


@router.get(
    "/courses",
    response_model=CourseListResponse,
    status_code=status.HTTP_200_OK,
    summary="List courses",
    description="List published courses",
)
async def list_courses(
    pagination: PaginationParams = Depends(get_pagination),
    skill_level: str = None,
    db: Session = Depends(get_db),
) -> CourseListResponse:
    """List all published courses with pagination."""
    try:
        courses, total = CourseService.list_courses(
            db=db,
            skip=pagination.skip,
            limit=pagination.limit,
            skill_level=skill_level,
        )
        
        return CourseListResponse(
            data=[
                CourseResponse(
                    id=c.id,
                    title=c.title,
                    description=c.description,
                    tags=c.tags,
                    skill_level=c.skill_level.value,
                    category=c.category,
                    instructor_id=c.instructor_id,
                    status=c.status.value,
                    is_free=c.is_free,
                    total_enrollments=c.total_enrollments,
                    created_at=c.created_at.isoformat(),
                    published_at=c.published_at.isoformat() if c.published_at else None,
                )
                for c in courses
            ],
            meta=PaginationMeta(
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=(total + pagination.page_size - 1) // pagination.page_size,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing courses: {str(e)}")
        raise


# ============================================================================
# MODULE ENDPOINTS
# ============================================================================

# Retained temporarily for backwards reference only. Dedicated module and lesson
# routers are the canonical API surface and are the only ones mounted by main.py.
legacy_content_router = APIRouter(prefix="/api/v1", include_in_schema=False)

@legacy_content_router.post(
    "/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create module",
)
async def create_module(
    request: ModuleCreateRequest,
    course_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> ModuleResponse:
    """Create a new module in a course."""
    try:
        module = CourseService.create_module(
            db=db,
            course_id=course_id,
            instructor_id=current_user.get("sub"),
            title=request.title,
            description=request.description,
            order=request.order,
        )
        
        return ModuleResponse(
            id=module.id,
            course_id=module.course_id,
            title=module.title,
            description=module.description,
            order=module.order,
            lessons=[],
            created_at=module.created_at.isoformat(),
        )
    except Exception as e:
        logger.error(f"Error creating module: {str(e)}")
        raise


@legacy_content_router.get(
    "/modules/{module_id}",
    response_model=ModuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get module",
)
async def get_module(
    module_id: str,
    db: Session = Depends(get_db),
) -> ModuleResponse:
    """Get module details."""
    try:
        module = CourseService.get_module(db, module_id)
        
        lessons = [
            LessonResponse(
                id=l.id,
                module_id=l.module_id,
                title=l.title,
                description=l.description,
                youtube_url=l.youtube_url,
                youtube_video_id=l.youtube_video_id,
                duration_minutes=l.duration_minutes,
                thumbnail_url=l.thumbnail_url,
                order=l.order,
                status=l.status.value,
                created_at=l.created_at.isoformat(),
            )
            for l in sorted(module.lessons, key=lambda x: x.order)
        ]
        
        return ModuleResponse(
            id=module.id,
            course_id=module.course_id,
            title=module.title,
            description=module.description,
            order=module.order,
            lessons=lessons,
            created_at=module.created_at.isoformat(),
        )
    except Exception as e:
        logger.error(f"Error fetching module: {str(e)}")
        raise


@legacy_content_router.put(
    "/modules/{module_id}",
    response_model=ModuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update module",
)
async def update_module(
    module_id: str,
    request: ModuleUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> ModuleResponse:
    """Update module."""
    try:
        module = CourseService.update_module(
            db=db,
            module_id=module_id,
            instructor_id=current_user.get("sub"),
            title=request.title,
            description=request.description,
            order=request.order,
        )
        
        return ModuleResponse(
            id=module.id,
            course_id=module.course_id,
            title=module.title,
            description=module.description,
            order=module.order,
            lessons=[],
            created_at=module.created_at.isoformat(),
        )
    except Exception as e:
        logger.error(f"Error updating module: {str(e)}")
        raise


@legacy_content_router.delete(
    "/modules/{module_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete module",
)
async def delete_module(
    module_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Delete a module."""
    try:
        CourseService.delete_module(
            db=db,
            module_id=module_id,
            instructor_id=current_user.get("sub"),
        )
        return {"message": "Module deleted"}
    except Exception as e:
        logger.error(f"Error deleting module: {str(e)}")
        raise


# ============================================================================
# LESSON ENDPOINTS
# ============================================================================

@legacy_content_router.post(
    "/lessons",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create lesson",
)
async def create_lesson(
    request: LessonCreateRequest,
    module_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> LessonResponse:
    """Create a new lesson with YouTube video."""
    try:
        lesson = await CourseService.create_lesson(
            db=db,
            module_id=module_id,
            instructor_id=current_user.get("sub"),
            title=request.title,
            description=request.description,
            youtube_url=request.youtube_url,
            order=request.order,
        )
        
        return LessonResponse(
            id=lesson.id,
            module_id=lesson.module_id,
            title=lesson.title,
            description=lesson.description,
            youtube_url=lesson.youtube_url,
            youtube_video_id=lesson.youtube_video_id,
            duration_minutes=lesson.duration_minutes,
            thumbnail_url=lesson.thumbnail_url,
            order=lesson.order,
            status=lesson.status.value,
            created_at=lesson.created_at.isoformat(),
        )
    except Exception as e:
        logger.error(f"Error creating lesson: {str(e)}")
        raise


@legacy_content_router.get(
    "/lessons/{lesson_id}",
    response_model=LessonResponse,
    status_code=status.HTTP_200_OK,
    summary="Get lesson",
)
async def get_lesson(
    lesson_id: str,
    db: Session = Depends(get_db),
) -> LessonResponse:
    """Get lesson details."""
    try:
        lesson = CourseService.get_lesson(db, lesson_id)
        
        return LessonResponse(
            id=lesson.id,
            module_id=lesson.module_id,
            title=lesson.title,
            description=lesson.description,
            youtube_url=lesson.youtube_url,
            youtube_video_id=lesson.youtube_video_id,
            duration_minutes=lesson.duration_minutes,
            thumbnail_url=lesson.thumbnail_url,
            order=lesson.order,
            status=lesson.status.value,
            created_at=lesson.created_at.isoformat(),
        )
    except Exception as e:
        logger.error(f"Error fetching lesson: {str(e)}")
        raise


@legacy_content_router.put(
    "/lessons/{lesson_id}",
    response_model=LessonResponse,
    status_code=status.HTTP_200_OK,
    summary="Update lesson",
)
async def update_lesson(
    lesson_id: str,
    request: LessonUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> LessonResponse:
    """Update lesson."""
    try:
        lesson = await CourseService.update_lesson(
            db=db,
            lesson_id=lesson_id,
            instructor_id=current_user.get("sub"),
            title=request.title,
            description=request.description,
            youtube_url=request.youtube_url,
            order=request.order,
        )
        
        return LessonResponse(
            id=lesson.id,
            module_id=lesson.module_id,
            title=lesson.title,
            description=lesson.description,
            youtube_url=lesson.youtube_url,
            youtube_video_id=lesson.youtube_video_id,
            duration_minutes=lesson.duration_minutes,
            thumbnail_url=lesson.thumbnail_url,
            order=lesson.order,
            status=lesson.status.value,
            created_at=lesson.created_at.isoformat(),
        )
    except Exception as e:
        logger.error(f"Error updating lesson: {str(e)}")
        raise


@legacy_content_router.delete(
    "/lessons/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete lesson",
)
async def delete_lesson(
    lesson_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Delete a lesson."""
    try:
        CourseService.delete_lesson(
            db=db,
            lesson_id=lesson_id,
            instructor_id=current_user.get("sub"),
        )
        return {"message": "Lesson deleted"}
    except Exception as e:
        logger.error(f"Error deleting lesson: {str(e)}")
        raise
