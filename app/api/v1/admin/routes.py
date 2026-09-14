"""
Admin dashboard and analytics endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.api.v1.admin.service import AdminService
from app.models.course import Course
from app.config import settings
from app.dependencies import (
    get_db,
    get_admin_user,
    get_pagination,
    PaginationParams,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Dashboard"])


@router.get("/email/health", response_model=Dict[str, Any], summary="Email provider configuration health")
async def get_email_health(
    current_admin: Dict[str, Any] = Depends(get_admin_user),
) -> Dict[str, Any]:
    """Expose safe Resend configuration health without returning secrets."""
    return {
        "provider": "resend",
        "configured": bool(settings.RESEND_API_KEY and settings.RESEND_FROM_EMAIL),
        "from_email": settings.RESEND_FROM_EMAIL,
        "webhook_configured": bool(settings.RESEND_WEBHOOK_SECRET),
        "status": "ready" if settings.RESEND_API_KEY else "not_configured",
    }


@router.get("/courses", response_model=Dict[str, Any], summary="List all courses for administration")
async def get_admin_courses(
    pagination: PaginationParams = Depends(get_pagination),
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return drafts and published courses through the standard pagination envelope."""
    query = db.query(Course)
    total = query.count()
    courses = query.order_by(Course.created_at.desc()).offset(pagination.skip).limit(pagination.limit).all()
    return {
        "data": [
            {
                "id": str(course.id),
                "title": course.title,
                "description": course.description,
                "tags": course.tags,
                "skill_level": course.skill_level.value,
                "category": course.category,
                "instructor_id": str(course.instructor_id),
                "status": course.status.value,
                "is_free": course.is_free,
                "is_featured": course.is_featured,
                "cover_image_url": course.cover_image_url,
                "total_enrollments": course.total_enrollments,
                "modules_count": len(course.modules),
                "lessons_count": sum(len(module.lessons) for module in course.modules),
                "created_at": course.created_at.isoformat(),
                "published_at": course.published_at.isoformat() if course.published_at else None,
            }
            for course in courses
        ],
        "meta": {
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total": total,
            "total_pages": (total + pagination.page_size - 1) // pagination.page_size,
        },
    }


# ============================================================================
# DASHBOARD OVERVIEW
# ============================================================================

@router.get(
    "/dashboard/overview",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Admin dashboard overview",
)
async def get_dashboard_overview(
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get admin dashboard overview with key metrics.
    
    Returns:
    - Total users
    - Total courses
    - Total enrollments
    - Total lessons completed
    - Average completion rate
    - Recent activity
    """
    try:
        overview = AdminService.get_dashboard_overview(db=db)
        return overview
    
    except Exception as e:
        logger.error(f"Error fetching dashboard: {str(e)}")
        raise


# ============================================================================
# USERS ANALYTICS
# ============================================================================

@router.get(
    "/analytics/users",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Users analytics",
)
async def get_users_analytics(
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get comprehensive user analytics.
    
    Returns:
    - Total users by role
    - New users (last 7 days, 30 days)
    - Active users
    - User retention rate
    - Geographic distribution
    """
    try:
        analytics = AdminService.get_users_analytics(db=db)
        return analytics
    
    except Exception as e:
        logger.error(f"Error fetching user analytics: {str(e)}")
        raise


@router.get(
    "/analytics/users/list",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List all users (paginated)",
)
async def get_users_list(
    pagination: PaginationParams = Depends(get_pagination),
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get paginated list of all users."""
    try:
        users, total = AdminService.get_all_users(
            db=db,
            skip=pagination.skip,
            limit=pagination.limit,
        )
        
        return {
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "users": [
                {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.get_full_name(),
                    "role": user.role.value,
                    "country": user.country,
                    "created_at": user.created_at.isoformat(),
                    "is_active": user.is_active,
                }
                for user in users
            ],
        }
    
    except Exception as e:
        logger.error(f"Error fetching users list: {str(e)}")
        raise


# ============================================================================
# COURSES ANALYTICS
# ============================================================================

@router.get(
    "/analytics/courses",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Courses analytics",
)
async def get_courses_analytics(
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get comprehensive course analytics.
    
    Returns:
    - Total courses (draft, published)
    - Total enrollments
    - Average completion rate
    - Most popular courses
    - Drop-off analysis
    """
    try:
        analytics = AdminService.get_courses_analytics(db=db)
        return analytics
    
    except Exception as e:
        logger.error(f"Error fetching course analytics: {str(e)}")
        raise


@router.get(
    "/analytics/courses/{course_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Single course analytics",
)
async def get_course_analytics(
    course_id: str,
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get detailed analytics for a specific course.
    
    Returns:
    - Enrollments over time
    - Completion rate
    - Module-by-module completion
    - Most completed lessons
    - Lesson drop-off points
    - Average time per lesson
    """
    try:
        analytics = AdminService.get_course_analytics(db=db, course_id=course_id)
        return analytics
    
    except Exception as e:
        logger.error(f"Error fetching course analytics: {str(e)}")
        raise


# ============================================================================
# ENGAGEMENT ANALYTICS
# ============================================================================

@router.get(
    "/analytics/engagement",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="User engagement analytics",
)
async def get_engagement_analytics(
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get user engagement metrics.
    
    Returns:
    - Daily active users
    - Weekly active users
    - Average session duration
    - Lessons completed per day
    - Streak patterns
    - Email engagement
    """
    try:
        analytics = AdminService.get_engagement_analytics(db=db)
        return analytics
    
    except Exception as e:
        logger.error(f"Error fetching engagement analytics: {str(e)}")
        raise


# ============================================================================
# REVENUE/GROWTH ANALYTICS
# ============================================================================

@router.get(
    "/analytics/growth",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Growth analytics",
)
async def get_growth_analytics(
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get growth metrics.
    
    Returns:
    - New users per day/week/month
    - Course creation trend
    - Enrollment trend
    - Completion trend
    - Geographic growth
    """
    try:
        analytics = AdminService.get_growth_analytics(db=db)
        return analytics
    
    except Exception as e:
        logger.error(f"Error fetching growth analytics: {str(e)}")
        raise


# ============================================================================
# CONTENT QUALITY ANALYTICS
# ============================================================================

@router.get(
    "/analytics/content-quality",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Content quality metrics",
)
async def get_content_quality_analytics(
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get content quality metrics.
    
    Returns:
    - Lessons with poor completion
    - Lessons with high drop-off
    - Lessons with low engagement
    - Average rating by course
    - Recommended content improvements
    """
    try:
        analytics = AdminService.get_content_quality_analytics(db=db)
        return analytics
    
    except Exception as e:
        logger.error(f"Error fetching content quality analytics: {str(e)}")
        raise


# ============================================================================
# REPORTS & EXPORTS
# ============================================================================

@router.get(
    "/reports/users-export",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Export users report",
)
async def export_users_report(
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Export user data (CSV-ready format)."""
    try:
        report = AdminService.export_users_report(db=db)
        return report
    
    except Exception as e:
        logger.error(f"Error exporting users: {str(e)}")
        raise


@router.get(
    "/reports/courses-export",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Export courses report",
)
async def export_courses_report(
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Export course data (CSV-ready format)."""
    try:
        report = AdminService.export_courses_report(db=db)
        return report
    
    except Exception as e:
        logger.error(f"Error exporting courses: {str(e)}")
        raise


@router.get(
    "/reports/enrollments-export",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Export enrollments report",
)
async def export_enrollments_report(
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Export enrollment data (CSV-ready format)."""
    try:
        report = AdminService.export_enrollments_report(db=db)
        return report
    
    except Exception as e:
        logger.error(f"Error exporting enrollments: {str(e)}")
        raise
