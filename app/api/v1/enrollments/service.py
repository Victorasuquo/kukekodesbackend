"""
Enrollment management business logic.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Tuple, Optional
from uuid import UUID
from datetime import datetime
import logging

from app.models.course import Course
from app.models.enrollment import Enrollment, UserProgress, Streak
from app.models.user import User
from app.models.notification import Notification, NotificationType
from app.services.email_service import email_service
from app.db.mongodb import insert_activity
from app.dependencies import NotFoundError, ValidationError, ConflictError

logger = logging.getLogger(__name__)


class EnrollmentService:
    """Service for enrollment operations."""
    
    @staticmethod
    async def enroll_user(
        db: Session,
        user_id: str,
        course_id: str,
    ) -> Enrollment:
        """
        Enroll a user in a course.
        
        Args:
            db: Database session
            user_id: User ID
            course_id: Course ID
        
        Returns:
            Created enrollment
        
        Raises:
            ValidationError: If course not published or user already enrolled
            NotFoundError: If user or course not found
        """
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)
        
        # Get course
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise NotFoundError("Course", course_id)
        
        # Check if course is published
        if not course.is_published():
            raise ValidationError("Cannot enroll in unpublished course")
        
        # Check if already enrolled
        existing = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
        ).first()
        
        if existing:
            raise ConflictError("User is already enrolled in this course")
        
        # Create enrollment
        enrollment = Enrollment(
            user_id=UUID(user_id),
            course_id=UUID(course_id),
        )
        
        try:
            db.add(enrollment)
            db.commit()
            db.refresh(enrollment)
            
            logger.info(f"User {user_id} enrolled in course {course_id}")
            
            # Update course enrollment count
            course.total_enrollments = db.query(Enrollment).filter(
                Enrollment.course_id == course_id,
            ).count()
            db.commit()
            
            # Create notification
            notification = Notification(
                user_id=UUID(user_id),
                title="Course Enrollment 📚",
                message=f"You enrolled in '{course.title}'",
                type=NotificationType.COURSE_UPDATE,
                related_entity_id=UUID(course_id),
                related_entity_type="course",
            )
            db.add(notification)
            db.commit()
            
            # Log activity
            try:
                insert_activity(
                    user_id=user_id,
                    action="enrolled_course",
                    entity_id=course_id,
                    entity_type="course",
                    metadata={"course_title": course.title},
                )
            except Exception as e:
                logger.warning(f"Failed to log activity: {str(e)}")
            
            return enrollment
        
        except IntegrityError:
            db.rollback()
            raise ConflictError("User is already enrolled in this course")
        except Exception as e:
            db.rollback()
            logger.error(f"Error enrolling user: {str(e)}")
            raise
    
    @staticmethod
    def get_user_enrollments(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Enrollment], int]:
        """
        Get all enrollments for a user.
        
        Returns:
            Tuple of (enrollments list, total count)
        """
        query = db.query(Enrollment).filter(Enrollment.user_id == user_id)
        total = query.count()
        
        enrollments = query.order_by(
            Enrollment.enrolled_at.desc()
        ).offset(skip).limit(limit).all()
        
        return enrollments, total
    
    @staticmethod
    def get_enrollment(
        db: Session,
        user_id: str,
        course_id: str,
    ) -> Enrollment:
        """Get specific enrollment."""
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
        ).first()
        
        if not enrollment:
            raise ValidationError("User is not enrolled in this course")
        
        return enrollment
    
    @staticmethod
    def unenroll_user(
        db: Session,
        user_id: str,
        course_id: str,
    ) -> None:
        """
        Unenroll user from course.
        
        Deletes:
        - Enrollment record
        - All user progress on lessons in this course
        
        WARNING: This is permanent!
        """
        try:
            enrollment = EnrollmentService.get_enrollment(db, user_id, course_id)
            
            # Delete all progress on lessons in this course
            progress_records = db.query(UserProgress).filter(
                UserProgress.user_id == user_id,
                UserProgress.course_id == course_id,
            ).all()
            
            for record in progress_records:
                db.delete(record)
            
            # Delete enrollment
            db.delete(enrollment)
            db.commit()
            
            logger.info(f"User {user_id} unenrolled from course {course_id}")
            
            # Log activity
            try:
                insert_activity(
                    user_id=user_id,
                    action="unenrolled_course",
                    entity_id=course_id,
                    entity_type="course",
                )
            except Exception as e:
                logger.warning(f"Failed to log activity: {str(e)}")
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error unenrolling user: {str(e)}")
            raise
    
    @staticmethod
    def is_user_enrolled(
        db: Session,
        user_id: str,
        course_id: str,
    ) -> bool:
        """Check if user is enrolled in course."""
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
        ).first()
        
        return enrollment is not None
    
    @staticmethod
    def get_course_enrollments(
        db: Session,
        course_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Enrollment], int]:
        """Get all enrollments for a course (admin)."""
        query = db.query(Enrollment).filter(Enrollment.course_id == course_id)
        total = query.count()
        
        enrollments = query.order_by(
            Enrollment.enrolled_at.desc()
        ).offset(skip).limit(limit).all()
        
        return enrollments, total