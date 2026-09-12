"""
Progress tracking API endpoints.
Mark lessons complete, get progress, track streaks.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from app.api.v1.progress.service import ProgressService
from app.api.v1.progress.schemas import (
    MarkLessonCompleteRequest,
    ProgressResponse,
    CourseProgressResponse,
    UserProgressDashboardResponse,
    UserProgressResponse,
    ModuleProgressResponse,
)
from app.dependencies import (
    get_db,
    get_student_user,
    get_pagination,
    PaginationParams,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/progress", tags=["Progress Tracking"])


# ============================================================================
# MARK LESSON COMPLETE
# ============================================================================

@router.post(
    "/mark-lesson-complete/{lesson_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Mark lesson complete",
    description="Mark a lesson as complete and update progress",
)
async def mark_lesson_complete(
    lesson_id: str,
    request: MarkLessonCompleteRequest,
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Mark a lesson as complete.
    
    Updates:
    - Lesson completion status
    - Module progress percentage
    - Course progress percentage
    - Current streak count
    - User badges eligibility
    - Sends email notification
    - Returns next lesson recommendation
    """
    try:
        user_id = current_user.get("sub")
        
        result = await ProgressService.mark_lesson_complete(
            db=db,
            user_id=user_id,
            lesson_id=lesson_id,
            time_spent_minutes=request.time_spent_minutes,
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error marking lesson complete: {str(e)}")
        raise


# ============================================================================
# GET LESSON PROGRESS
# ============================================================================

@router.get(
    "/lesson/{lesson_id}",
    response_model=UserProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Get lesson progress",
)
async def get_lesson_progress(
    lesson_id: str,
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> UserProgressResponse:
    """Get user's progress for a specific lesson."""
    try:
        user_id = current_user.get("sub")
        
        progress = ProgressService.get_lesson_progress(
            db=db,
            user_id=user_id,
            lesson_id=lesson_id,
        )
        
        return progress
    
    except Exception as e:
        logger.error(f"Error fetching lesson progress: {str(e)}")
        raise


# ============================================================================
# GET MODULE PROGRESS
# ============================================================================

@router.get(
    "/module/{module_id}",
    response_model=ModuleProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Get module progress",
)
async def get_module_progress(
    module_id: str,
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> ModuleProgressResponse:
    """Get user's progress for a specific module."""
    try:
        user_id = current_user.get("sub")
        
        progress = ProgressService.get_module_progress(
            db=db,
            user_id=user_id,
            module_id=module_id,
        )
        
        return progress
    
    except Exception as e:
        logger.error(f"Error fetching module progress: {str(e)}")
        raise


# ============================================================================
# GET COURSE PROGRESS
# ============================================================================

@router.get(
    "/course/{course_id}",
    response_model=CourseProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Get course progress",
)
async def get_course_progress(
    course_id: str,
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> CourseProgressResponse:
    """
    Get user's progress for a specific course.
    
    Returns:
    - Overall completion percentage
    - Current module and lesson
    - Module-by-module breakdown
    - Estimated time remaining
    """
    try:
        user_id = current_user.get("sub")
        
        progress = ProgressService.get_course_progress(
            db=db,
            user_id=user_id,
            course_id=course_id,
        )
        
        return progress
    
    except Exception as e:
        logger.error(f"Error fetching course progress: {str(e)}")
        raise


# ============================================================================
# GET USER DASHBOARD
# ============================================================================

@router.get(
    "/user/dashboard",
    response_model=UserProgressDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user dashboard",
    description="Get comprehensive user learning dashboard",
)
async def get_user_dashboard(
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> UserProgressDashboardResponse:
    """
    Get complete user learning dashboard.
    
    Includes:
    - All enrolled courses with progress
    - Current learning streaks
    - Recent achievements/badges
    - Weekly learning stats
    - Recommendations
    """
    try:
        user_id = current_user.get("sub")
        
        dashboard = await ProgressService.get_user_dashboard(
            db=db,
            user_id=user_id,
        )
        
        return dashboard
    
    except Exception as e:
        logger.error(f"Error fetching dashboard: {str(e)}")
        raise


# ============================================================================
# GET USER STATS
# ============================================================================

@router.get(
    "/user/stats",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get user learning statistics",
)
async def get_user_stats(
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get user's learning statistics.
    
    Returns:
    - Total courses enrolled
    - Total courses completed
    - Total lessons completed
    - Total time spent learning
    - Current streak
    - Longest streak
    - Badges earned
    - XP points
    """
    try:
        user_id = current_user.get("sub")
        
        stats = ProgressService.get_user_stats(
            db=db,
            user_id=user_id,
        )
        
        return stats
    
    except Exception as e:
        logger.error(f"Error fetching user stats: {str(e)}")
        raise


# ============================================================================
# GET USER LEARNING HISTORY
# ============================================================================

@router.get(
    "/user/history",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get learning history",
)
async def get_learning_history(
    pagination: PaginationParams = Depends(get_pagination),
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get user's learning activity history.
    
    Shows:
    - Recent lessons completed
    - When completed
    - Time spent on each
    - Achievements earned
    """
    try:
        user_id = current_user.get("sub")
        
        history = ProgressService.get_learning_history(
            db=db,
            user_id=user_id,
            skip=pagination.skip,
            limit=pagination.limit,
        )
        
        return history
    
    except Exception as e:
        logger.error(f"Error fetching learning history: {str(e)}")
        raise


# ============================================================================
# RESET LESSON PROGRESS (ADMIN)
# ============================================================================

@router.post(
    "/admin/reset-lesson/{lesson_id}/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset lesson progress (admin only)",
)
async def reset_lesson_progress(
    lesson_id: str,
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_student_user),  # Should be admin
    db: Session = Depends(get_db),
):
    """Reset user's progress on a specific lesson (admin only)."""
    try:
        # Check if admin (simplified - should verify in get_student_user)
        if current_user.get("role") not in ["admin", "instructor"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can reset progress",
            )
        
        ProgressService.reset_lesson_progress(
            db=db,
            user_id=user_id,
            lesson_id=lesson_id,
        )
        
        return None
    
    except Exception as e:
        logger.error(f"Error resetting progress: {str(e)}")
        raise


# ============================================================================
# CERTIFICATES
# ============================================================================

@router.get(
    "/certificate/{course_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get course certificate",
    description="Get certificate details for a completed course",
)
async def get_course_certificate(
    course_id: str,
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get certificate for a completed course.
    
    Returns certificate details including:
    - Certificate ID
    - Course name
    - User name
    - Completion date
    - Certificate URL
    - Verification code
    """
    try:
        user_id = current_user.get("sub")
        
        certificate = await ProgressService.get_certificate(
            db=db,
            user_id=user_id,
            course_id=course_id,
        )
        
        return certificate
    
    except Exception as e:
        logger.error(f"Error fetching certificate: {str(e)}")
        raise


@router.get(
    "/certificates",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get all user certificates",
    description="Get all certificates earned by the user",
)
async def get_user_certificates(
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get all certificates earned by the user.
    
    Returns list of certificates for all completed courses.
    """
    try:
        user_id = current_user.get("sub")
        
        certificates = await ProgressService.get_user_certificates(
            db=db,
            user_id=user_id,
        )
        
        return certificates
    
    except Exception as e:
        logger.error(f"Error fetching certificates: {str(e)}")
        raise


@router.get(
    "/verify-certificate/{verification_code}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Verify certificate",
    description="Verify a certificate using its verification code",
)
async def verify_certificate(
    verification_code: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Verify a certificate using its verification code.
    
    This is a public endpoint for employers/third parties to verify certificates.
    """
    try:
        result = ProgressService.verify_certificate(
            db=db,
            verification_code=verification_code,
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error verifying certificate: {str(e)}")
        raise