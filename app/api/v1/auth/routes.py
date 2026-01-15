"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.api.v1.auth.service import AuthService
from app.api.v1.auth.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    AdminCreateRequest,
    RefreshTokenRequest,
    AuthResponse,
    UserResponse,
    TokenResponse,
    SuccessResponse,
)
from app.dependencies import (
    get_db,
    get_admin_user,
    ValidationError,
)
from app.security import create_access_token, create_refresh_token
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ============================================================================
# PUBLIC ENDPOINTS (No authentication required)
# ============================================================================

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new student account",
)
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Register a new user account.
    
    - **email**: Valid email address
    - **password**: Minimum 8 characters with uppercase, lowercase, and digit
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **country**: Optional country
    """
    try:
        # Register user
        user = AuthService.register_user(
            db=db,
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            country=request.country,
        )
        
        # Create tokens
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role.value,
        )
        refresh_token = create_refresh_token(
            user_id=str(user.id),
            email=user.email,
        )
        
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
            message="User registered successfully",
        )
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user and return access token",
)
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Login with email and password.
    
    Returns access and refresh tokens.
    """
    try:
        user, access_token, refresh_token = AuthService.login_user(
            db=db,
            email=request.email,
            password=request.password,
        )
        
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
            message="Login successful",
        )
    
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.post(
    "/refresh-token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Get a new access token using refresh token",
)
async def refresh_token(
    request: RefreshTokenRequest,
) -> TokenResponse:
    """
    Get a new access token using a valid refresh token.
    """
    try:
        access_token = AuthService.refresh_access_token(request.refresh_token)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=request.refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


# ============================================================================
# ADMIN-ONLY ENDPOINTS
# ============================================================================

@router.post(
    "/admin/create",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create admin user",
    description="Create a new admin account (admin only)",
)
async def create_admin(
    request: AdminCreateRequest,
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Create a new admin user account.
    
    Only existing admins can perform this action.
    """
    try:
        admin_user = AuthService.create_admin(
            db=db,
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            by_admin_id=current_admin.get("sub"),
        )
        
        return UserResponse(
            id=admin_user.id,
            email=admin_user.email,
            first_name=admin_user.first_name,
            last_name=admin_user.last_name,
            username=admin_user.username,
            profile_picture_url=admin_user.profile_picture_url,
            country=admin_user.country,
            role=admin_user.role.value,
            is_active=admin_user.is_active,
            created_at=admin_user.created_at.isoformat(),
        )
    
    except Exception as e:
        logger.error(f"Admin creation error: {str(e)}")
        raise


@router.post(
    "/logout",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Logout current user (invalidate tokens)",
)
async def logout(
    current_user: Dict[str, Any] = Depends(lambda: None),
) -> SuccessResponse:
    """
    Logout user.
    
    Note: JWT tokens are stateless, so actual logout is handled client-side
    by removing the tokens. This endpoint is for symmetry and future use
    (e.g., token blacklist).
    """
    return SuccessResponse(
        success=True,
        message="Logout successful. Please clear tokens on client-side.",
    )