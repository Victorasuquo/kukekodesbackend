"""
User profile and dashboard endpoints.
"""

from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import shutil
import os
from pathlib import Path

from app.api.v1.users.service import UserService
from app.api.v1.users.schemas import (
    UserProfileResponse,
    UpdateProfileRequest,
    UserDashboardResponse,
)
from app.services.cloudinary_service import cloudinary_service
from app.dependencies import (
    get_db,
    get_student_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["User Profile"])


# ============================================================================
# GET PROFILE
# ============================================================================

@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """
    Get current authenticated user's profile.
    
    Returns:
    - Profile information
    - Settings
    - Statistics
    """
    try:
        user_id = current_user.get("sub")
        
        profile = UserService.get_user_profile(db=db, user_id=user_id)
        
        return profile
    
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        raise


# ============================================================================
# UPDATE PROFILE
# ============================================================================

@router.put(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user profile",
)
async def update_user_profile(
    request: UpdateProfileRequest,
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """
    Update current user's profile.
    
    Can update:
    - First name
    - Last name
    - Bio
    - Country
    - Timezone
    - Preferred language
    """
    try:
        user_id = current_user.get("sub")
        
        profile = UserService.update_user_profile(
            db=db,
            user_id=user_id,
            first_name=request.first_name,
            last_name=request.last_name,
            bio=request.bio,
            country=request.country,
            timezone=request.timezone,
            preferred_language=request.preferred_language,
        )
        
        return profile
    
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise


# ============================================================================
# UPLOAD PROFILE PICTURE
# ============================================================================

@router.post(
    "/me/profile-picture",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Upload profile picture",
)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Upload user profile picture.
    
    Supported formats: JPG, PNG, GIF
    Max size: 5MB
    Automatically resized to 200x200
    """
    try:
        user_id = current_user.get("sub")
        
        # Validate file
        if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
            raise ValueError("Invalid file format. Use JPG, PNG, or GIF")
        
        # Save temporary file
        temp_path = f"/tmp/{user_id}_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Upload to Cloudinary
        image_url = cloudinary_service.upload_profile_picture(
            file_path=temp_path,
            user_id=user_id,
        )
        
        # Clean up temp file
        os.remove(temp_path)
        
        if not image_url:
            raise ValueError("Failed to upload image")
        
        # Update user profile
        profile = UserService.update_user_profile(
            db=db,
            user_id=user_id,
            profile_picture_url=image_url,
        )
        
        return {
            "success": True,
            "message": "Profile picture uploaded successfully",
            "profile_picture_url": image_url,
        }
    
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}")
        raise
    finally:
        file.file.close()


# ============================================================================
# GET USER DASHBOARD
# ============================================================================

@router.get(
    "/dashboard",
    response_model=UserDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user dashboard",
    description="Get comprehensive user learning dashboard",
)
async def get_user_dashboard(
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> UserDashboardResponse:
    """
    Get complete user learning dashboard.
    
    Includes:
    - Enrolled courses with progress
    - Current learning streaks
    - Recent achievements/badges
    - Learning statistics
    - Recommendations
    - Recent activity
    """
    try:
        user_id = current_user.get("sub")
        
        dashboard = UserService.get_user_dashboard(
            db=db,
            user_id=user_id,
        )
        
        return dashboard
    
    except Exception as e:
        logger.error(f"Error fetching dashboard: {str(e)}")
        raise


# ============================================================================
# GET ENROLLED COURSES
# ============================================================================

@router.get(
    "/courses/enrolled",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get enrolled courses",
)
async def get_enrolled_courses(
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get all courses user is enrolled in.
    
    Includes:
    - Course details
    - Progress percentage
    - Current lesson
    - Completion status
    """
    try:
        user_id = current_user.get("sub")
        
        courses = UserService.get_enrolled_courses(
            db=db,
            user_id=user_id,
        )
        
        return {
            "total_enrolled": len(courses),
            "courses": courses,
        }
    
    except Exception as e:
        logger.error(f"Error fetching enrolled courses: {str(e)}")
        raise


# ============================================================================
# GET PROFILE PUBLIC VIEW
# ============================================================================

@router.get(
    "/{user_id}/public",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get public user profile",
)
async def get_public_profile(
    user_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get public user profile (badges, achievements, stats).
    
    Only shows information user has made public.
    """
    try:
        profile = UserService.get_public_profile(
            db=db,
            user_id=user_id,
        )
        
        return profile
    
    except Exception as e:
        logger.error(f"Error fetching public profile: {str(e)}")
        raise


# ============================================================================
# NOTIFICATION PREFERENCES
# ============================================================================

@router.get(
    "/me/notification-preferences",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get notification preferences",
)
async def get_notification_preferences(
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get user's notification preferences."""
    try:
        user_id = current_user.get("sub")
        
        preferences = UserService.get_notification_preferences(
            db=db,
            user_id=user_id,
        )
        
        return preferences
    
    except Exception as e:
        logger.error(f"Error fetching preferences: {str(e)}")
        raise


@router.put(
    "/me/notification-preferences",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Update notification preferences",
)
async def update_notification_preferences(
    preferences: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Update notification preferences."""
    try:
        user_id = current_user.get("sub")
        
        updated = UserService.update_notification_preferences(
            db=db,
            user_id=user_id,
            preferences=preferences,
        )
        
        return {
            "success": True,
            "message": "Preferences updated",
            "preferences": updated,
        }
    
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise


# ============================================================================
# ACCOUNT SETTINGS
# ============================================================================

@router.post(
    "/me/change-password",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Change password",
)
async def change_password(
    request: Dict[str, str],
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Change user's password.
    
    Requires:
    - current_password
    - new_password
    """
    try:
        user_id = current_user.get("sub")
        
        success = UserService.change_password(
            db=db,
            user_id=user_id,
            current_password=request.get("current_password"),
            new_password=request.get("new_password"),
        )
        
        if success:
            return {
                "success": True,
                "message": "Password changed successfully",
            }
        else:
            return {
                "success": False,
                "message": "Failed to change password",
            }
    
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise


@router.post(
    "/me/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate account",
)
async def deactivate_account(
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
):
    """
    Deactivate user account.
    
    WARNING: This cannot be undone immediately.
    """
    try:
        user_id = current_user.get("sub")
        
        UserService.deactivate_account(db=db, user_id=user_id)
        
        return None
    
    except Exception as e:
        logger.error(f"Error deactivating account: {str(e)}")
        raise