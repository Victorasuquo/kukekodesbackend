"""
User profile and dashboard business logic.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
import logging

from app.models.user import User, UserProfile
from app.models.enrollment import Enrollment, UserProgress
from app.models.progress import Streak, Badge, BadgeAward
from app.models.notification import NotificationPreference
from app.security import verify_password, hash_password
from app.utils.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class UserService:
    """Service for user profile operations."""
    
    @staticmethod
    def get_user_profile(db: Session, user_id: str) -> Dict[str, Any]:
        """Get user profile."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)
        
        # Get extended profile
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
        ).first()
        
        return {
            "user_id": user_id,
            "learner_id": user.learner_id,
            "email": user.contact_email or user.email,
            "contact_email": user.contact_email or user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "bio": user.bio,
            "profile_picture_url": user.profile_picture_url,
            "country": user.country,
            "timezone": user.timezone,
            "preferred_language": user.preferred_language,
            "role": user.role.value,
            "created_at": user.created_at.isoformat(),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "is_email_verified": user.is_email_verified,
            "learning_goals": profile.learning_goals if profile else None,
            "current_job_title": profile.current_job_title if profile else None,
            "company": profile.company if profile else None,
        }
    
    @staticmethod
    def update_user_profile(
        db: Session,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        bio: Optional[str] = None,
        country: Optional[str] = None,
        timezone: Optional[str] = None,
        preferred_language: Optional[str] = None,
        profile_picture_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update user profile."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)
        
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if bio:
            user.bio = bio
        if country:
            user.country = country
        if timezone:
            user.timezone = timezone
        if preferred_language:
            user.preferred_language = preferred_language
        if profile_picture_url:
            user.profile_picture_url = profile_picture_url
        
        db.commit()
        
        logger.info(f"User profile updated: {user_id}")
        
        return UserService.get_user_profile(db, user_id)
    
    @staticmethod
    def get_user_dashboard(db: Session, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user dashboard."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)
        
        # Enrolled courses
        enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
        ).all()
        
        courses = []
        for enrollment in enrollments:
            course = enrollment.course
            courses.append({
                "course_id": str(course.id),
                "course_title": course.title,
                "cover_image_url": course.cover_image_url,
                "completion_percentage": round(enrollment.completion_percentage, 2),
                "is_completed": enrollment.is_completed,
                "enrolled_at": enrollment.enrolled_at.isoformat(),
            })
        
        # Sort by completion percentage (in progress first)
        courses.sort(key=lambda x: (x["is_completed"], -x["completion_percentage"]))
        
        # Get streak
        streak = db.query(Streak).filter(Streak.user_id == user_id).first()
        
        # Get badges (via BadgeAward)
        badge_awards = db.query(BadgeAward).filter(
            BadgeAward.user_id == user_id,
        ).order_by(BadgeAward.earned_at.desc()).limit(5).all()
        
        # Get statistics
        lessons_completed = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.is_completed == True,
        ).count()
        
        total_time = db.query(func.sum(UserProgress.time_spent_minutes)).filter(
            UserProgress.user_id == user_id,
        ).scalar() or 0
        
        return {
            "user_id": user_id,
            "user_name": user.get_full_name(),
            "profile_picture_url": user.profile_picture_url,
            "in_progress_courses": sum(1 for c in courses if not c["is_completed"]),
            "completed_courses": sum(1 for c in courses if c["is_completed"]),
            "enrolled_courses": courses,
            "streak": {
                "current": streak.current_streak_count if streak else 0,
                "longest": streak.longest_streak_count if streak else 0,
                "fire_emoji": "🔥" * min(streak.current_streak_count // 7 + 1, 5) if streak and streak.current_streak_count > 0 else "🔲",
            },
            "recent_achievements": [
                {
                    "id": str(award.badge.id),
                    "name": award.badge.name,
                    "icon_url": award.badge.icon_url,
                    "earned_at": award.earned_at.isoformat(),
                }
                for award in badge_awards
            ],
            "statistics": {
                "total_courses_enrolled": len(enrollments),
                "total_courses_completed": sum(1 for e in enrollments if e.is_completed),
                "total_lessons_completed": lessons_completed,
                "total_time_spent_hours": round(total_time / 60, 1),
                "badges_earned": db.query(BadgeAward).filter(
                    BadgeAward.user_id == user_id,
                ).count(),
            },
        }
    
    @staticmethod
    def get_enrolled_courses(db: Session, user_id: str) -> List[Dict[str, Any]]:
        """Get all courses user is enrolled in."""
        enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
        ).order_by(Enrollment.enrolled_at.desc()).all()
        
        courses = []
        for enrollment in enrollments:
            course = enrollment.course
            
            # Get next lesson
            next_lesson = None
            if enrollment.current_lesson_id:
                next_lesson = db.query(UserProgress).filter(
                    UserProgress.user_id == user_id,
                    UserProgress.course_id == course.id,
                    UserProgress.is_completed == False,
                ).first()
            
            courses.append({
                "course_id": str(course.id),
                "course_title": course.title,
                "course_description": course.description,
                "cover_image_url": course.cover_image_url,
                "skill_level": course.skill_level.value,
                "completion_percentage": round(enrollment.completion_percentage, 2),
                "is_completed": enrollment.is_completed,
                "enrolled_at": enrollment.enrolled_at.isoformat(),
                "completed_at": enrollment.completed_at.isoformat() if enrollment.completed_at else None,
                "current_module_id": str(enrollment.current_module_id) if enrollment.current_module_id else None,
                "current_lesson_id": str(enrollment.current_lesson_id) if enrollment.current_lesson_id else None,
                "lessons_completed": db.query(UserProgress).filter(
                    UserProgress.user_id == user_id,
                    UserProgress.course_id == course.id,
                    UserProgress.is_completed == True,
                ).count(),
                "total_lessons": db.query(UserProgress).filter(
                    UserProgress.course_id == course.id,
                ).count(),
            })
        
        return courses
    
    @staticmethod
    def get_public_profile(db: Session, user_id: str) -> Dict[str, Any]:
        """Get public user profile."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)
        
        # Get profile preference
        profile_pref = db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
        ).first()
        
        is_public = profile_pref.profile_is_public if profile_pref else False
        
        if not is_public:
            return {
                "user_id": user_id,
                "user_name": user.get_full_name(),
                "profile_picture_url": user.profile_picture_url,
                "is_public": False,
                "message": "This profile is private",
            }
        
        # Get public info
        badge_awards = db.query(BadgeAward).filter(
            BadgeAward.user_id == user_id,
        ).all()
        
        completed_courses = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.is_completed == True,
        ).count()
        
        streak = db.query(Streak).filter(Streak.user_id == user_id).first()
        
        return {
            "user_id": user_id,
            "user_name": user.get_full_name(),
            "profile_picture_url": user.profile_picture_url,
            "bio": user.bio,
            "country": user.country,
            "is_public": True,
            "completed_courses": completed_courses,
            "current_streak_days": streak.current_streak_count if streak else 0,
            "longest_streak_days": streak.longest_streak_count if streak else 0,
            "badges_earned": [
                {
                    "id": str(award.badge.id),
                    "name": award.badge.name,
                    "icon_url": award.badge.icon_url,
                }
                for award in badge_awards
            ] if profile_pref and profile_pref.show_badges_publicly else [],
        }
    
    @staticmethod
    def get_notification_preferences(db: Session, user_id: str) -> Dict[str, Any]:
        """Get user's notification preferences."""
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
        ).first()
        
        if not prefs:
            return {
                "all_emails_enabled": True,
                "email_on_lesson_complete": True,
                "email_on_course_complete": True,
                "email_on_badge_earned": True,
                "email_on_streak_milestone": True,
                "receive_weekly_summary": True,
            }
        
        return {
            "all_emails_enabled": prefs.all_emails_enabled,
            "email_on_lesson_complete": prefs.email_on_lesson_complete,
            "email_on_course_complete": prefs.email_on_course_complete,
            "email_on_badge_earned": prefs.email_on_badge_earned,
            "email_on_streak_milestone": prefs.email_on_streak_milestone,
            "email_on_course_update": prefs.email_on_course_update,
            "email_on_reply": prefs.email_on_reply,
            "receive_weekly_summary": prefs.receive_weekly_summary,
            "weekly_summary_day": prefs.weekly_summary_day,
        }
    
    @staticmethod
    def update_notification_preferences(
        db: Session,
        user_id: str,
        preferences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update notification preferences."""
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
        ).first()
        
        if not prefs:
            prefs = NotificationPreference(user_id=UUID(user_id))
            db.add(prefs)
        
        # Update fields
        if "all_emails_enabled" in preferences:
            prefs.all_emails_enabled = preferences["all_emails_enabled"]
        if "email_on_lesson_complete" in preferences:
            prefs.email_on_lesson_complete = preferences["email_on_lesson_complete"]
        if "email_on_course_complete" in preferences:
            prefs.email_on_course_complete = preferences["email_on_course_complete"]
        if "email_on_badge_earned" in preferences:
            prefs.email_on_badge_earned = preferences["email_on_badge_earned"]
        if "email_on_streak_milestone" in preferences:
            prefs.email_on_streak_milestone = preferences["email_on_streak_milestone"]
        if "receive_weekly_summary" in preferences:
            prefs.receive_weekly_summary = preferences["receive_weekly_summary"]
        if "weekly_summary_day" in preferences:
            prefs.weekly_summary_day = preferences["weekly_summary_day"]
        
        db.commit()
        
        logger.info(f"Notification preferences updated for user {user_id}")
        
        return UserService.get_notification_preferences(db, user_id)
    
    @staticmethod
    def change_password(
        db: Session,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user password."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)
        
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise ValidationError("Current password is incorrect")
        
        # Update password
        user.password_hash = hash_password(new_password)
        db.commit()
        
        logger.info(f"Password changed for user {user_id}")
        
        return True
    
    @staticmethod
    def deactivate_account(db: Session, user_id: str) -> None:
        """Deactivate user account."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)
        
        user.is_active = False
        db.commit()
        
        logger.info(f"Account deactivated for user {user_id}")
