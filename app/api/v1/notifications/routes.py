"""
Notification API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.postgres import get_db
from app.security import get_current_user
from app.models.user import User
from app.api.v1.notifications.service import NotificationService
from app.api.v1.notifications.schemas import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
    MarkReadRequest,
    MarkAllReadResponse,
    NotificationPreferencesResponse,
    UpdatePreferencesRequest,
)

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"],
)


# ============================================================================
# GET NOTIFICATIONS
# ============================================================================

@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of notifications for current user.
    
    - **page**: Page number (starts at 1)
    - **page_size**: Number of notifications per page (max 100)
    - **unread_only**: If true, only return unread notifications
    """
    skip = (page - 1) * page_size
    
    notifications, total, unread_count = NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=page_size,
        unread_only=unread_only,
    )
    
    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=n.id,
                title=n.title,
                message=n.message,
                type=n.type,
                is_read=n.is_read,
                related_entity_id=n.related_entity_id,
                related_entity_type=n.related_entity_type,
                icon_emoji=n.get_icon_emoji(),
                created_at=n.created_at,
                read_at=n.read_at,
            )
            for n in notifications
        ],
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get count of unread notifications."""
    count = NotificationService.get_unread_count(db, current_user.id)
    return UnreadCountResponse(unread_count=count)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific notification."""
    notification = NotificationService.get_notification(db, notification_id, current_user.id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    
    return NotificationResponse(
        id=notification.id,
        title=notification.title,
        message=notification.message,
        type=notification.type,
        is_read=notification.is_read,
        related_entity_id=notification.related_entity_id,
        related_entity_type=notification.related_entity_type,
        icon_emoji=notification.get_icon_emoji(),
        created_at=notification.created_at,
        read_at=notification.read_at,
    )


# ============================================================================
# MARK AS READ
# ============================================================================

@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a single notification as read."""
    notification = NotificationService.mark_as_read(db, notification_id, current_user.id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    
    return NotificationResponse(
        id=notification.id,
        title=notification.title,
        message=notification.message,
        type=notification.type,
        is_read=notification.is_read,
        related_entity_id=notification.related_entity_id,
        related_entity_type=notification.related_entity_type,
        icon_emoji=notification.get_icon_emoji(),
        created_at=notification.created_at,
        read_at=notification.read_at,
    )


@router.post("/mark-read", response_model=MarkAllReadResponse)
async def mark_multiple_read(
    request: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark multiple notifications as read."""
    count = NotificationService.mark_multiple_as_read(
        db, 
        request.notification_ids, 
        current_user.id
    )
    
    return MarkAllReadResponse(
        marked_count=count,
        message=f"Marked {count} notification(s) as read",
    )


@router.post("/mark-all-read", response_model=MarkAllReadResponse)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read."""
    count = NotificationService.mark_all_as_read(db, current_user.id)
    
    return MarkAllReadResponse(
        marked_count=count,
        message=f"Marked {count} notification(s) as read",
    )


# ============================================================================
# DELETE NOTIFICATIONS
# ============================================================================

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a notification."""
    deleted = NotificationService.delete_notification(db, notification_id, current_user.id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )


@router.delete("/cleanup/old")
async def cleanup_old_notifications(
    days_old: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete read notifications older than specified days."""
    count = NotificationService.delete_old_notifications(db, current_user.id, days_old)
    
    return {
        "deleted_count": count,
        "message": f"Deleted {count} old notification(s)",
    }


# ============================================================================
# NOTIFICATION PREFERENCES
# ============================================================================

@router.get("/preferences/me", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's notification preferences."""
    prefs = NotificationService.get_or_create_preferences(db, current_user.id)
    
    return NotificationPreferencesResponse(
        email_on_lesson_complete=prefs.email_on_lesson_complete,
        email_on_course_complete=prefs.email_on_course_complete,
        email_on_badge_earned=prefs.email_on_badge_earned,
        email_on_streak_milestone=prefs.email_on_streak_milestone,
        email_on_course_update=prefs.email_on_course_update,
        email_on_reply=prefs.email_on_reply,
        receive_weekly_summary=prefs.receive_weekly_summary,
        weekly_summary_day=prefs.weekly_summary_day,
        all_emails_enabled=prefs.all_emails_enabled,
    )


@router.put("/preferences/me", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    request: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's notification preferences."""
    prefs = NotificationService.update_preferences(
        db=db,
        user_id=current_user.id,
        **request.model_dump(exclude_unset=True),
    )
    
    return NotificationPreferencesResponse(
        email_on_lesson_complete=prefs.email_on_lesson_complete,
        email_on_course_complete=prefs.email_on_course_complete,
        email_on_badge_earned=prefs.email_on_badge_earned,
        email_on_streak_milestone=prefs.email_on_streak_milestone,
        email_on_course_update=prefs.email_on_course_update,
        email_on_reply=prefs.email_on_reply,
        receive_weekly_summary=prefs.receive_weekly_summary,
        weekly_summary_day=prefs.weekly_summary_day,
        all_emails_enabled=prefs.all_emails_enabled,
    )
