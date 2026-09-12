"""
Notification service for managing user notifications.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Tuple, Optional
from datetime import datetime
from uuid import UUID
import logging

from app.models.notification import Notification, NotificationType, NotificationPreference
from app.models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for notification operations."""
    
    # ========================================================================
    # GET NOTIFICATIONS
    # ========================================================================
    
    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
    ) -> Tuple[List[Notification], int, int]:
        """
        Get paginated notifications for a user.
        
        Returns:
            Tuple of (notifications, total_count, unread_count)
        """
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        total = query.count()
        unread = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
        
        notifications = query.order_by(
            Notification.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return notifications, total, unread
    
    @staticmethod
    def get_unread_count(db: Session, user_id: UUID) -> int:
        """Get count of unread notifications."""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
    
    @staticmethod
    def get_notification(db: Session, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        """Get a specific notification."""
        return db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
    
    # ========================================================================
    # CREATE NOTIFICATIONS
    # ========================================================================
    
    @staticmethod
    def create_notification(
        db: Session,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: NotificationType,
        related_entity_id: Optional[UUID] = None,
        related_entity_type: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            related_entity_id=related_entity_id,
            related_entity_type=related_entity_type,
            extra_data=extra_data,
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        logger.info(f"Created notification for user {user_id}: {title}")
        return notification
    
    @staticmethod
    def create_enrollment_notification(db: Session, user_id: UUID, course_title: str, course_id: UUID) -> Notification:
        """Create notification when user enrolls in a course."""
        return NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title="Course Enrollment",
            message=f"You've successfully enrolled in '{course_title}'. Start learning now!",
            notification_type=NotificationType.ENROLLMENT,
            related_entity_id=course_id,
            related_entity_type="course",
        )
    
    @staticmethod
    def create_lesson_completion_notification(
        db: Session,
        user_id: UUID,
        lesson_title: str,
        course_title: str,
        lesson_id: UUID,
    ) -> Notification:
        """Create notification when user completes a lesson."""
        return NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title="Lesson Completed!",
            message=f"Great job! You've completed '{lesson_title}' in {course_title}.",
            notification_type=NotificationType.LESSON_COMPLETED,
            related_entity_id=lesson_id,
            related_entity_type="lesson",
        )
    
    @staticmethod
    def create_course_completion_notification(
        db: Session,
        user_id: UUID,
        course_title: str,
        course_id: UUID,
    ) -> Notification:
        """Create notification when user completes a course."""
        return NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title="🎉 Course Completed!",
            message=f"Congratulations! You've completed '{course_title}'. Your certificate is ready!",
            notification_type=NotificationType.COURSE_COMPLETED,
            related_entity_id=course_id,
            related_entity_type="course",
        )
    
    @staticmethod
    def create_badge_earned_notification(
        db: Session,
        user_id: UUID,
        badge_name: str,
        badge_id: UUID,
    ) -> Notification:
        """Create notification when user earns a badge."""
        return NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title="🏆 New Badge Earned!",
            message=f"You've earned the '{badge_name}' badge!",
            notification_type=NotificationType.BADGE_EARNED,
            related_entity_id=badge_id,
            related_entity_type="badge",
        )
    
    @staticmethod
    def create_streak_notification(
        db: Session,
        user_id: UUID,
        streak_count: int,
    ) -> Notification:
        """Create notification for streak milestones."""
        return NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title=f"🔥 {streak_count} Day Streak!",
            message=f"You're on fire! You've maintained a {streak_count} day learning streak!",
            notification_type=NotificationType.STREAK_MILESTONE,
            extra_data={"streak_count": streak_count},
        )
    
    # ========================================================================
    # UPDATE NOTIFICATIONS
    # ========================================================================
    
    @staticmethod
    def mark_as_read(db: Session, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        """Mark a notification as read."""
        notification = NotificationService.get_notification(db, notification_id, user_id)
        if notification:
            notification.mark_as_read()
            db.commit()
            db.refresh(notification)
        return notification
    
    @staticmethod
    def mark_multiple_as_read(db: Session, notification_ids: List[UUID], user_id: UUID) -> int:
        """Mark multiple notifications as read. Returns count of updated."""
        count = db.query(Notification).filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({
            Notification.is_read: True,
            Notification.read_at: datetime.utcnow()
        }, synchronize_session=False)
        
        db.commit()
        return count
    
    @staticmethod
    def mark_all_as_read(db: Session, user_id: UUID) -> int:
        """Mark all notifications as read. Returns count of updated."""
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({
            Notification.is_read: True,
            Notification.read_at: datetime.utcnow()
        }, synchronize_session=False)
        
        db.commit()
        return count
    
    # ========================================================================
    # DELETE NOTIFICATIONS
    # ========================================================================
    
    @staticmethod
    def delete_notification(db: Session, notification_id: UUID, user_id: UUID) -> bool:
        """Delete a notification."""
        notification = NotificationService.get_notification(db, notification_id, user_id)
        if notification:
            db.delete(notification)
            db.commit()
            return True
        return False
    
    @staticmethod
    def delete_old_notifications(db: Session, user_id: UUID, days_old: int = 30) -> int:
        """Delete notifications older than specified days."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.created_at < cutoff,
            Notification.is_read == True
        ).delete(synchronize_session=False)
        
        db.commit()
        return count
    
    # ========================================================================
    # NOTIFICATION PREFERENCES
    # ========================================================================
    
    @staticmethod
    def get_preferences(db: Session, user_id: UUID) -> Optional[NotificationPreference]:
        """Get user's notification preferences."""
        return db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()
    
    @staticmethod
    def get_or_create_preferences(db: Session, user_id: UUID) -> NotificationPreference:
        """Get or create notification preferences."""
        prefs = NotificationService.get_preferences(db, user_id)
        if not prefs:
            prefs = NotificationPreference(user_id=user_id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        return prefs
    
    @staticmethod
    def update_preferences(
        db: Session,
        user_id: UUID,
        **kwargs
    ) -> NotificationPreference:
        """Update notification preferences."""
        prefs = NotificationService.get_or_create_preferences(db, user_id)
        
        for key, value in kwargs.items():
            if hasattr(prefs, key) and value is not None:
                setattr(prefs, key, value)
        
        db.commit()
        db.refresh(prefs)
        return prefs
