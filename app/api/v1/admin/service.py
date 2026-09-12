"""
Admin analytics and dashboard business logic.
"""

from sqlalchemy.orm import Session
from sqlalchemy import case, func
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any
import logging

from app.models.user import User, UserRole
from app.models.course import Course, CourseStatus, Lesson
from app.models.enrollment import Enrollment, UserProgress
from app.models.progress import Streak

logger = logging.getLogger(__name__)


class AdminService:
    """Service for admin dashboard and analytics."""
    
    @staticmethod
    def get_dashboard_overview(db: Session) -> Dict[str, Any]:
        """Get admin dashboard overview."""
        # Basic counts
        total_users = db.query(User).filter(User.is_active == True).count()
        total_courses = db.query(Course).filter(
            Course.status == CourseStatus.PUBLISHED,
        ).count()
        total_instructors = db.query(User).filter(
            User.role == UserRole.INSTRUCTOR,
        ).count()
        total_enrollments = db.query(Enrollment).count()
        total_lessons_completed = db.query(UserProgress).filter(
            UserProgress.is_completed == True,
        ).count()
        
        # Average completion rate
        avg_completion_rate = db.query(
            func.avg(Enrollment.completion_percentage),
        ).scalar() or 0
        
        # New users (last 7 days)
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_week = db.query(User).filter(
            User.created_at >= one_week_ago,
        ).count()
        
        # New courses (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_courses_month = db.query(Course).filter(
            Course.created_at >= thirty_days_ago,
        ).count()
        
        return {
            "total_users": total_users,
            "total_students": db.query(User).filter(
                User.role == UserRole.STUDENT,
            ).count(),
            "total_instructors": total_instructors,
            "total_courses": total_courses,
            "total_enrollments": total_enrollments,
            "total_lessons_completed": total_lessons_completed,
            "average_completion_rate": round(float(avg_completion_rate), 2),
            "new_users_this_week": new_users_week,
            "new_courses_this_month": new_courses_month,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def get_users_analytics(db: Session) -> Dict[str, Any]:
        """Get comprehensive user analytics."""
        total_users = db.query(User).filter(User.is_active == True).count()
        
        # Users by role
        students = db.query(User).filter(User.role == UserRole.STUDENT).count()
        instructors = db.query(User).filter(User.role == UserRole.INSTRUCTOR).count()
        admins = db.query(User).filter(User.role == UserRole.ADMIN).count()
        
        # New users
        today = datetime.utcnow().date()
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        new_users_today = db.query(User).filter(
            func.date(User.created_at) == today,
        ).count()
        new_users_week = db.query(User).filter(
            User.created_at >= one_week_ago,
        ).count()
        new_users_month = db.query(User).filter(
            User.created_at >= thirty_days_ago,
        ).count()
        
        # Active users (users with recent activity)
        active_week = db.query(User.id.distinct()).join(UserProgress).filter(
            UserProgress.completed_at >= one_week_ago,
        ).count()
        
        active_month = db.query(User.id.distinct()).join(UserProgress).filter(
            UserProgress.completed_at >= thirty_days_ago,
        ).count()
        
        # Geographic distribution
        top_countries = db.query(
            User.country,
            func.count(User.id).label('count'),
        ).filter(
            User.is_active == True,
            User.country.isnot(None),
        ).group_by(User.country).order_by(
            func.count(User.id).desc(),
        ).limit(10).all()
        
        return {
            "total_users": total_users,
            "users_by_role": {
                "students": students,
                "instructors": instructors,
                "admins": admins,
            },
            "new_users": {
                "today": new_users_today,
                "this_week": new_users_week,
                "this_month": new_users_month,
            },
            "active_users": {
                "this_week": active_week,
                "this_month": active_month,
            },
            "top_countries": [
                {"country": country, "users": count}
                for country, count in top_countries
            ],
        }
    
    @staticmethod
    def get_courses_analytics(db: Session) -> Dict[str, Any]:
        """Get comprehensive course analytics."""
        total_courses = db.query(Course).count()
        published_courses = db.query(Course).filter(
            Course.status == CourseStatus.PUBLISHED,
        ).count()
        draft_courses = db.query(Course).filter(
            Course.status == CourseStatus.DRAFT,
        ).count()
        
        total_enrollments = db.query(Enrollment).count()
        
        # Most popular courses
        top_courses = db.query(
            Course.id,
            Course.title,
            func.count(Enrollment.id).label('enrollments'),
        ).outerjoin(Enrollment).group_by(
            Course.id,
            Course.title,
        ).order_by(
            func.count(Enrollment.id).desc(),
        ).limit(10).all()
        
        return {
            "total_courses": total_courses,
            "published": published_courses,
            "draft": draft_courses,
            "total_enrollments": total_enrollments,
            "top_courses": [
                {"course_id": str(c[0]), "title": c[1], "enrollments": c[2]}
                for c in top_courses
            ],
        }
    
    @staticmethod
    def get_course_analytics(db: Session, course_id: str) -> Dict[str, Any]:
        """Get detailed analytics for a course."""
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("Course not found")
        
        enrollments = db.query(Enrollment).filter(
            Enrollment.course_id == course_id,
        )
        total_enrollments = enrollments.count()
        completed_enrollments = enrollments.filter(
            Enrollment.is_completed == True,
        ).count()
        
        completion_rate = (
            (completed_enrollments / total_enrollments * 100)
            if total_enrollments > 0
            else 0
        )
        
        # Module completion
        module_stats = []
        for module in course.modules:
            lessons_completed = db.query(UserProgress).filter(
                UserProgress.module_id == module.id,
                UserProgress.is_completed == True,
            ).count()
            
            total_lessons = len(module.lessons)
            completion = (lessons_completed / total_lessons * 100) if total_lessons > 0 else 0
            
            module_stats.append({
                "module_id": str(module.id),
                "title": module.title,
                "lessons_completed": lessons_completed,
                "total_lessons": total_lessons,
                "completion_percentage": round(completion, 2),
            })
        
        return {
            "course_id": course_id,
            "course_title": course.title,
            "total_enrollments": total_enrollments,
            "completed_enrollments": completed_enrollments,
            "completion_rate": round(completion_rate, 2),
            "modules": module_stats,
            "average_time_spent_minutes": int(
                db.query(func.avg(UserProgress.time_spent_minutes)).filter(
                    UserProgress.course_id == course_id,
                ).scalar() or 0
            ),
        }
    
    @staticmethod
    def get_engagement_analytics(db: Session) -> Dict[str, Any]:
        """Get engagement metrics."""
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Daily active users (last 7 days)
        daily_active = db.query(
            func.date(UserProgress.completed_at).label('date'),
            func.count(UserProgress.user_id.distinct()).label('count'),
        ).filter(
            UserProgress.completed_at >= one_week_ago,
        ).group_by(
            func.date(UserProgress.completed_at),
        ).order_by(
            func.date(UserProgress.completed_at),
        ).all()
        
        # Average time per lesson
        avg_time_per_lesson = db.query(
            func.avg(UserProgress.time_spent_minutes),
        ).scalar() or 0
        
        # Lessons completed per day (last 7 days)
        lessons_per_day = db.query(
            func.count(UserProgress.id),
        ).filter(
            UserProgress.completed_at >= one_week_ago,
            UserProgress.is_completed == True,
        ).scalar() or 0
        
        # Users with current streak
        users_with_streak = db.query(Streak).filter(
            Streak.current_streak_count > 0,
        ).count()
        
        return {
            "daily_active_users": [
                {"date": str(date), "active_users": count}
                for date, count in daily_active
            ],
            "average_time_per_lesson_minutes": round(avg_time_per_lesson, 2),
            "lessons_completed_last_7_days": lessons_per_day,
            "users_with_active_streak": users_with_streak,
            "average_lessons_per_user": round(
                (db.query(UserProgress).count() / db.query(User).count())
                if db.query(User).count() else 0,
                2,
            ),
        }
    
    @staticmethod
    def get_growth_analytics(db: Session) -> Dict[str, Any]:
        """Get growth metrics."""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # New users trend
        new_users_week = db.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count'),
        ).filter(
            User.created_at >= seven_days_ago,
        ).group_by(
            func.date(User.created_at),
        ).all()
        
        # New courses trend
        new_courses_month = db.query(
            func.date(Course.created_at).label('date'),
            func.count(Course.id).label('count'),
        ).filter(
            Course.created_at >= thirty_days_ago,
        ).group_by(
            func.date(Course.created_at),
        ).all()
        
        # New enrollments trend
        new_enrollments_month = db.query(
            func.date(Enrollment.enrolled_at).label('date'),
            func.count(Enrollment.id).label('count'),
        ).filter(
            Enrollment.enrolled_at >= thirty_days_ago,
        ).group_by(
            func.date(Enrollment.enrolled_at),
        ).all()
        
        return {
            "new_users_this_week": [
                {"date": str(date), "new_users": count}
                for date, count in new_users_week
            ],
            "new_courses_this_month": [
                {"date": str(date), "new_courses": count}
                for date, count in new_courses_month
            ],
            "new_enrollments_this_month": [
                {"date": str(date), "new_enrollments": count}
                for date, count in new_enrollments_month
            ],
        }
    
    @staticmethod
    def get_content_quality_analytics(db: Session) -> Dict[str, Any]:
        """Get content quality metrics."""
        # Lessons with low completion (< 50%)
        low_completion_lessons = db.query(
            Lesson.id,
            Lesson.title,
            func.count(UserProgress.id).label('views'),
            func.sum(
                case(
                    (UserProgress.is_completed == True, 1),
                    else_=0,
                ),
            ).label('completions'),
        ).outerjoin(UserProgress).group_by(
            Lesson.id,
            Lesson.title,
        ).having(
            func.sum(
                case(
                    (UserProgress.is_completed == True, 1),
                    else_=0,
                ),
            ) < func.count(UserProgress.id) * 0.5,
        ).all()
        
        return {
            "low_completion_lessons": [
                {
                    "lesson_id": str(l[0]),
                    "title": l[1],
                    "views": l[2],
                    "completions": l[3] or 0,
                    "completion_rate": round(
                        ((l[3] or 0) / l[2] * 100) if l[2] > 0 else 0,
                        2,
                    ),
                }
                for l in low_completion_lessons
            ],
        }
    
    @staticmethod
    def get_all_users(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[User], int]:
        """Get paginated list of all users."""
        query = db.query(User)
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return users, total
    
    @staticmethod
    def export_users_report(db: Session) -> Dict[str, Any]:
        """Export users report."""
        users = db.query(User).filter(User.is_active == True).all()
        
        return {
            "report_type": "users",
            "generated_at": datetime.utcnow().isoformat(),
            "total_records": len(users),
            "data": [
                {
                    "id": str(u.id),
                    "email": u.email,
                    "name": u.get_full_name(),
                    "role": u.role.value,
                    "country": u.country,
                    "created_at": u.created_at.isoformat(),
                    "last_login": u.last_login_at.isoformat() if u.last_login_at else None,
                }
                for u in users
            ],
        }
    
    @staticmethod
    def export_courses_report(db: Session) -> Dict[str, Any]:
        """Export courses report."""
        courses = db.query(Course).all()
        
        return {
            "report_type": "courses",
            "generated_at": datetime.utcnow().isoformat(),
            "total_records": len(courses),
            "data": [
                {
                    "id": str(c.id),
                    "title": c.title,
                    "instructor": c.instructor.get_full_name() if c.instructor else None,
                    "status": c.status.value,
                    "enrollments": c.total_enrollments,
                    "created_at": c.created_at.isoformat(),
                    "published_at": c.published_at.isoformat() if c.published_at else None,
                }
                for c in courses
            ],
        }
    
    @staticmethod
    def export_enrollments_report(db: Session) -> Dict[str, Any]:
        """Export enrollments report."""
        enrollments = db.query(Enrollment).all()
        
        return {
            "report_type": "enrollments",
            "generated_at": datetime.utcnow().isoformat(),
            "total_records": len(enrollments),
            "data": [
                {
                    "id": str(e.id),
                    "user_email": e.user.email if e.user else None,
                    "course_title": e.course.title if e.course else None,
                    "completion_percentage": e.completion_percentage,
                    "is_completed": e.is_completed,
                    "enrolled_at": e.enrolled_at.isoformat(),
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                }
                for e in enrollments
            ],
        }
