"""Admin authentication endpoints.

Platform administration is intentionally separate from learner authentication so
student sessions cannot drift into the admin application.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.api.v1.auth.schemas import AuthResponse, TokenResponse, UserResponse
from app.api.v1.auth.service import AuthService
from app.dependencies import ValidationError, get_db
from app.models.user import UserRole
from app.security import create_access_token, create_refresh_token
from app.config import settings


router = APIRouter(prefix="/api/v1/admin/auth", tags=["Admin Authentication"])


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def admin_login(
    request: AdminLoginRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Authenticate a platform administrator through the admin surface."""
    try:
        user, _, _ = AuthService.login_user(
            db=db,
            email=request.email,
            password=request.password,
        )
    except ValidationError:
        raise

    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )

    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verified administrator email is required",
        )

    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
        username=user.username,
    )
    refresh_token = create_refresh_token(user_id=str(user.id), email=user.email)

    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            profile_picture_url=user.profile_picture_url,
            country=user.country,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
        ),
        token=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
        message="Admin login successful",
    )
