"""
Lesson management business logic.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging
import re

from app.models.course import Course, Module, Lesson, LessonStatus
from app.utils.exceptions import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class LessonService:
    """Service for lesson operations."""
    
    @staticmethod
    def get_lesson(db: Session, lesson_id: str) -> Lesson:
        """Get a single lesson by ID."""
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise NotFoundError(f"Lesson with ID {lesson_id} not found")
        return lesson
    
    @staticmethod
    def get_lessons_by_module(db: Session, module_id: str) -> List[Lesson]:
        """Get all lessons for a module."""
        lessons = db.query(Lesson).filter(
            Lesson.module_id == module_id
        ).order_by(Lesson.order).all()
        return lessons
    
    @staticmethod
    def _extract_youtube_video_id(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'(?:youtube\.com/watch\?.*v=)([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def create_lesson(
        db: Session,
        module_id: str,
        title: str,
        description: Optional[str] = None,
        youtube_url: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        resources: Optional[Dict] = None,
        transcript: Optional[str] = None,
        order: Optional[int] = None,
        status: LessonStatus = LessonStatus.DRAFT,
    ) -> Lesson:
        """Create a new lesson."""
        # Verify module exists
        module = db.query(Module).filter(Module.id == module_id).first()
        if not module:
            raise NotFoundError(f"Module with ID {module_id} not found")
        
        # Extract YouTube video ID if URL provided
        youtube_video_id = None
        if youtube_url:
            youtube_video_id = LessonService._extract_youtube_video_id(youtube_url)
        
        # Auto-assign order if not provided
        if order is None:
            max_order = db.query(Lesson).filter(
                Lesson.module_id == module_id
            ).count()
            order = max_order + 1
        
        lesson = Lesson(
            module_id=UUID(module_id),
            title=title,
            description=description,
            youtube_url=youtube_url,
            youtube_video_id=youtube_video_id,
            duration_minutes=duration_minutes,
            resources=resources,
            transcript=transcript,
            order=order,
            status=status,
        )
        
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        
        # Update course lesson count
        course = module.course
        total_lessons = 0
        for m in course.modules:
            total_lessons += db.query(Lesson).filter(Lesson.module_id == m.id).count()
        course.required_lessons_count = total_lessons
        db.commit()
        
        logger.info(f"Created lesson: {title} for module {module_id}")
        return lesson
    
    @staticmethod
    def update_lesson(
        db: Session,
        lesson_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        youtube_url: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        resources: Optional[Dict] = None,
        transcript: Optional[str] = None,
        order: Optional[int] = None,
        status: Optional[LessonStatus] = None,
        expected_version: Optional[int] = None,
    ) -> Lesson:
        """Update a lesson."""
        lesson = LessonService.get_lesson(db, lesson_id)
        if expected_version is not None and lesson.version != expected_version:
            raise ConflictError("Lesson was changed by another request; reload before saving")
        
        if title:
            lesson.title = title
        if description is not None:
            lesson.description = description
        if youtube_url is not None:
            lesson.youtube_url = youtube_url
            lesson.youtube_video_id = LessonService._extract_youtube_video_id(youtube_url) if youtube_url else None
        if duration_minutes is not None:
            lesson.duration_minutes = duration_minutes
        if resources is not None:
            lesson.resources = resources
        if transcript is not None:
            lesson.transcript = transcript
        if order is not None:
            lesson.order = order
        if status is not None:
            lesson.status = status
        lesson.version += 1
        
        db.commit()
        db.refresh(lesson)
        
        logger.info(f"Updated lesson: {lesson_id}")
        return lesson
    
    @staticmethod
    def delete_lesson(db: Session, lesson_id: str) -> None:
        """Delete a lesson and reorder remaining lessons."""
        lesson = LessonService.get_lesson(db, lesson_id)
        module_id = lesson.module_id
        deleted_order = lesson.order
        
        db.delete(lesson)
        
        # Reorder remaining lessons
        remaining_lessons = db.query(Lesson).filter(
            Lesson.module_id == module_id,
            Lesson.order > deleted_order
        ).all()
        
        for l in remaining_lessons:
            l.order -= 1
        
        db.commit()
        
        logger.info(f"Deleted lesson: {lesson_id}")
    
    @staticmethod
    def publish_lesson(db: Session, lesson_id: str) -> Lesson:
        """Publish a lesson."""
        lesson = LessonService.get_lesson(db, lesson_id)
        lesson.status = LessonStatus.PUBLISHED
        db.commit()
        db.refresh(lesson)
        
        logger.info(f"Published lesson: {lesson_id}")
        return lesson
    
    @staticmethod
    def unpublish_lesson(db: Session, lesson_id: str) -> Lesson:
        """Unpublish a lesson (set to draft)."""
        lesson = LessonService.get_lesson(db, lesson_id)
        lesson.status = LessonStatus.DRAFT
        db.commit()
        db.refresh(lesson)
        
        logger.info(f"Unpublished lesson: {lesson_id}")
        return lesson
    
    @staticmethod
    def get_lesson_detail(db: Session, lesson_id: str) -> Dict[str, Any]:
        """Get detailed lesson information."""
        lesson = LessonService.get_lesson(db, lesson_id)
        module = lesson.module
        course = module.course
        
        # Get previous and next lessons
        prev_lesson = db.query(Lesson).filter(
            Lesson.module_id == lesson.module_id,
            Lesson.order < lesson.order
        ).order_by(Lesson.order.desc()).first()
        
        next_lesson = db.query(Lesson).filter(
            Lesson.module_id == lesson.module_id,
            Lesson.order > lesson.order
        ).order_by(Lesson.order).first()
        
        # If no next in module, get first lesson of next module
        if not next_lesson:
            next_module = db.query(Module).filter(
                Module.course_id == course.id,
                Module.order > module.order
            ).order_by(Module.order).first()
            
            if next_module:
                next_lesson = db.query(Lesson).filter(
                    Lesson.module_id == next_module.id
                ).order_by(Lesson.order).first()
        
        return {
            "id": str(lesson.id),
            "module_id": str(lesson.module_id),
            "module_title": module.title,
            "course_id": str(course.id),
            "course_title": course.title,
            "title": lesson.title,
            "description": lesson.description,
            "youtube_url": lesson.youtube_url,
            "youtube_video_id": lesson.youtube_video_id,
            "duration_minutes": lesson.duration_minutes,
            "thumbnail_url": lesson.thumbnail_url,
            "transcript": lesson.transcript,
            "resources": lesson.resources,
            "order": lesson.order,
            "status": lesson.status.value,
            "created_at": lesson.created_at.isoformat(),
            "updated_at": lesson.updated_at.isoformat(),
            "previous_lesson": {
                "id": str(prev_lesson.id),
                "title": prev_lesson.title,
            } if prev_lesson else None,
            "next_lesson": {
                "id": str(next_lesson.id),
                "title": next_lesson.title,
            } if next_lesson else None,
        }
