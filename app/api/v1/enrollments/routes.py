"""
Course enrollment API endpoints.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.api.v1.enrollments.service import EnrollmentService
from app.api.v1.enrollments.schemas import (
    EnrollCourseRequest,
    EnrollmentResponse,
    UserEnrollmentsResponse,
)
from app.dependencies import (
    get_db,
    get_student_user,
    get_pagination,
    PaginationParams,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/enrollments", tags=["Enrollments"])


# ============================================================================
# ENROLL IN COURSE
# ============================================================================

@router.post(
    "",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll in course",
    description="Enroll current user in a course",
)
async def enroll_course(
    request: EnrollCourseRequest,
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> EnrollmentResponse:
    """
    Enroll in a course.
    
    - Course must be published
    - Student can't enroll twice in same course
    - Starts progress tracking automatically
    """
    try:
        user_id = current_user.get("sub")
        
        enrollment = await EnrollmentService.enroll_user(
            db=db,
            user_id=user_id,
            course_id=request.course_id,
        )
        
        return EnrollmentResponse(
            id=enrollment.id,
            user_id=enrollment.user_id,
            course_id=enrollment.course_id,
            course_title=enrollment.course.title,
            completion_percentage=enrollment.completion_percentage,
            is_completed=enrollment.is_completed,
            enrolled_at=enrollment.enrolled_at.isoformat(),
            completed_at=enrollment.completed_at.isoformat() if enrollment.completed_at else None,
        )
    
    except Exception as e:
        logger.error(f"Error enrolling in course: {str(e)}")
        raise


# ============================================================================
# GET USER ENROLLMENTS
# ============================================================================

@router.get(
    "/my-enrollments",
    response_model=UserEnrollmentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get my enrollments",
    description="Get all courses user is enrolled in",
)
async def get_my_enrollments(
    pagination: PaginationParams = Depends(get_pagination),
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> UserEnrollmentsResponse:
    """
    Get all courses the current user is enrolled in.
    
    Returns:
    - Course details
    - Progress percentage
    - Enrollment date
    - Completion date (if completed)
    """
    try:
        user_id = current_user.get("sub")
        
        enrollments, total = EnrollmentService.get_user_enrollments(
            db=db,
            user_id=user_id,
            skip=pagination.skip,
            limit=pagination.limit,
        )
        
        return UserEnrollmentsResponse(
            data=[
                EnrollmentResponse(
                    id=e.id,
                    user_id=e.user_id,
                    course_id=e.course_id,
                    course_title=e.course.title,
                    completion_percentage=e.completion_percentage,
                    is_completed=e.is_completed,
                    enrolled_at=e.enrolled_at.isoformat(),
                    completed_at=e.completed_at.isoformat() if e.completed_at else None,
                )
                for e in enrollments
            ],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    
    except Exception as e:
        logger.error(f"Error fetching enrollments: {str(e)}")
        raise


# ============================================================================
# GET SPECIFIC ENROLLMENT
# ============================================================================

@router.get(
    "/{course_id}",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get enrollment",
)
async def get_enrollment(
    course_id: str,
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> EnrollmentResponse:
    """Get enrollment details for a specific course."""
    try:
        user_id = current_user.get("sub")
        
        enrollment = EnrollmentService.get_enrollment(
            db=db,
            user_id=user_id,
            course_id=course_id,
        )
        
        return EnrollmentResponse(
            id=enrollment.id,
            user_id=enrollment.user_id,
            course_id=enrollment.course_id,
            course_title=enrollment.course.title,
            completion_percentage=enrollment.completion_percentage,
            is_completed=enrollment.is_completed,
            enrolled_at=enrollment.enrolled_at.isoformat(),
            completed_at=enrollment.completed_at.isoformat() if enrollment.completed_at else None,
        )
    
    except Exception as e:
        logger.error(f"Error fetching enrollment: {str(e)}")
        raise


# ============================================================================
# UNENROLL FROM COURSE
# ============================================================================

@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unenroll from course",
)
async def unenroll_course(
    course_id: str,
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    """
    Unenroll from a course.
    
    WARNING: This will delete all progress on this course.
    """
    try:
        user_id = current_user.get("sub")
        
        EnrollmentService.unenroll_user(
            db=db,
            user_id=user_id,
            course_id=course_id,
        )
        
        return None
    
    except Exception as e:
        logger.error(f"Error unenrolling: {str(e)}")
        raise


# ============================================================================
# CHECK ENROLLMENT
# ============================================================================

@router.get(
    "/check/{course_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Check if enrolled",
)
async def check_enrollment(
    course_id: str,
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Check if user is enrolled in a course."""
    try:
        user_id = current_user.get("sub")
        
        is_enrolled = EnrollmentService.is_user_enrolled(
            db=db,
            user_id=user_id,
            course_id=course_id,
        )
        
        return {
            "course_id": course_id,
            "is_enrolled": is_enrolled,
        }
    
    except Exception as e:
        logger.error(f"Error checking enrollment: {str(e)}")
        raise