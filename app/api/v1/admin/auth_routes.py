"""Admin authentication endpoints.

Platform administration is intentionally separate from learner authentication so
student sessions cannot drift into the admin application.
"""

from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.api.v1.auth.schemas import AuthResponse, TokenResponse, UserResponse
from app.api.v1.auth.service import AuthService
from app.dependencies import ValidationError, get_db
from app.models.identity import SessionAudience
from app.models.user import UserRole
from app.config import settings


router = APIRouter(prefix="/api/v1/admin/auth", tags=["Admin Authentication"])


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def admin_login(
    request: AdminLoginRequest,
    response: Response,
    http_request: Request,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Authenticate a platform administrator through the admin surface."""
    try:
        user = AuthService.authenticate_admin_by_email(
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

    access_token, refresh_token = AuthService.issue_session(
        db,
        user,
        SessionAudience.ADMIN,
        user_agent=http_request.headers.get("user-agent"),
        ip_address=http_request.client.host if http_request.client else None,
    )
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/admin/auth",
    )

    return AuthResponse(
        user=UserResponse(**AuthService.user_response_payload(user)),
        token=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
        message="Admin login successful",
    )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_admin_token(
    response: Response,
    request_refresh_token: Optional[str] = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> TokenResponse:
    if not request_refresh_token:
        raise ValidationError("Refresh token is required")
    access_token, refresh_token = AuthService.refresh_session(db, request_refresh_token, SessionAudience.ADMIN)
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/admin/auth",
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=dict, status_code=status.HTTP_200_OK)
async def admin_logout(
    response: Response,
    request_refresh_token: Optional[str] = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> dict:
    AuthService.revoke_refresh_session(db, request_refresh_token)
    response.delete_cookie(key=settings.REFRESH_COOKIE_NAME, path="/api/v1/admin/auth")
    return {"success": True, "message": "Admin logout successful"}
