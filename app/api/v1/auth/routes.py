"""Learner authentication API endpoints."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.v1.auth.schemas import (
    AdminCreateRequest,
    AuthResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    SuccessResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.api.v1.auth.service import AuthService
from app.config import settings
from app.dependencies import ValidationError, get_admin_user, get_db
from app.models.identity import SessionAudience
from app.models.organization import OrganizationMembership, MembershipStatus
from app.security import get_current_user


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.REFRESH_COOKIE_NAME, path="/api/v1/auth")


def to_auth_response(user, access_token: str, refresh_token: str, message: str) -> AuthResponse:
    return AuthResponse(
        user=UserResponse(**AuthService.user_response_payload(user)),
        token=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
        message=message,
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    response: Response,
    http_request: Request,
    db: Session = Depends(get_db),
) -> AuthResponse:
    user = AuthService.register_user(
        db=db,
        email=request.email,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
        country=request.country,
        is_minor=request.is_minor,
    )
    access_token, refresh_token = AuthService.issue_session(
        db,
        user,
        SessionAudience.LEARNER,
        user_agent=http_request.headers.get("user-agent"),
        ip_address=http_request.client.host if http_request.client else None,
    )
    set_refresh_cookie(response, refresh_token)
    return to_auth_response(user, access_token, refresh_token, "User registered successfully")


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def login(
    request: UserLoginRequest,
    response: Response,
    http_request: Request,
    db: Session = Depends(get_db),
) -> AuthResponse:
    user = AuthService.authenticate_by_learner_id(db, request.learner_id, request.password)
    access_token, refresh_token = AuthService.issue_session(
        db,
        user,
        SessionAudience.LEARNER,
        user_agent=http_request.headers.get("user-agent"),
        ip_address=http_request.client.host if http_request.client else None,
    )
    set_refresh_cookie(response, refresh_token)
    return to_auth_response(user, access_token, refresh_token, "Login successful")


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
@router.post("/refresh-token", response_model=TokenResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
async def refresh_token(
    response: Response,
    request_refresh_token: Optional[str] = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> TokenResponse:
    if not request_refresh_token:
        raise ValidationError("Refresh token is required")
    access_token, refresh_token = AuthService.refresh_session(db, request_refresh_token, SessionAudience.LEARNER)
    set_refresh_cookie(response, refresh_token)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    request_refresh_token: Optional[str] = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> SuccessResponse:
    AuthService.revoke_refresh_session(db, request_refresh_token)
    clear_refresh_cookie(response)
    return SuccessResponse(success=True, message="Logout successful")


@router.post("/logout-all", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def logout_all(
    response: Response,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse:
    AuthService.revoke_all_sessions(db, current_user.get("sub"))
    clear_refresh_cookie(response)
    return SuccessResponse(success=True, message="All sessions revoked")


@router.post("/recovery/request", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def request_recovery(
    request: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> SuccessResponse:
    AuthService.request_password_recovery(db, request.contact_email, request.learner_id)
    return SuccessResponse(
        success=True,
        message="If the learner ID and contact email match, recovery instructions will be sent.",
    )


@router.post("/recovery/confirm", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def confirm_recovery(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db),
) -> SuccessResponse:
    AuthService.confirm_password_recovery(db, request.token, request.new_password)
    return SuccessResponse(success=True, message="Password reset successfully")


@router.get("/session", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def session(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    user = AuthService.get_user_by_id(db, current_user.get("sub"))
    if not user or not user.is_active:
        raise ValidationError("Session is no longer valid")
    memberships = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id,
        OrganizationMembership.status == MembershipStatus.ACTIVE,
    ).all()
    return {
        "user": AuthService.user_response_payload(user),
        "memberships": [
            {
                "organization_id": str(m.organization_id),
                "role": m.role.value,
                "status": m.status.value,
                "joined_at": m.joined_at.isoformat(),
            }
            for m in memberships
        ],
    }


@router.post("/admin/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    request: AdminCreateRequest,
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    admin_user = AuthService.create_admin(
        db=db,
        email=request.email,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
        by_admin_id=current_admin.get("sub"),
    )
    return UserResponse(**AuthService.user_response_payload(admin_user))
