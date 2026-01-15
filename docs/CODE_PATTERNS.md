# Kukekodes - Code Implementation Patterns & Examples

**Date:** January 15, 2026  
**Purpose:** Provide code templates and patterns for consistent implementation  
**Status:** Reference Guide

---

## TABLE OF CONTENTS

1. [API Endpoint Pattern](#api-endpoint-pattern)
2. [Service Layer Pattern](#service-layer-pattern)
3. [Model Pattern](#model-pattern)
4. [Schema Pattern](#schema-pattern)
5. [Error Handling Pattern](#error-handling-pattern)
6. [Authentication Pattern](#authentication-pattern)
7. [Testing Pattern](#testing-pattern)
8. [Critical Implementation Examples](#critical-implementation-examples)

---

## API ENDPOINT PATTERN

### Standard Route File Structure

**File:** `app/api/v1/{feature}/routes.py`

```python
"""
{Feature Name} API endpoints.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging

from app.api.v1.{feature}.service import {Feature}Service
from app.api.v1.{feature}.schemas import (
    {Feature}CreateRequest,
    {Feature}UpdateRequest,
    {Feature}Response,
    PaginationParams,
)
from app.dependencies import get_db, get_current_user, get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["{Feature}"])


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================

@router.post(
    "/{feature}s",
    response_model={Feature}Response,
    status_code=status.HTTP_201_CREATED,
    summary="Create {feature}",
    description="Create a new {feature} (admin only)",
)
async def create_{feature}(
    request: {Feature}CreateRequest,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> {Feature}Response:
    """
    Create a new {feature}.
    
    - **Requires:** Admin role
    - **Returns:** Created {feature} object
    """
    try:
        {feature} = {Feature}Service.create(
            db=db,
            data=request,
            user_id=current_user.get("sub")
        )
        
        logger.info(f"Created {feature}: {{{feature}.id}}")
        
        return {Feature}Response.from_orm({feature})
    
    except Exception as e:
        logger.error(f"Error creating {feature}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{feature}s/{id}",
    response_model={Feature}Response,
    status_code=status.HTTP_200_OK,
    summary="Get {feature}",
)
async def get_{feature}(
    id: str,
    db: Session = Depends(get_db),
) -> {Feature}Response:
    """Get {feature} details."""
    try:
        {feature} = {Feature}Service.get_by_id(db, id)
        
        if not {feature}:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="{Feature} not found"
            )
        
        return {Feature}Response.from_orm({feature})
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching {feature}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{feature}s",
    response_model=List[{Feature}Response],
    status_code=status.HTTP_200_OK,
    summary="List {feature}s",
)
async def list_{feature}s(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> List[{Feature}Response]:
    """List all {feature}s with pagination."""
    try:
        {feature}s = {Feature}Service.list(
            db=db,
            skip=skip,
            limit=min(limit, 100)  # Max 100 per page
        )
        
        return [{Feature}Response.from_orm(item) for item in {feature}s]
    
    except Exception as e:
        logger.error(f"Error listing {feature}s: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put(
    "/{feature}s/{id}",
    response_model={Feature}Response,
    status_code=status.HTTP_200_OK,
    summary="Update {feature}",
)
async def update_{feature}(
    id: str,
    request: {Feature}UpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> {Feature}Response:
    """Update {feature} (owner only)."""
    try:
        {feature} = {Feature}Service.get_by_id(db, id)
        
        if not {feature}:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="{Feature} not found"
            )
        
        # Check ownership
        if {feature}.user_id != current_user.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this {feature}"
            )
        
        updated_{feature} = {Feature}Service.update(
            db=db,
            id=id,
            data=request
        )
        
        logger.info(f"Updated {feature}: {id}")
        
        return {Feature}Response.from_orm(updated_{feature})
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating {feature}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{feature}s/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete {feature}",
)
async def delete_{feature}(
    id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Delete {feature} (admin only)."""
    try:
        {feature} = {Feature}Service.get_by_id(db, id)
        
        if not {feature}:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="{Feature} not found"
            )
        
        {Feature}Service.delete(db, id)
        
        logger.info(f"Deleted {feature}: {id}")
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting {feature}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

---

## SERVICE LAYER PATTERN

**File:** `app/api/v1/{feature}/service.py`

```python
"""
{Feature Name} business logic.
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from app.models.{model} import {Model}
from app.utils.exceptions import ResourceNotFoundError, ValidationError
from app.db.mongodb import get_mongodb

logger = logging.getLogger(__name__)


class {Feature}Service:
    """Service class for {Feature} operations."""
    
    @staticmethod
    def create(
        db: Session,
        data: {Feature}CreateRequest,
        user_id: str,
    ) -> {Model}:
        """
        Create a new {feature}.
        
        Args:
            db: Database session
            data: Request data
            user_id: User ID (creator)
        
        Returns:
            Created {feature} object
        
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate
            {Feature}Service._validate_create(db, data)
            
            # Create
            {feature} = {Model}(
                title=data.title,
                description=data.description,
                user_id=user_id,
                # ... other fields
            )
            
            # Save
            db.add({feature})
            db.commit()
            db.refresh({feature})
            
            # Log to MongoDB
            mongo = get_mongodb()
            mongo.activity_logs.insert_one({
                "user_id": user_id,
                "action": "{feature}_created",
                "resource_type": "{feature}",
                "resource_id": str({feature}.id),
                "timestamp": datetime.utcnow()
            })
            
            logger.info(f"Created {feature}: {{{feature}.id}}")
            return {feature}
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating {feature}: {str(e)}")
            raise
    
    @staticmethod
    def get_by_id(db: Session, id: str) -> Optional[{Model}]:
        """
        Get {feature} by ID.
        
        Args:
            db: Database session
            id: {Feature} ID
        
        Returns:
            {Feature} object or None
        """
        try:
            {feature} = db.query({Model}).filter(
                {Model}.id == id
            ).first()
            
            return {feature}
        
        except Exception as e:
            logger.error(f"Error fetching {feature}: {str(e)}")
            return None
    
    @staticmethod
    def list(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        filters: Dict[str, Any] = None,
    ) -> List[{Model}]:
        """
        List {feature}s with pagination and optional filters.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Number of records to return
            filters: Optional filter dict
        
        Returns:
            List of {feature} objects
        """
        try:
            query = db.query({Model})
            
            # Apply filters
            if filters:
                if "status" in filters:
                    query = query.filter({Model}.status == filters["status"])
                if "user_id" in filters:
                    query = query.filter({Model}.user_id == filters["user_id"])
            
            # Paginate
            {feature}s = query.order_by(
                desc({Model}.created_at)
            ).offset(skip).limit(limit).all()
            
            return {feature}s
        
        except Exception as e:
            logger.error(f"Error listing {feature}s: {str(e)}")
            return []
    
    @staticmethod
    def update(
        db: Session,
        id: str,
        data: {Feature}UpdateRequest,
    ) -> {Model}:
        """
        Update {feature}.
        
        Args:
            db: Database session
            id: {Feature} ID
            data: Update data
        
        Returns:
            Updated {feature} object
        
        Raises:
            ResourceNotFoundError: If {feature} not found
        """
        try:
            {feature} = db.query({Model}).filter({Model}.id == id).first()
            
            if not {feature}:
                raise ResourceNotFoundError("{Feature} not found")
            
            # Update fields
            if data.title:
                {feature}.title = data.title
            if data.description:
                {feature}.description = data.description
            
            # Update timestamp
            {feature}.updated_at = datetime.utcnow()
            
            # Save
            db.commit()
            db.refresh({feature})
            
            logger.info(f"Updated {feature}: {id}")
            return {feature}
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating {feature}: {str(e)}")
            raise
    
    @staticmethod
    def delete(db: Session, id: str) -> bool:
        """
        Delete {feature}.
        
        Args:
            db: Database session
            id: {Feature} ID
        
        Returns:
            True if successful
        
        Raises:
            ResourceNotFoundError: If {feature} not found
        """
        try:
            {feature} = db.query({Model}).filter({Model}.id == id).first()
            
            if not {feature}:
                raise ResourceNotFoundError("{Feature} not found")
            
            # Delete
            db.delete({feature})
            db.commit()
            
            logger.info(f"Deleted {feature}: {id}")
            return True
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting {feature}: {str(e)}")
            raise
    
    @staticmethod
    def _validate_create(db: Session, data: {Feature}CreateRequest) -> None:
        """Validate {feature} creation data."""
        if not data.title or len(data.title.strip()) == 0:
            raise ValidationError("Title is required")
        
        if not data.description or len(data.description.strip()) == 0:
            raise ValidationError("Description is required")
        
        # Add more validations as needed
```

---

## MODEL PATTERN

**File:** `app/models/{model}.py`

```python
"""
SQLAlchemy ORM models for {Feature}.
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from app.db.postgres import Base


class {Feature}Status(str, PyEnum):
    """Status enum for {Feature}."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class {Model}(Base):
    """{Feature} model."""
    
    __tablename__ = "{feature_table}"
    
    # === PRIMARY KEY ===
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # === FOREIGN KEYS ===
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # === BASIC INFO ===
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    slug = Column(String(255), unique=True, nullable=True, index=True)
    
    # === STATUS ===
    status = Column(
        Enum({Feature}Status),
        default={Feature}Status.ACTIVE,
        nullable=False,
        index=True,
    )
    
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # === RELATIONSHIPS ===
    user = relationship("User", foreign_keys=[user_id])
    
    # === INDEXES ===
    __table_args__ = (
        Index("idx_{feature}_user_status", "user_id", "status"),
        Index("idx_{feature}_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<{Model} {self.title} ({self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
```

---

## SCHEMA PATTERN

**File:** `app/api/v1/{feature}/schemas.py`

```python
"""
Pydantic schemas for {Feature} API requests and responses.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class {Feature}CreateRequest(BaseModel):
    """Request schema for creating {feature}."""
    
    title: str = Field(..., min_length=1, max_length=255, description="Title")
    description: Optional[str] = Field(None, description="Description")
    
    @validator('title')
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Example Title",
                "description": "Example description",
            }
        }


class {Feature}UpdateRequest(BaseModel):
    """Request schema for updating {feature}."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    status: Optional[str] = Field(None, regex="^(active|inactive|archived)$")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Updated Title",
                "description": "Updated description",
            }
        }


class {Feature}Response(BaseModel):
    """Response schema for {feature}."""
    
    id: UUID
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Support ORM models
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Example Title",
                "description": "Example description",
                "status": "active",
                "created_at": "2026-01-15T10:30:00Z",
                "updated_at": "2026-01-15T10:30:00Z",
            }
        }


class {Feature}DetailResponse({Feature}Response):
    """Detailed response with relationships."""
    
    user: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    
    total: int
    page: int
    limit: int
    total_pages: int


class {Feature}ListResponse(BaseModel):
    """List response with pagination."""
    
    data: List[{Feature}Response]
    meta: PaginationMeta
```

---

## ERROR HANDLING PATTERN

**File:** `app/utils/exceptions.py`

```python
"""
Custom exceptions for Kukekodes.
"""

class KukekodesException(Exception):
    """Base exception for Kukekodes."""
    
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ResourceNotFoundError(KukekodesException):
    """Resource not found."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(KukekodesException):
    """Validation failed."""
    
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=422)


class UnauthorizedError(KukekodesException):
    """User not authorized."""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ForbiddenError(KukekodesException):
    """User forbidden."""
    
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class ExternalServiceError(KukekodesException):
    """External service error."""
    
    def __init__(self, message: str = "External service error"):
        super().__init__(message, status_code=503)


# Global exception handler
from fastapi import FastAPI
from fastapi.responses import JSONResponse

def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers."""
    
    @app.exception_handler(KukekodesException)
    async def kukekodes_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "detail": exc.message,
                "request_id": request.headers.get("X-Request-ID"),
            }
        )
```

---

## AUTHENTICATION PATTERN

**File:** Example usage in routes

```python
"""
Authentication dependency pattern.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from typing import Dict, Any, Optional
import logging

from app.security import decode_token

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Get current user from JWT token.
    
    Returns:
        Decoded token payload with user info
    
    Raises:
        HTTPException: If token invalid or expired
    """
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        return payload
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get current user and verify admin role.
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If not admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return current_user


async def get_instructor_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Verify instructor role."""
    if current_user.get("role") not in ["instructor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor access required",
        )
    
    return current_user


# Usage in route
@router.get("/profile")
async def get_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get user profile (requires auth)."""
    return {
        "id": current_user.get("sub"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
    }
```

---

## TESTING PATTERN

**File:** `app/tests/test_{feature}.py`

```python
"""
Tests for {Feature} API.
"""

import pytest
from sqlalchemy.orm import Session
from httpx import AsyncClient
from uuid import uuid4

from app.main import app
from app.models.{model} import {Model}
from app.api.v1.{feature}.service import {Feature}Service


@pytest.fixture
def test_client():
    """Create test client."""
    return AsyncClient(app=app, base_url="http://test")


@pytest.fixture
def test_db():
    """Create test database session."""
    # Setup test database
    yield db
    # Cleanup


@pytest.fixture
def test_user(test_db):
    """Create test user."""
    from app.models.user import User
    from app.security import hash_password
    
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        first_name="Test",
        last_name="User",
        role="admin",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_{feature}(test_client, test_user):
    """Test creating {feature}."""
    
    # Create JWT token for test user
    from app.security import create_access_token
    token = create_access_token(
        user_id=str(test_user.id),
        email=test_user.email,
        role=test_user.role,
    )
    
    # Make request
    response = await test_client.post(
        "/api/v1/{feature}s",
        json={
            "title": "Test {Feature}",
            "description": "Test description",
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test {Feature}"
    assert data["description"] == "Test description"


@pytest.mark.asyncio
async def test_get_{feature}(test_client, test_db):
    """Test getting {feature}."""
    
    # Create test {feature}
    {feature} = {Model}(
        title="Test {Feature}",
        description="Test description",
        user_id=uuid4(),
    )
    test_db.add({feature})
    test_db.commit()
    test_db.refresh({feature})
    
    # Make request
    response = await test_client.get(
        f"/api/v1/{feature}s/{{{feature}.id}}"
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test {Feature}"


@pytest.mark.asyncio
async def test_{feature}_not_found(test_client):
    """Test {feature} not found."""
    
    response = await test_client.get(
        f"/api/v1/{feature}s/{uuid4()}"
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_{feature}s(test_client, test_db):
    """Test listing {feature}s."""
    
    # Create multiple test {feature}s
    for i in range(5):
        {feature} = {Model}(
            title=f"Test {Feature} {i}",
            description="Test description",
            user_id=uuid4(),
        )
        test_db.add({feature})
    test_db.commit()
    
    # Make request
    response = await test_client.get(
        "/api/v1/{feature}s?skip=0&limit=10"
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5


def test_{feature}_service_create(test_db):
    """Test {feature} service create."""
    
    from app.api.v1.{feature}.schemas import {Feature}CreateRequest
    
    request = {Feature}CreateRequest(
        title="Test {Feature}",
        description="Test description",
    )
    
    {feature} = {Feature}Service.create(
        db=test_db,
        data=request,
        user_id=str(uuid4()),
    )
    
    assert {feature}.title == "Test {Feature}"
    assert {feature}.id is not None


def test_{feature}_validation(test_db):
    """Test {feature} validation."""
    
    from app.api.v1.{feature}.schemas import {Feature}CreateRequest
    from app.utils.exceptions import ValidationError
    
    # Empty title should fail
    with pytest.raises(ValueError):
        {Feature}CreateRequest(title="", description="Test")
```

---

## CRITICAL IMPLEMENTATION EXAMPLES

### 1. MARK LESSON COMPLETE (Progress Tracking)

**File:** `app/api/v1/progress/routes.py`

```python
from datetime import datetime, timedelta
from app.db.mongodb import get_mongodb
from app.services.email_service import EmailService

@router.post("/progress/mark-lesson-complete/{lesson_id}")
async def mark_lesson_complete(
    lesson_id: str,
    request: MarkLessonCompleteRequest,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a lesson as complete and update all related progress.
    
    This is a CRITICAL endpoint that:
    1. Validates lesson and enrollment
    2. Updates user_progress
    3. Calculates module/course progress
    4. Increments streak
    5. Checks badge conditions
    6. Sends email notification
    7. Logs to MongoDB
    """
    
    try:
        user_id = current_user.get("sub")
        
        # ===== STEP 1: VALIDATE LESSON EXISTS =====
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        module = db.query(Module).filter(Module.id == lesson.module_id).first()
        course = db.query(Course).filter(Course.id == module.course_id).first()
        
        # ===== STEP 2: VALIDATE ENROLLMENT =====
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course.id
        ).first()
        
        if not enrollment:
            raise HTTPException(
                status_code=403,
                detail="Not enrolled in this course"
            )
        
        # ===== STEP 3: UPDATE USER PROGRESS =====
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.lesson_id == lesson_id
        ).first()
        
        if not progress:
            # Create if doesn't exist
            progress = UserProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                module_id=module.id,
                course_id=course.id,
            )
            db.add(progress)
        
        # Mark complete
        was_already_complete = progress.is_completed
        progress.is_completed = True
        progress.completed_at = datetime.utcnow()
        progress.time_spent_minutes = request.time_spent_minutes
        progress.quiz_score = request.quiz_score
        
        db.commit()
        db.refresh(progress)
        
        # ===== STEP 4: CALCULATE MODULE PROGRESS =====
        module_lessons = db.query(UserProgress).filter(
            UserProgress.module_id == module.id,
            UserProgress.user_id == user_id
        ).all()
        
        completed_in_module = sum(1 for p in module_lessons if p.is_completed)
        total_in_module = len(module_lessons)
        module_percentage = (completed_in_module / total_in_module * 100) if total_in_module > 0 else 0
        
        # ===== STEP 5: CALCULATE COURSE PROGRESS =====
        course_lessons = db.query(UserProgress).filter(
            UserProgress.course_id == course.id,
            UserProgress.user_id == user_id
        ).all()
        
        completed_in_course = sum(1 for p in course_lessons if p.is_completed)
        total_in_course = len(course_lessons)
        course_percentage = (completed_in_course / total_in_course * 100) if total_in_course > 0 else 0
        
        # Update enrollment progress
        enrollment.completion_percentage = course_percentage
        enrollment.is_completed = course_percentage >= 100
        if enrollment.is_completed and not enrollment.completed_at:
            enrollment.completed_at = datetime.utcnow()
        enrollment.current_lesson_id = lesson_id
        enrollment.last_accessed_at = datetime.utcnow()
        
        db.commit()
        
        # ===== STEP 6: UPDATE STREAK =====
        streak = db.query(Streak).filter(Streak.user_id == user_id).first()
        
        if not streak:
            streak = Streak(user_id=user_id, current_streak=1, longest_streak=1)
            db.add(streak)
        
        # Check if should increment streak
        today = datetime.utcnow().date()
        last_activity = streak.last_activity_date
        
        streak_incremented = False
        if not was_already_complete:  # Only increment if first completion today
            if last_activity is None or last_activity < today:
                # New day
                if last_activity and (today - last_activity).days == 1:
                    # Consecutive day
                    streak.current_streak += 1
                else:
                    # Reset if gap
                    streak.current_streak = 1
                
                streak.current_streak = min(streak.current_streak, 365)  # Cap at 1 year
                streak.longest_streak = max(streak.longest_streak, streak.current_streak)
                streak.last_activity_date = today
                streak_incremented = True
        
        db.commit()
        db.refresh(streak)
        
        # ===== STEP 7: CHECK BADGE CONDITIONS =====
        badges_earned = []
        
        # Badge: First Lesson Complete
        if completed_in_course == 1:
            badge = db.query(Badge).filter(Badge.name == "First Lesson Complete").first()
            if badge and not db.query(UserBadge).filter(
                UserBadge.user_id == user_id,
                UserBadge.badge_id == badge.id
            ).first():
                user_badge = UserBadge(user_id=user_id, badge_id=badge.id)
                db.add(user_badge)
                badges_earned.append(badge)
        
        # Badge: 7-Day Streak
        if streak.current_streak == 7:
            badge = db.query(Badge).filter(Badge.name == "7-Day Streak").first()
            if badge and not db.query(UserBadge).filter(
                UserBadge.user_id == user_id,
                UserBadge.badge_id == badge.id
            ).first():
                user_badge = UserBadge(user_id=user_id, badge_id=badge.id)
                db.add(user_badge)
                badges_earned.append(badge)
        
        # Badge: Perfect Score
        if request.quiz_score == 100:
            badge = db.query(Badge).filter(Badge.name == "Perfect Score").first()
            if badge and not db.query(UserBadge).filter(
                UserBadge.user_id == user_id,
                UserBadge.badge_id == badge.id
            ).first():
                user_badge = UserBadge(user_id=user_id, badge_id=badge.id)
                db.add(user_badge)
                badges_earned.append(badge)
        
        db.commit()
        
        # ===== STEP 8: FIND NEXT LESSON =====
        next_lesson = None
        current_lesson_order = lesson.order
        
        # Try to get next lesson in same module
        next_in_module = db.query(Lesson).filter(
            Lesson.module_id == module.id,
            Lesson.order > current_lesson_order
        ).order_by(Lesson.order).first()
        
        if next_in_module:
            next_lesson = next_in_module
        else:
            # Get next module's first lesson
            next_module = db.query(Module).filter(
                Module.course_id == course.id,
                Module.order > module.order
            ).order_by(Module.order).first()
            
            if next_module:
                next_lesson = db.query(Lesson).filter(
                    Lesson.module_id == next_module.id
                ).order_by(Lesson.order).first()
        
        # ===== STEP 9: SEND EMAIL NOTIFICATION =====
        user = db.query(User).filter(User.id == user_id).first()
        
        try:
            await EmailService.send_lesson_completion(
                user_email=user.email,
                user_name=user.get_full_name(),
                course_title=course.title,
                lesson_title=lesson.title,
                progress_percentage=course_percentage,
                next_lesson_title=next_lesson.title if next_lesson else None,
                course_url=f"http://app.kukekodes.com/courses/{course.id}"
            )
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            # Don't fail the request if email fails
        
        # ===== STEP 10: LOG TO MONGODB =====
        mongo = get_mongodb()
        
        mongo.activity_logs.insert_one({
            "user_id": user_id,
            "action": "lesson_completed",
            "resource_type": "lesson",
            "resource_id": lesson_id,
            "metadata": {
                "course_id": str(course.id),
                "module_id": str(module.id),
                "time_spent": request.time_spent_minutes,
                "quiz_score": request.quiz_score,
            },
            "timestamp": datetime.utcnow()
        })
        
        mongo.analytics.insert_one({
            "user_id": user_id,
            "metric_type": "course_progress",
            "data": {
                "course_id": str(course.id),
                "progress_percentage": course_percentage,
                "lessons_completed": completed_in_course,
                "total_lessons": total_in_course,
            },
            "timestamp": datetime.utcnow()
        })
        
        # ===== RETURN RESPONSE =====
        return {
            "success": True,
            "lesson_status": "completed",
            "lesson_marked_green": True,
            "module_progress": {
                "completed": completed_in_module,
                "total": total_in_module,
                "percentage": round(module_percentage, 1)
            },
            "course_progress": {
                "percentage": round(course_percentage, 1),
                "completed_lessons": completed_in_course,
                "total_lessons": total_in_course
            },
            "next_lesson": {
                "id": str(next_lesson.id),
                "title": next_lesson.title,
                "module_id": str(next_lesson.module_id)
            } if next_lesson else None,
            "streak": {
                "current": streak.current_streak,
                "longest": streak.longest_streak,
                "incremented": streak_incremented
            },
            "badges_earned": [
                {
                    "id": str(badge.id),
                    "name": badge.name,
                    "icon_url": badge.icon_url
                }
                for badge in badges_earned
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking lesson complete: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error processing lesson completion"
        )
```

---

### 2. PUBLISH COURSE

**File:** `app/api/v1/courses/routes.py`

```python
@router.post("/courses/{course_id}/publish")
async def publish_course(
    course_id: str,
    current_user: Dict = Depends(get_instructor_user),
    db: Session = Depends(get_db),
):
    """Publish course if all requirements are met."""
    
    try:
        # Get course
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Check ownership
        if course.instructor_id != current_user.get("sub"):
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Validate requirements
        if not course.title or not course.description:
            raise HTTPException(status_code=400, detail="Title and description required")
        
        # Check modules
        modules = db.query(Module).filter(Module.course_id == course.id).all()
        if not modules:
            raise HTTPException(status_code=400, detail="Course must have at least 1 module")
        
        # Check lessons per module
        for module in modules:
            lessons = db.query(Lesson).filter(Lesson.module_id == module.id).all()
            if not lessons:
                raise HTTPException(
                    status_code=400,
                    detail=f"Module '{module.title}' has no lessons"
                )
        
        # Publish course
        course.status = CourseStatus.PUBLISHED
        course.published_at = datetime.utcnow()
        
        # Publish all lessons
        for module in modules:
            lessons = db.query(Lesson).filter(Lesson.module_id == module.id).all()
            for lesson in lessons:
                lesson.status = LessonStatus.PUBLISHED
        
        db.commit()
        
        # Notify enrolled students
        enrollments = db.query(Enrollment).filter(
            Enrollment.course_id == course.id
        ).all()
        
        mongo = get_mongodb()
        
        for enrollment in enrollments:
            student = db.query(User).filter(User.id == enrollment.user_id).first()
            
            # Send email
            try:
                await EmailService.send_course_published(
                    user_email=student.email,
                    user_name=student.get_full_name(),
                    course_title=course.title
                )
            except:
                pass
            
            # Log event
            mongo.activity_logs.insert_one({
                "user_id": str(enrollment.user_id),
                "action": "course_published",
                "resource_type": "course",
                "resource_id": str(course.id),
                "timestamp": datetime.utcnow()
            })
        
        return CourseResponse.from_orm(course)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing course: {str(e)}")
        raise HTTPException(status_code=500, detail="Error publishing course")
```

---

### 3. YOUTUBE API INTEGRATION

**File:** `app/services/youtube_service.py` (COMPLETE IMPLEMENTATION)

```python
"""
YouTube API integration for extracting video metadata.
"""

import re
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for YouTube API operations."""
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    @staticmethod
    def extract_video_id(youtube_url: str) -> str:
        """
        Extract video ID from YouTube URL.
        
        Supports:
        - https://www.youtube.com/watch?v=dQw4w9WgXcQ
        - https://youtu.be/dQw4w9WgXcQ
        - https://www.youtube.com/embed/dQw4w9WgXcQ
        
        Args:
            youtube_url: YouTube URL
        
        Returns:
            Video ID
        
        Raises:
            ValueError: If URL is invalid
        """
        try:
            # Pattern for standard YouTube URLs
            match = re.search(
                r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([0-9A-Za-z_-]{11})",
                youtube_url
            )
            
            if match:
                return match.group(1)
            
            # Try URL parsing
            parsed = urlparse(youtube_url)
            if parsed.hostname in ['www.youtube.com', 'youtube.com', 'youtu.be']:
                if 'v' in parse_qs(parsed.query):
                    return parse_qs(parsed.query)['v'][0]
            
            raise ValueError("Invalid YouTube URL")
        
        except Exception as e:
            logger.error(f"Error extracting video ID: {str(e)}")
            raise ValueError(f"Invalid YouTube URL: {str(e)}")
    
    @staticmethod
    async def get_video_metadata(video_id: str) -> Dict[str, Any]:
        """
        Fetch video metadata from YouTube API.
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            Dict with duration_minutes, thumbnail_url, title
        
        Raises:
            ExternalServiceError: If API call fails
        """
        if not settings.YOUTUBE_API_KEY:
            logger.warning("YouTube API key not configured")
            return {
                "duration_minutes": None,
                "thumbnail_url": None,
                "title": None
            }
        
        try:
            async with httpx.AsyncClient(timeout=settings.EXTERNAL_API_TIMEOUT) as client:
                response = await client.get(
                    f"{YouTubeService.BASE_URL}/videos",
                    params={
                        "id": video_id,
                        "key": settings.YOUTUBE_API_KEY,
                        "part": "contentDetails,snippet"
                    }
                )
            
            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code}")
            
            data = response.json()
            
            if not data.get("items"):
                raise Exception("Video not found")
            
            item = data["items"][0]
            
            # Extract duration
            duration_iso = item["contentDetails"]["duration"]
            duration_seconds = YouTubeService._parse_iso_duration(duration_iso)
            duration_minutes = duration_seconds // 60
            
            # Extract thumbnail
            thumbnail_url = (
                item["snippet"]["thumbnails"].get("maxres", {}).get("url") or
                item["snippet"]["thumbnails"].get("high", {}).get("url") or
                item["snippet"]["thumbnails"].get("default", {}).get("url")
            )
            
            # Extract title
            title = item["snippet"]["title"]
            
            return {
                "duration_minutes": duration_minutes,
                "thumbnail_url": thumbnail_url,
                "title": title
            }
        
        except Exception as e:
            logger.error(f"Error fetching video metadata: {str(e)}")
            return {
                "duration_minutes": None,
                "thumbnail_url": None,
                "title": None
            }
    
    @staticmethod
    async def get_transcript(video_id: str) -> Optional[str]:
        """
        Fetch video transcript (if available).
        
        Note: This requires additional library (youtube-transcript-api)
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            Transcript text or None
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Combine all transcript entries
            full_text = "\n".join([entry["text"] for entry in transcript])
            
            return full_text
        
        except Exception as e:
            logger.warning(f"Could not fetch transcript: {str(e)}")
            return None
    
    @staticmethod
    def _parse_iso_duration(duration_str: str) -> int:
        """
        Parse ISO 8601 duration string to seconds.
        
        Example: PT1H2M3S = 3723 seconds
        
        Args:
            duration_str: ISO duration string
        
        Returns:
            Duration in seconds
        """
        pattern = r'P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return 0
        
        years, months, weeks, days, hours, minutes, seconds = match.groups()
        
        total_seconds = (
            int(years or 0) * 365 * 24 * 3600 +
            int(months or 0) * 30 * 24 * 3600 +
            int(weeks or 0) * 7 * 24 * 3600 +
            int(days or 0) * 24 * 3600 +
            int(hours or 0) * 3600 +
            int(minutes or 0) * 60 +
            int(float(seconds or 0))
        )
        
        return total_seconds
```

---

## SUMMARY

This document provides:

✅ **Standard patterns** for all endpoint types  
✅ **Service layer** best practices  
✅ **Database model** structure  
✅ **API schema** validation  
✅ **Error handling** framework  
✅ **Authentication** implementation  
✅ **Testing** patterns  
✅ **Critical implementations** with full code  

**Follow these patterns consistently for clean, maintainable code.**

---

**Document Version:** 1.0  
**Status:** Reference Guide  
**Last Updated:** January 15, 2026
