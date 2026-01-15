"""
Re-export auth schemas from app.schemas.auth for API v1.
This file acts as a convenience import point for the auth module.
"""

from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    AdminCreateRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    UserDetailResponse,
    AuthResponse,
    PasswordResetInitResponse,
    SuccessResponse,
    ErrorResponse,
)

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "AdminCreateRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "RefreshTokenRequest",
    "TokenResponse",
    "UserResponse",
    "UserDetailResponse",
    "AuthResponse",
    "PasswordResetInitResponse",
    "SuccessResponse",
    "ErrorResponse",
]
