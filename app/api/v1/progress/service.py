"""
Progress tracking business logic.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
import logging
import secrets

from app.models.course import Course, Module, Lesson
from app.models.enrollment import Enrollment, UserProgress
from app.models.progress import Streak, Badge, BadgeAward
from app.models.user import User
from app.models.notification import Notification, NotificationType, NotificationPreference
from app.models.assessment import Certificate
from app.api.v1.quizzes.service import QuizService
from app.services.email_service import email_service
from app.db.mongodb import insert_activity
from app.utils.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class ProgressService:
    """Service for progress tracking operations."""
    
    @staticmethod
    async def mark_lesson_complete(
        db: Session,
        user_id: str,
        lesson_id: str,
        time_spent_minutes: int = 0,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mark a lesson as complete.
        
        Updates:
        1. UserProgress record
        2. Module completion percentage
        3. Course completion percentage
        4. Streak counter
        5. Badges eligibility
        6. Creates notification
        7. Sends email
        8. Recommends next lesson
        """
        try:
            # Get lesson and related data
            lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
            if not lesson:
                raise NotFoundError("Lesson", lesson_id)
            
            module = lesson.module
            course = module.course
            
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotFoundError("User", user_id)

            enrollment = db.query(Enrollment).filter(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course.id,
            ).first()
            if not enrollment:
                raise ValidationError("User is not enrolled in this course")
            
            # Get or create user progress record
            progress = db.query(UserProgress).filter(
                UserProgress.user_id == user_id,
                UserProgress.lesson_id == lesson_id,
            ).first()
            if progress and idempotency_key and progress.last_idempotency_key == idempotency_key:
                return {
                    "lesson_id": str(progress.lesson_id),
                    "course_id": str(progress.course_id),
                    "is_completed": progress.is_completed,
                    "completion_percentage": enrollment.completion_percentage,
                    "idempotent_replay": True,
                }
            
            if not progress:
                progress = UserProgress(
                    user_id=UUID(user_id),
                    lesson_id=UUID(lesson_id),
                    module_id=lesson.module_id,
                    course_id=course.id,
                )
                db.add(progress)
            
            # Mark as complete
            was_previously_complete = progress.is_completed
            progress.mark_complete(time_spent_minutes)
            progress.last_idempotency_key = idempotency_key
            # Make a newly-created progress row visible to the rollup queries
            # before calculating enrollment completion.
            db.flush()

            # Update enrollment
            if enrollment:
                # Calculate total completed lessons in course
                completed_lessons = db.query(UserProgress).filter(
                    UserProgress.user_id == user_id,
                    UserProgress.course_id == course.id,
                    UserProgress.is_completed == True,
                ).count()
                
                total_lessons = db.query(Lesson).join(Module).filter(
                    Module.course_id == course.id,
                ).count()
                
                enrollment.update_progress(completed_lessons, total_lessons)
                enrollment.current_lesson_id = lesson.id
                enrollment.current_module_id = module.id
                enrollment.last_accessed_at = datetime.utcnow()
            
            # Update streak
            streak = db.query(Streak).filter(Streak.user_id == user_id).first()
            if not streak:
                streak = Streak(user_id=UUID(user_id))
                db.add(streak)
            
            streak_incremented = streak.increment_streak()
            
            # Check for badges
            badges_earned = ProgressService._check_badges(
                db=db,
                user_id=user_id,
                lesson_id=lesson_id,
                streak_count=streak.current_streak_count,
                completed_lessons=completed_lessons,
            )
            
            # Commit all changes
            db.commit()
            
            # Create notification
            notification = Notification(
                user_id=UUID(user_id),
                title="Lesson Completed! 🎉",
                message=f"You completed '{lesson.title}'",
                type=NotificationType.LESSON_COMPLETED,
                related_entity_id=UUID(lesson_id),
                related_entity_type="lesson",
            )
            db.add(notification)
            db.commit()
            
            # Send email if first completion
            if not was_previously_complete:
                try:
                    # Get next lesson
                    next_lesson = ProgressService._get_next_lesson(
                        db=db,
                        module=module,
                        current_lesson=lesson,
                    )
                    
                    email_service.send_lesson_completed_email(
                        user_email=user.email,
                        user_name=user.first_name,
                        course_title=course.title,
                        lesson_title=lesson.title,
                        progress_percentage=enrollment.completion_percentage if enrollment else 0,
                        next_lesson_title=next_lesson.title if next_lesson else None,
                        course_url=f"https://kukekodes.com/courses/{course.id}",
                    )
                except Exception as e:
                    logger.warning(f"Failed to send email: {str(e)}")
            
            # Send streak milestone email if milestone
            if streak_incremented and streak.current_streak_count in [7, 14, 30, 60, 90]:
                try:
                    email_service.send_streak_milestone_email(
                        user_email=user.email,
                        user_name=user.first_name,
                        streak_count=streak.current_streak_count,
                        dashboard_url="https://kukekodes.com/dashboard",
                    )
                except Exception as e:
                    logger.warning(f"Failed to send streak email: {str(e)}")
            
            # Log activity
            try:
                insert_activity(
                    user_id=user_id,
                    action="completed_lesson",
                    entity_id=lesson_id,
                    entity_type="lesson",
                    metadata={
                        "course_id": str(course.id),
                        "module_id": str(module.id),
                        "time_spent_minutes": time_spent_minutes,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to log activity: {str(e)}")
            
            # Get next lesson
            next_lesson = ProgressService._get_next_lesson(db, module, lesson)
            
            return {
                "success": True,
                "lesson_id": lesson_id,
                "lesson_status": "completed",
                "lesson_marked_green": True,
                "time_spent_minutes": time_spent_minutes,
                "module_progress": {
                    "completed": db.query(UserProgress).filter(
                        UserProgress.user_id == user_id,
                        UserProgress.module_id == module.id,
                        UserProgress.is_completed == True,
                    ).count(),
                    "total": len(module.lessons),
                },
                "course_progress": {
                    "percentage": enrollment.completion_percentage if enrollment else 0,
                    "completed": completed_lessons,
                    "total": total_lessons,
                },
                "next_lesson": {
                    "id": str(next_lesson.id),
                    "title": next_lesson.title,
                    "module_id": str(next_lesson.module_id),
                } if next_lesson else None,
                "streak": {
                    "current": streak.current_streak_count,
                    "longest": streak.longest_streak_count,
                    "incremented": streak_incremented,
                },
                "badges_earned": [badge.name for badge in badges_earned],
            }
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking lesson complete: {str(e)}")
            raise

    @staticmethod
    def sync_lesson_position(
        db: Session,
        user_id: str,
        lesson_id: str,
        position_seconds: int,
        time_spent_minutes: int,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise NotFoundError(f"Lesson with ID {lesson_id} not found")
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == lesson.module.course_id,
        ).first()
        if not enrollment:
            raise ValidationError("User is not enrolled in this course")
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.lesson_id == lesson_id,
        ).first()
        if progress and progress.last_idempotency_key == idempotency_key:
            return {
                "lesson_id": str(progress.lesson_id),
                "resume_position_seconds": progress.resume_position_seconds,
                "time_spent_minutes": progress.time_spent_minutes,
                "idempotent_replay": True,
            }
        if not progress:
            progress = UserProgress(
                user_id=UUID(user_id),
                lesson_id=lesson.id,
                module_id=lesson.module_id,
                course_id=lesson.module.course_id,
            )
            db.add(progress)
        progress.resume_position_seconds = position_seconds
        progress.time_spent_minutes = max(progress.time_spent_minutes or 0, time_spent_minutes)
        progress.last_idempotency_key = idempotency_key
        enrollment.current_module_id = lesson.module_id
        enrollment.current_lesson_id = lesson.id
        enrollment.last_accessed_at = datetime.utcnow()
        db.commit()
        return {
            "lesson_id": str(progress.lesson_id),
            "resume_position_seconds": progress.resume_position_seconds,
            "time_spent_minutes": progress.time_spent_minutes,
            "idempotent_replay": False,
        }
    
    @staticmethod
    def get_lesson_progress(
        db: Session,
        user_id: str,
        lesson_id: str,
    ) -> Dict[str, Any]:
        """Get user's progress for a specific lesson."""
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.lesson_id == lesson_id,
        ).first()
        
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise NotFoundError("Lesson", lesson_id)
        
        if not progress:
            return {
                "user_id": user_id,
                "lesson_id": lesson_id,
                "module_id": lesson.module_id,
                "course_id": lesson.module.course_id,
                "is_completed": False,
                "completed_at": None,
                "time_spent_minutes": 0,
                "resume_position_seconds": 0,
            }
        
        return {
            "user_id": progress.user_id,
            "lesson_id": lesson_id,
            "module_id": progress.module_id,
            "course_id": progress.course_id,
            "is_completed": progress.is_completed,
            "completed_at": progress.completed_at,
            "time_spent_minutes": progress.time_spent_minutes,
            "resume_position_seconds": progress.resume_position_seconds,
        }
    
    @staticmethod
    def get_module_progress(
        db: Session,
        user_id: str,
        module_id: str,
    ) -> Dict[str, Any]:
        """Get user's progress for a specific module."""
        module = db.query(Module).filter(Module.id == module_id).first()
        if not module:
            raise NotFoundError("Module", module_id)
        
        completed = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.module_id == module_id,
            UserProgress.is_completed == True,
        ).count()
        
        total = len(module.lessons)
        percentage = (completed / total * 100) if total > 0 else 0
        
        return {
            "module_id": module_id,
            "module_title": module.title,
            "completion_percentage": percentage,
            "completed_lessons": completed,
            "total_lessons": total,
            "lessons": [
                {
                    "id": str(lesson.id),
                    "title": lesson.title,
                    "order": lesson.order,
                    "is_completed": db.query(UserProgress).filter(
                        UserProgress.user_id == user_id,
                        UserProgress.lesson_id == lesson.id,
                    ).first() is not None,
                }
                for lesson in sorted(module.lessons, key=lambda x: x.order)
            ],
        }
    
    @staticmethod
    def get_course_progress(
        db: Session,
        user_id: str,
        course_id: str,
    ) -> Dict[str, Any]:
        """Get user's progress for a specific course."""
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise NotFoundError("Course", course_id)
        
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
        ).first()
        
        if not enrollment:
            raise ValidationError("User is not enrolled in this course")
        
        modules_progress = []
        for module in sorted(course.modules, key=lambda x: x.order):
            completed = db.query(UserProgress).filter(
                UserProgress.user_id == user_id,
                UserProgress.module_id == module.id,
                UserProgress.is_completed == True,
            ).count()
            
            total = len(module.lessons)
            percentage = (completed / total * 100) if total > 0 else 0
            
            modules_progress.append({
                "module_id": str(module.id),
                "module_title": module.title,
                "completion_percentage": percentage,
                "completed_lessons": completed,
                "total_lessons": total,
                "lessons": [
                    {
                        "id": str(lesson.id),
                        "title": lesson.title,
                        "order": lesson.order,
                        "is_completed": db.query(UserProgress).filter(
                            UserProgress.user_id == user_id,
                            UserProgress.lesson_id == lesson.id,
                            UserProgress.is_completed.is_(True),
                        ).first() is not None,
                    }
                    for lesson in sorted(module.lessons, key=lambda item: item.order)
                ],
            })
        
        # Calculate remaining time
        total_duration = sum(
            lesson.duration_minutes or 0
            for module in course.modules
            for lesson in module.lessons
        )
        
        spent_time = db.query(func.sum(UserProgress.time_spent_minutes)).filter(
            UserProgress.user_id == user_id,
            UserProgress.course_id == course_id,
        ).scalar() or 0

        completed_lessons_count = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.course_id == course_id,
            UserProgress.is_completed.is_(True),
        ).count()
        completed_modules_count = sum(
            1 for module_progress in modules_progress
            if module_progress["total_lessons"] > 0
            and module_progress["completed_lessons"] == module_progress["total_lessons"]
        )
        current_module = next(
            ({"id": str(module.id), "title": module.title} for module in course.modules if module.id == enrollment.current_module_id),
            None,
        )
        current_lesson = next(
            (
                {"id": str(lesson.id), "title": lesson.title}
                for module in course.modules
                for lesson in module.lessons
                if lesson.id == enrollment.current_lesson_id
            ),
            None,
        )
        
        return {
            "user_id": user_id,
            "course_id": course_id,
            "course_title": course.title,
            "total_modules": len(course.modules),
            "completed_modules": completed_modules_count,
            "completion_percentage": enrollment.completion_percentage,
            "is_completed": enrollment.is_completed,
            "current_module": current_module,
            "current_lesson": current_lesson,
            "modules": modules_progress,
            "total_lessons": sum(len(m.lessons) for m in course.modules),
            "completed_lessons": completed_lessons_count,
            "estimated_time_remaining_hours": round(max(0, total_duration - int(spent_time)) / 60, 2),
        }
    
    @staticmethod
    async def get_user_dashboard(
        db: Session,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get comprehensive user dashboard."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)
        
        # Get enrolled courses
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
                "completion_percentage": enrollment.completion_percentage,
                "is_completed": enrollment.is_completed,
                "enrolled_at": enrollment.enrolled_at.isoformat(),
                "progress_bar": int(enrollment.completion_percentage),
            })
        
        # Get streak
        streak = db.query(Streak).filter(Streak.user_id == user_id).first()
        streak_data = {
            "current": streak.current_streak_count if streak else 0,
            "longest": streak.longest_streak_count if streak else 0,
            "fire_emoji": "🔥" if streak and streak.current_streak_count else "🔲",
        } if streak else {"current": 0, "longest": 0, "fire_emoji": "🔲"}
        
        # Get recent badges (via BadgeAward)
        recent_awards = db.query(BadgeAward).filter(
            BadgeAward.user_id == user_id,
        ).order_by(BadgeAward.earned_at.desc()).limit(5).all()
        
        # Get stats
        stats = {
            "total_courses_enrolled": len(enrollments),
            "total_courses_completed": sum(1 for e in enrollments if e.is_completed),
            "total_lessons_completed": db.query(UserProgress).filter(
                UserProgress.user_id == user_id,
                UserProgress.is_completed == True,
            ).count(),
            "total_time_spent_hours": round((db.query(func.sum(UserProgress.time_spent_minutes)).filter(
                UserProgress.user_id == user_id,
            ).scalar() or 0) / 60, 2),
            "badges_earned": len(recent_awards),
        }
        
        return {
            "user_id": user_id,
            "user_name": user.get_full_name(),
            "profile_picture_url": user.profile_picture_url,
            "enrolled_courses": courses,
            "streak": streak_data,
            "recent_badges": [
                {
                    "id": str(award.badge.id),
                    "name": award.badge.name,
                    "icon_url": award.badge.icon_url,
                    "earned_at": award.earned_at.isoformat(),
                }
                for award in recent_awards
            ],
            "statistics": stats,
        }
    
    @staticmethod
    def get_user_stats(db: Session, user_id: str) -> Dict[str, Any]:
        """Get user learning statistics."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)
        
        enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()
        completed_lessons = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.is_completed == True,
        )
        
        streak = db.query(Streak).filter(Streak.user_id == user_id).first()
        
        badge_awards = db.query(BadgeAward).filter(
            BadgeAward.user_id == user_id,
        ).all()
        
        return {
            "total_courses_enrolled": len(enrollments),
            "total_courses_completed": sum(1 for e in enrollments if e.is_completed),
            "total_lessons_completed": completed_lessons.count(),
            "total_time_spent_hours": round((completed_lessons.with_entities(
                func.sum(UserProgress.time_spent_minutes)
            ).scalar() or 0) / 60, 1),
            "current_streak_days": streak.current_streak_count if streak else 0,
            "longest_streak_days": streak.longest_streak_count if streak else 0,
            "total_badges": len(badge_awards),
            "xp_points": len(badge_awards) * 50 + sum(1 for e in enrollments if e.is_completed) * 100,  # Simple XP calc
        }
    
    @staticmethod
    def get_learning_history(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Get user's learning activity history."""
        history = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.is_completed == True,
        ).order_by(UserProgress.completed_at.desc()).offset(skip).limit(limit).all()
        
        total = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.is_completed == True,
        ).count()
        
        return {
            "activities": [
                {
                    "lesson_id": str(item.lesson_id),
                    "lesson_title": item.lesson.title,
                    "course_id": str(item.course_id),
                    "course_title": item.lesson.module.course.title,
                    "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                    "time_spent_minutes": item.time_spent_minutes,
                }
                for item in history
            ],
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    
    @staticmethod
    def reset_lesson_progress(
        db: Session,
        user_id: str,
        lesson_id: str,
    ) -> None:
        """Reset user's progress on a specific lesson."""
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.lesson_id == lesson_id,
        ).first()
        
        if progress:
            db.delete(progress)
            db.commit()
            logger.info(f"Progress reset for user {user_id} on lesson {lesson_id}")
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    @staticmethod
    def _check_badges(
        db: Session,
        user_id: str,
        lesson_id: str,
        streak_count: int,
        completed_lessons: int,
    ) -> List[Badge]:
        """
        Check and award badges based on progress.
        
        Returns list of newly earned badges.
        """
        earned_badges = []
        
        # Get user's existing badge IDs (via BadgeAward)
        existing_awards = db.query(BadgeAward.badge_id).filter(
            BadgeAward.user_id == user_id,
        ).all()
        
        user_badge_ids = [award[0] for award in existing_awards]
        
        # Check for "First Lesson" badge
        if completed_lessons == 1:
            badge = db.query(Badge).filter(Badge.name == "First Lesson").first()
            if badge and badge.id not in user_badge_ids:
                award = BadgeAward(
                    user_id=user_id,
                    badge_id=badge.id,
                    context=f'{{"lesson_id": "{lesson_id}"}}',
                )
                db.add(award)
                earned_badges.append(badge)
        
        # Check for streak badges
        streak_badges = {
            7: "7-Day Streak",
            14: "2-Week Streak",
            30: "30-Day Streak",
            60: "60-Day Streak",
            90: "90-Day Streak",
        }
        
        for days, badge_name in streak_badges.items():
            if streak_count >= days:
                badge = db.query(Badge).filter(Badge.name == badge_name).first()
                if badge and badge.id not in user_badge_ids:
                    award = BadgeAward(
                        user_id=user_id,
                        badge_id=badge.id,
                        context=f'{{"streak_days": {days}}}',
                    )
                    db.add(award)
                    earned_badges.append(badge)
        
        # Check for completion badges (by course)
        # This would be triggered by enrollment completion
        
        if earned_badges:
            db.commit()
        
        return earned_badges
    
    @staticmethod
    def _get_next_lesson(
        db: Session,
        module: Module,
        current_lesson: Lesson,
    ) -> Optional[Lesson]:
        """Get the next lesson in sequence."""
        # Next lesson in same module
        next_in_module = db.query(Lesson).filter(
            Lesson.module_id == module.id,
            Lesson.order > current_lesson.order,
        ).order_by(Lesson.order).first()
        
        if next_in_module:
            return next_in_module
        
        # Next lesson in next module
        next_module = db.query(Module).filter(
            Module.course_id == module.course_id,
            Module.order > module.order,
        ).order_by(Module.order).first()
        
        if next_module:
            return db.query(Lesson).filter(
                Lesson.module_id == next_module.id,
            ).order_by(Lesson.order).first()
        
        return None
    
    # ========================================================================
    # CERTIFICATES
    # ========================================================================
    
    @staticmethod
    def _ensure_certificate(db: Session, enrollment: Enrollment) -> Certificate:
        certificate = db.query(Certificate).filter(
            Certificate.user_id == enrollment.user_id,
            Certificate.course_id == enrollment.course_id,
        ).first()
        if certificate:
            return certificate

        verification_code = secrets.token_hex(8).upper()
        certificate = Certificate(
            user_id=enrollment.user_id,
            course_id=enrollment.course_id,
            certificate_id=f"CERT-{verification_code}",
            verification_code=verification_code,
        )
        db.add(certificate)
        db.commit()
        db.refresh(certificate)
        return certificate

    @staticmethod
    def _serialize_certificate(certificate: Certificate) -> Dict[str, Any]:
        user = certificate.user
        course = certificate.course
        return {
            "id": str(certificate.id),
            "certificate_id": certificate.certificate_id,
            "user_id": str(certificate.user_id),
            "user_name": user.get_full_name(),
            "course_id": str(certificate.course_id),
            "course_title": course.title,
            "course_description": course.description,
            "skill_level": course.skill_level.value,
            "completed_at": certificate.issued_at.isoformat(),
            "issued_at": certificate.issued_at.isoformat(),
            "verification_code": certificate.verification_code,
            "verification_url": f"/api/v1/progress/verify-certificate/{certificate.verification_code}",
            "file_key": certificate.file_key,
            "is_valid": certificate.revoked_at is None,
            "issued_by": "KukeKodes",
        }

    @staticmethod
    async def get_certificate(
        db: Session,
        user_id: str,
        course_id: str,
    ) -> Dict[str, Any]:
        """
        Get certificate for a completed course.
        
        Args:
            db: Database session
            user_id: User ID
            course_id: Course ID
        
        Returns:
            Certificate details
        
        Raises:
            NotFoundError: If enrollment not found
            ValidationError: If course not completed
        """
        # Get enrollment
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
        ).first()
        
        if not enrollment:
            raise NotFoundError("Enrollment not found")
        
        if not enrollment.is_completed:
            raise ValidationError("Course not completed yet. Complete all lessons to earn your certificate.")
        if not QuizService.all_required_passed(db, user_id, course_id):
            raise ValidationError("Pass every published course quiz to earn your certificate.")
        return ProgressService._serialize_certificate(ProgressService._ensure_certificate(db, enrollment))
    
    @staticmethod
    async def get_user_certificates(
        db: Session,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get all certificates for a user."""
        # Get all completed enrollments
        completed_enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.is_completed == True,
        ).all()
        
        user = db.query(User).filter(User.id == user_id).first()
        
        certificates = []
        for enrollment in completed_enrollments:
            if QuizService.all_required_passed(db, user_id, str(enrollment.course_id)):
                certificates.append(ProgressService._serialize_certificate(
                    ProgressService._ensure_certificate(db, enrollment)
                ))
        
        return {
            "user_id": str(user_id),
            "user_name": user.get_full_name(),
            "total_certificates": len(certificates),
            "certificates": certificates,
        }
    
    @staticmethod
    def verify_certificate(
        db: Session,
        verification_code: str,
    ) -> Dict[str, Any]:
        """
        Verify a certificate by its verification code.
        
        This is a public endpoint that can be used by employers/third parties.
        """
        certificate = db.query(Certificate).filter(
            Certificate.verification_code == verification_code.upper(),
            Certificate.revoked_at.is_(None),
        ).first()
        if certificate:
            result = ProgressService._serialize_certificate(certificate)
            result["message"] = "This certificate is valid and was issued by KukeKodes."
            return result
        
        return {
            "is_valid": False,
            "message": "Certificate not found or invalid verification code.",
        }
