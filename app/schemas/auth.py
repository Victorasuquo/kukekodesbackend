"""
Pydantic models for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from uuid import UUID


# ============================================================================
# REQUEST MODELS
# ============================================================================

class UserRegisterRequest(BaseModel):
    """User registration request."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars)",
    )
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    is_minor: bool = Field(False, description="Minor self-registration is not allowed")
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
    
    class Config:
        example = {
            "email": "user@example.com",
            "password": "MyPassword123",
            "first_name": "John",
            "last_name": "Doe",
            "country": "Nigeria",
        }


class UserLoginRequest(BaseModel):
    """User login request."""
    
    learner_id: str = Field(..., min_length=3, max_length=32, description="Generated learner ID")
    password: str = Field(..., description="Password")
    
    class Config:
        example = {
            "learner_id": "KK-1234ABCD",
            "password": "MyPassword123",
        }


class AdminCreateRequest(BaseModel):
    """Admin creation request (by super-admin only)."""
    
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    
    class Config:
        example = {
            "email": "admin@kukekodes.com",
            "password": "AdminPassword123",
            "first_name": "Admin",
            "last_name": "User",
        }


class PasswordResetRequest(BaseModel):
    """Password reset request (step 1: request token)."""
    
    contact_email: EmailStr
    learner_id: str = Field(..., min_length=3, max_length=32)
    
    class Config:
        example = {"contact_email": "shared@example.com", "learner_id": "KK-1234ABCD"}


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation (step 2: reset with token)."""
    
    token: str
    new_password: str = Field(min_length=8, max_length=128)
    
    class Config:
        example = {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "new_password": "NewPassword123",
        }


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    
    refresh_token: str
    
    class Config:
        example = {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class TokenResponse(BaseModel):
    """Token response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User response (minimal)."""
    
    id: UUID
    learner_id: str
    contact_email: Optional[str] = None
    email: str
    first_name: str
    last_name: str
    username: Optional[str]
    profile_picture_url: Optional[str]
    country: Optional[str]
    role: str
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """User response with full details."""
    
    bio: Optional[str]
    timezone: str
    preferred_language: str
    is_email_verified: bool
    last_login_at: Optional[str]


class AuthResponse(BaseModel):
    """Complete authentication response."""
    
    user: UserResponse
    token: TokenResponse
    message: str = "Authentication successful"


class PasswordResetInitResponse(BaseModel):
    """Password reset initialization response."""
    
    message: str = "Password reset email sent"
    email: str


class SuccessResponse(BaseModel):
    """Generic success response."""
    
    success: bool
    message: str
    
    class Config:
        example = {
            "success": True,
            "message": "Operation completed successfully",
        }


class ErrorResponse(BaseModel):
    """Error response."""
    
    error: str
    detail: Optional[str] = None
    
    class Config:
        example = {
            "error": "validation_error",
            "detail": "Email already exists",
        }
