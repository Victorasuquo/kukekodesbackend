"""
Course management business logic.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime
import logging
import re

from app.models.course import Course, Module, Lesson, CourseStatus, LessonStatus, SkillLevel
from app.models.enrollment import Enrollment, UserProgress
from app.models.progress import Streak
from app.services.youtube_service import youtube_service
from app.db.mongodb import insert_activity
from app.dependencies import ConflictError, NotFoundError, UnauthorizedError, ValidationError

logger = logging.getLogger(__name__)


class CourseService:
    """Service for course management operations."""
    
    # ========================================================================
    # COURSE OPERATIONS
    # ========================================================================
    
    @staticmethod
    def create_course(
        db: Session,
        instructor_id: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        skill_level: str = "beginner",
        category: Optional[str] = None,
        is_free: bool = True,
    ) -> Course:
        """
        Create a new course (initially in draft status).
        
        Args:
            db: Database session
            instructor_id: ID of course instructor
            title: Course title
            description: Course description
            tags: List of tags/keywords
            skill_level: beginner/intermediate/advanced
            category: Course category
            is_free: Whether course is free
        
        Returns:
            Created course object
        """
        # Generate slug from title
        slug = CourseService._generate_slug(title)
        
        course = Course(
            title=title,
            description=description,
            slug=slug,
            tags=tags or [],
            skill_level=SkillLevel(skill_level),
            category=category,
            instructor_id=UUID(instructor_id),
            status=CourseStatus.DRAFT,
            is_free=is_free,
        )
        
        try:
            db.add(course)
            db.commit()
            db.refresh(course)
            
            logger.info(f"Course created: {course.id} by {instructor_id}")
            
            # Log activity
            try:
                insert_activity(
                    user_id=instructor_id,
                    action="created_course",
                    entity_id=str(course.id),
                    entity_type="course",
                )
            except Exception as e:
                logger.warning(f"Failed to log activity: {str(e)}")
            
            return course
        
        except IntegrityError:
            db.rollback()
            raise ValidationError("Course already exists")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating course: {str(e)}")
            raise
    
    @staticmethod
    def get_course(db: Session, course_id: str) -> Course:
        """Get course by ID."""
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise NotFoundError("Course", course_id)
        return course
    
    @staticmethod
    def get_course_by_slug(db: Session, slug: str) -> Optional[Course]:
        """Get course by slug."""
        return db.query(Course).filter(Course.slug == slug).first()
    
    @staticmethod
    def update_course(
        db: Session,
        course_id: str,
        instructor_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skill_level: Optional[str] = None,
        category: Optional[str] = None,
        is_free: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        cover_image_url: Optional[str] = None,
        expected_version: Optional[int] = None,
    ) -> Course:
        """Update course details."""
        course = CourseService.get_course(db, course_id)
        
        # Check authorization
        if str(course.instructor_id) != instructor_id:
            raise UnauthorizedError("You can only edit your own courses")
        
        # Only allow editing draft courses
        if course.status != CourseStatus.DRAFT:
            raise ValidationError("Cannot edit published or archived courses")
        if expected_version is not None and course.version != expected_version:
            raise ConflictError("Course was changed by another request; reload before saving")
        
        if title:
            course.title = title
            course.slug = CourseService._generate_slug(title)
        if description:
            course.description = description
        if tags is not None:
            course.tags = tags
        if skill_level:
            course.skill_level = SkillLevel(skill_level)
        if category:
            course.category = category
        if is_free is not None:
            course.is_free = is_free
        if is_featured is not None:
            course.is_featured = is_featured
        if cover_image_url:
            course.cover_image_url = cover_image_url
        course.version += 1
        
        db.commit()
        db.refresh(course)
        
        logger.info(f"Course updated: {course.id}")
        
        return course
    
    @staticmethod
    def delete_course(db: Session, course_id: str, instructor_id: str) -> None:
        """Delete course (draft only)."""
        course = CourseService.get_course(db, course_id)
        
        if str(course.instructor_id) != instructor_id:
            raise UnauthorizedError("You can only delete your own courses")
        
        if course.status != CourseStatus.DRAFT:
            raise ValidationError("Cannot delete published or archived courses")
        
        try:
            db.delete(course)
            db.commit()
            logger.info(f"Course deleted: {course.id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting course: {str(e)}")
            raise
    
    @staticmethod
    def publish_course(db: Session, course_id: str, instructor_id: str) -> Course:
        """
        Publish a course (move from draft to published).
        
        Validates:
        - At least 1 module
        - Each module has at least 1 lesson
        - All lessons have YouTube URLs
        """
        course = CourseService.get_course(db, course_id)
        
        if str(course.instructor_id) != instructor_id:
            raise UnauthorizedError("You can only publish your own courses")
        
        # Validate course structure
        if not course.modules:
            raise ValidationError("Course must have at least 1 module")
        
        for module in course.modules:
            if not module.lessons:
                raise ValidationError(f"Module '{module.title}' must have at least 1 lesson")
            
            for lesson in module.lessons:
                if not lesson.youtube_video_id:
                    raise ValidationError(
                        f"Lesson '{lesson.title}' in module '{module.title}' is missing YouTube video"
                    )
        
        # Publish course
        course.status = CourseStatus.PUBLISHED
        course.published_at = datetime.utcnow()
        
        # Publish all modules and lessons
        for module in course.modules:
            for lesson in module.lessons:
                lesson.status = LessonStatus.PUBLISHED
        
        db.commit()
        db.refresh(course)
        
        logger.info(f"Course published: {course.id}")
        
        return course
    
    @staticmethod
    def get_course_preview(db: Session, course_id: str) -> dict:
        """
        Get course preview (structure validation).
        
        Returns:
            Dict with course info and validation status
        """
        course = CourseService.get_course(db, course_id)
        
        modules = course.modules
        lessons = sum(len(m.lessons) for m in modules)
        duration = sum(
            (lesson.duration_minutes or 0)
            for module in modules
            for lesson in module.lessons
        )
        
        validation_errors = []
        
        if not modules:
            validation_errors.append("Course has no modules")
        
        for module in modules:
            if not module.lessons:
                validation_errors.append(f"Module '{module.title}' has no lessons")
            
            for lesson in module.lessons:
                if not lesson.youtube_video_id:
                    validation_errors.append(
                        f"Lesson '{lesson.title}' has no YouTube video"
                    )
        
        return {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "modules_count": len(modules),
            "lessons_count": lessons,
            "total_duration_minutes": duration,
            "status": course.status.value,
            "is_publishable": len(validation_errors) == 0,
            "validation_errors": validation_errors,
        }
    
    @staticmethod
    def list_courses(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        skill_level: Optional[str] = None,
    ) -> Tuple[List[Course], int]:
        """
        List courses with filtering.
        
        Returns:
            Tuple of (courses list, total count)
        """
        query = db.query(Course)
        
        # Filter by status (published by default for students)
        if status:
            query = query.filter(Course.status == CourseStatus(status))
        else:
            query = query.filter(Course.status == CourseStatus.PUBLISHED)
        
        if skill_level:
            query = query.filter(Course.skill_level == SkillLevel(skill_level))
        
        total = query.count()
        courses = query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
        
        return courses, total
    
    @staticmethod
    def list_instructor_courses(
        db: Session,
        instructor_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Course], int]:
        """List courses created by an instructor."""
        query = db.query(Course).filter(Course.instructor_id == instructor_id)
        total = query.count()
        courses = query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
        return courses, total
    
    # ========================================================================
    # MODULE OPERATIONS
    # ========================================================================
    
    @staticmethod
    def create_module(
        db: Session,
        course_id: str,
        instructor_id: str,
        title: str,
        description: Optional[str] = None,
        order: int = 1,
    ) -> Module:
        """Create a module in a course."""
        course = CourseService.get_course(db, course_id)
        
        if str(course.instructor_id) != instructor_id:
            raise UnauthorizedError("You can only add modules to your own courses")
        
        module = Module(
            course_id=UUID(course_id),
            title=title,
            description=description,
            order=order,
        )
        
        try:
            db.add(module)
            db.commit()
            db.refresh(module)
            
            logger.info(f"Module created: {module.id} in course {course_id}")
            
            return module
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating module: {str(e)}")
            raise
    
    @staticmethod
    def get_module(db: Session, module_id: str) -> Module:
        """Get module by ID."""
        module = db.query(Module).filter(Module.id == module_id).first()
        if not module:
            raise NotFoundError("Module", module_id)
        return module
    
    @staticmethod
    def update_module(
        db: Session,
        module_id: str,
        instructor_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        order: Optional[int] = None,
    ) -> Module:
        """Update module."""
        module = CourseService.get_module(db, module_id)
        course = module.course
        
        if str(course.instructor_id) != instructor_id:
            raise UnauthorizedError("You can only edit modules in your own courses")
        
        if title:
            module.title = title
        if description is not None:
            module.description = description
        if order:
            module.order = order
        
        db.commit()
        db.refresh(module)
        
        return module
    
    @staticmethod
    def delete_module(db: Session, module_id: str, instructor_id: str) -> None:
        """Delete module."""
        module = CourseService.get_module(db, module_id)
        course = module.course
        
        if str(course.instructor_id) != instructor_id:
            raise UnauthorizedError("You can only delete modules from your own courses")
        
        try:
            db.delete(module)
            db.commit()
            logger.info(f"Module deleted: {module_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting module: {str(e)}")
            raise
    
    # ========================================================================
    # LESSON OPERATIONS
    # ========================================================================
    
    @staticmethod
    async def create_lesson(
        db: Session,
        module_id: str,
        instructor_id: str,
        title: str,
        description: Optional[str] = None,
        youtube_url: str = "",
        order: int = 1,
    ) -> Lesson:
        """
        Create a lesson in a module.
        
        Automatically fetches YouTube video metadata if URL provided.
        """
        module = CourseService.get_module(db, module_id)
        course = module.course
        
        if str(course.instructor_id) != instructor_id:
            raise UnauthorizedError("You can only add lessons to your own courses")
        
        # Extract and validate YouTube video ID
        video_id = None
        duration_minutes = None
        thumbnail_url = None
        
        if youtube_url:
            video_id = youtube_service.extract_video_id(youtube_url)
            
            if not video_id:
                raise ValidationError("Invalid YouTube URL")
            
            # Fetch metadata
            try:
                metadata = await youtube_service.get_video_metadata(video_id)
                if metadata:
                    duration_minutes = metadata.get("duration_minutes")
                    thumbnail_url = metadata.get("thumbnail_url")
            except Exception as e:
                logger.warning(f"Failed to fetch YouTube metadata: {str(e)}")
        
        lesson = Lesson(
            module_id=UUID(module_id),
            title=title,
            description=description,
            youtube_url=youtube_url,
            youtube_video_id=video_id,
            duration_minutes=duration_minutes,
            thumbnail_url=thumbnail_url,
            order=order,
            status=LessonStatus.DRAFT,
        )
        
        try:
            db.add(lesson)
            db.commit()
            db.refresh(lesson)
            
            logger.info(f"Lesson created: {lesson.id} in module {module_id}")
            
            return lesson
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating lesson: {str(e)}")
            raise
    
    @staticmethod
    async def update_lesson(
        db: Session,
        lesson_id: str,
        instructor_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        youtube_url: Optional[str] = None,
        order: Optional[int] = None,
    ) -> Lesson:
        """Update lesson."""
        lesson = CourseService.get_lesson(db, lesson_id)
        course = lesson.module.course
        
        if str(course.instructor_id) != instructor_id:
            raise UnauthorizedError("You can only edit lessons in your own courses")
        
        if title:
            lesson.title = title
        if description is not None:
            lesson.description = description
        if order:
            lesson.order = order
        
        # Update YouTube URL if provided
        if youtube_url:
            video_id = youtube_service.extract_video_id(youtube_url)
            if not video_id:
                raise ValidationError("Invalid YouTube URL")
            
            lesson.youtube_url = youtube_url
            lesson.youtube_video_id = video_id
            
            # Fetch updated metadata
            try:
                metadata = await youtube_service.get_video_metadata(video_id)
                if metadata:
                    lesson.duration_minutes = metadata.get("duration_minutes")
                    lesson.thumbnail_url = metadata.get("thumbnail_url")
            except Exception as e:
                logger.warning(f"Failed to fetch YouTube metadata: {str(e)}")
        
        db.commit()
        db.refresh(lesson)
        
        return lesson
    
    @staticmethod
    def get_lesson(db: Session, lesson_id: str) -> Lesson:
        """Get lesson by ID."""
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise NotFoundError("Lesson", lesson_id)
        return lesson
    
    @staticmethod
    def delete_lesson(db: Session, lesson_id: str, instructor_id: str) -> None:
        """Delete lesson."""
        lesson = CourseService.get_lesson(db, lesson_id)
        course = lesson.module.course
        
        if str(course.instructor_id) != instructor_id:
            raise UnauthorizedError("You can only delete lessons from your own courses")
        
        try:
            db.delete(lesson)
            db.commit()
            logger.info(f"Lesson deleted: {lesson_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting lesson: {str(e)}")
            raise
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    @staticmethod
    def _generate_slug(title: str) -> str:
        """Generate URL-friendly slug from title."""
        slug = title.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug[:255]
