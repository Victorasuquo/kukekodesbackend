"""
Module management business logic.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from app.models.course import Course, Module, Lesson
from app.utils.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class ModuleService:
    """Service for module operations."""
    
    @staticmethod
    def get_module(db: Session, module_id: str) -> Module:
        """Get a single module by ID."""
        module = db.query(Module).filter(Module.id == module_id).first()
        if not module:
            raise NotFoundError(f"Module with ID {module_id} not found")
        return module
    
    @staticmethod
    def get_modules_by_course(db: Session, course_id: str) -> List[Module]:
        """Get all modules for a course."""
        modules = db.query(Module).filter(
            Module.course_id == course_id
        ).order_by(Module.order).all()
        return modules
    
    @staticmethod
    def create_module(
        db: Session,
        course_id: str,
        title: str,
        description: Optional[str] = None,
        order: Optional[int] = None,
    ) -> Module:
        """Create a new module."""
        # Verify course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise NotFoundError(f"Course with ID {course_id} not found")
        
        # Auto-assign order if not provided
        if order is None:
            max_order = db.query(Module).filter(
                Module.course_id == course_id
            ).count()
            order = max_order + 1
        
        module = Module(
            course_id=UUID(course_id),
            title=title,
            description=description,
            order=order,
        )
        
        db.add(module)
        db.commit()
        db.refresh(module)
        
        # Update course module count
        course.required_modules_count = db.query(Module).filter(
            Module.course_id == course_id
        ).count()
        db.commit()
        
        logger.info(f"Created module: {title} for course {course_id}")
        return module
    
    @staticmethod
    def update_module(
        db: Session,
        module_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        order: Optional[int] = None,
    ) -> Module:
        """Update a module."""
        module = ModuleService.get_module(db, module_id)
        
        if title:
            module.title = title
        if description is not None:
            module.description = description
        if order is not None:
            module.order = order
        
        db.commit()
        db.refresh(module)
        
        logger.info(f"Updated module: {module_id}")
        return module
    
    @staticmethod
    def delete_module(db: Session, module_id: str) -> None:
        """Delete a module and reorder remaining modules."""
        module = ModuleService.get_module(db, module_id)
        course_id = module.course_id
        deleted_order = module.order
        
        db.delete(module)
        
        # Reorder remaining modules
        remaining_modules = db.query(Module).filter(
            Module.course_id == course_id,
            Module.order > deleted_order
        ).all()
        
        for m in remaining_modules:
            m.order -= 1
        
        db.commit()
        
        # Update course module count
        course = db.query(Course).filter(Course.id == course_id).first()
        course.required_modules_count = db.query(Module).filter(
            Module.course_id == course_id
        ).count()
        db.commit()
        
        logger.info(f"Deleted module: {module_id}")
    
    @staticmethod
    def reorder_modules(db: Session, course_id: str, module_orders: List[Dict[str, Any]]) -> List[Module]:
        """
        Reorder modules in a course.
        
        Args:
            module_orders: List of {"module_id": str, "order": int}
        """
        for item in module_orders:
            module = db.query(Module).filter(
                Module.id == item["module_id"],
                Module.course_id == course_id
            ).first()
            
            if module:
                module.order = item["order"]
        
        db.commit()
        
        return ModuleService.get_modules_by_course(db, course_id)
    
    @staticmethod
    def get_module_with_lessons(db: Session, module_id: str) -> Dict[str, Any]:
        """Get module with all its lessons."""
        module = ModuleService.get_module(db, module_id)
        
        lessons = db.query(Lesson).filter(
            Lesson.module_id == module_id
        ).order_by(Lesson.order).all()
        
        return {
            "id": str(module.id),
            "course_id": str(module.course_id),
            "title": module.title,
            "description": module.description,
            "order": module.order,
            "created_at": module.created_at.isoformat(),
            "lessons": [
                {
                    "id": str(lesson.id),
                    "title": lesson.title,
                    "description": lesson.description,
                    "order": lesson.order,
                    "duration_minutes": lesson.duration_minutes,
                    "youtube_video_id": lesson.youtube_video_id,
                    "status": lesson.status.value,
                }
                for lesson in lessons
            ],
            "total_lessons": len(lessons),
        }
