"""
FastAPI dependency injection utilities.
Used across routes to get database sessions, auth info, etc.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from app.db.postgres import get_db as get_postgres_db
from app.security import (
    get_current_user,
    get_current_admin,
    get_current_student,
    get_optional_user,
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATABASE DEPENDENCIES
# ============================================================================

def get_db() -> Session:
    """Get PostgreSQL database session."""
    return get_postgres_db()


# ============================================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================================

async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    Get current authenticated admin user.
    Raises 403 if user is not admin.
    """
    return current_user


async def get_student_user(
    current_user: Dict[str, Any] = Depends(get_current_student),
) -> Dict[str, Any]:
    """Get current authenticated student user."""
    return current_user


async def get_user_optional(
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, None otherwise."""
    return current_user


# ============================================================================
# AUTHORIZATION HELPERS
# ============================================================================

def check_resource_ownership(
    resource_instructor_id: str,
    current_user: Dict[str, Any],
) -> bool:
    """
    Check if current user owns/can edit resource.
    
    Args:
        resource_instructor_id: ID of resource owner (instructor)
        current_user: Current user data
    
    Returns:
        True if user owns resource or is admin
    """
    user_id = current_user.get("sub")
    user_role = current_user.get("role")
    
    # Admin can edit anything
    if user_role == "admin":
        return True
    
    # Instructor can edit own resources
    if user_id == resource_instructor_id:
        return True
    
    return False


def check_admin_access(current_user: Dict[str, Any]) -> bool:
    """Check if user has admin access."""
    return current_user.get("role") in ["admin", "instructor"]


def get_user_id_from_token(current_user: Dict[str, Any]) -> str:
    """Extract user ID from token."""
    return current_user.get("sub")


def get_user_role_from_token(current_user: Dict[str, Any]) -> str:
    """Extract user role from token."""
    return current_user.get("role", "student")


# ============================================================================
# PAGINATION HELPER
# ============================================================================

class PaginationParams:
    """Pagination parameters for list endpoints."""
    
    def __init__(self, page: int = 1, page_size: int = 20):
        from app.config import settings
        
        self.page = max(1, page)
        self.page_size = min(page_size, settings.MAX_PAGE_SIZE)
        self.skip = (self.page - 1) * self.page_size
        self.limit = self.page_size
    
    def get_offset(self) -> int:
        """Get database offset."""
        return self.skip
    
    def get_limit(self) -> int:
        """Get database limit."""
        return self.limit


def get_pagination(
    page: int = 1,
    page_size: int = 20,
) -> PaginationParams:
    """FastAPI dependency for pagination parameters."""
    return PaginationParams(page=page, page_size=page_size)


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

class ValidationError(HTTPException):
    """Custom validation error."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class NotFoundError(HTTPException):
    """Resource not found error."""
    
    def __init__(self, resource_name: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} with id {resource_id} not found",
        )


class UnauthorizedError(HTTPException):
    """Unauthorized access error."""
    
    def __init__(self, detail: str = "Unauthorized access"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class ConflictError(HTTPException):
    """Conflict error (e.g., duplicate resource)."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )