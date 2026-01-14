"""
Cloudinary integration for media uploads.
Handles user profile pictures, course covers, etc.
"""

import cloudinary
import cloudinary.uploader
from typing import Optional, Dict, Any
import logging
import os

from app.config import settings

logger = logging.getLogger(__name__)


class CloudinaryService:
    """Service for Cloudinary media operations."""
    
    def __init__(self):
        """Initialize Cloudinary."""
        if settings.CLOUDINARY_CLOUD_NAME:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True,
            )
            self.initialized = True
        else:
            self.initialized = False
            logger.warning("Cloudinary not configured. File uploads will be disabled.")
    
    def upload_profile_picture(
        self,
        file_path: str,
        user_id: str,
    ) -> Optional[str]:
        """
        Upload user profile picture.
        
        Args:
            file_path: Path to image file
            user_id: User ID (for folder organization)
        
        Returns:
            Cloudinary URL or None if failed
        """
        if not self.initialized:
            logger.warning("Cloudinary not initialized")
            return None
        
        try:
            result = cloudinary.uploader.upload(
                file_path,
                folder=f"kukekodes/profiles/{user_id}",
                public_id="avatar",
                resource_type="image",
                transformation=[
                    {"width": 200, "height": 200, "crop": "fill", "gravity": "face"},
                    {"quality": "auto"},
                ],
                overwrite=True,
            )
            
            logger.info(f"Profile picture uploaded for user {user_id}")
            return result.get("secure_url")
        
        except Exception as e:
            logger.error(f"Error uploading profile picture: {str(e)}")
            return None
    
    def upload_course_cover(
        self,
        file_path: str,
        course_id: str,
    ) -> Optional[str]:
        """
        Upload course cover image.
        
        Args:
            file_path: Path to image file
            course_id: Course ID
        
        Returns:
            Cloudinary URL or None if failed
        """
        if not self.initialized:
            logger.warning("Cloudinary not initialized")
            return None
        
        try:
            result = cloudinary.uploader.upload(
                file_path,
                folder=f"kukekodes/courses/{course_id}",
                public_id="cover",
                resource_type="image",
                transformation=[
                    {"width": 600, "height": 300, "crop": "fill"},
                    {"quality": "auto"},
                ],
                overwrite=True,
            )
            
            logger.info(f"Course cover uploaded for course {course_id}")
            return result.get("secure_url")
        
        except Exception as e:
            logger.error(f"Error uploading course cover: {str(e)}")
            return None
    
    def upload_badge_icon(
        self,
        file_path: str,
        badge_id: str,
    ) -> Optional[str]:
        """
        Upload badge icon.
        
        Args:
            file_path: Path to image file
            badge_id: Badge ID
        
        Returns:
            Cloudinary URL or None if failed
        """
        if not self.initialized:
            logger.warning("Cloudinary not initialized")
            return None
        
        try:
            result = cloudinary.uploader.upload(
                file_path,
                folder="kukekodes/badges",
                public_id=badge_id,
                resource_type="image",
                transformation=[
                    {"width": 128, "height": 128, "crop": "fill"},
                    {"quality": "auto"},
                ],
                overwrite=True,
            )
            
            logger.info(f"Badge icon uploaded for badge {badge_id}")
            return result.get("secure_url")
        
        except Exception as e:
            logger.error(f"Error uploading badge icon: {str(e)}")
            return None
    
    def upload_resource(
        self,
        file_path: str,
        folder: str,
        public_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Upload a generic resource file.
        
        Args:
            file_path: Path to file
            folder: Cloudinary folder
            public_id: Optional public ID (filename)
        
        Returns:
            Cloudinary URL or None if failed
        """
        if not self.initialized:
            logger.warning("Cloudinary not initialized")
            return None
        
        try:
            result = cloudinary.uploader.upload(
                file_path,
                folder=f"kukekodes/{folder}",
                public_id=public_id,
                quality="auto",
            )
            
            logger.info(f"Resource uploaded to {folder}")
            return result.get("secure_url")
        
        except Exception as e:
            logger.error(f"Error uploading resource: {str(e)}")
            return None
    
    def delete_resource(self, public_id: str) -> bool:
        """
        Delete a resource from Cloudinary.
        
        Args:
            public_id: Public ID of resource to delete
        
        Returns:
            True if deleted, False if failed
        """
        if not self.initialized:
            logger.warning("Cloudinary not initialized")
            return False
        
        try:
            result = cloudinary.uploader.destroy(public_id)
            logger.info(f"Resource deleted: {public_id}")
            return result.get("result") == "ok"
        
        except Exception as e:
            logger.error(f"Error deleting resource: {str(e)}")
            return False
    
    @staticmethod
    def get_transformation_url(
        image_url: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: str = "fill",
        quality: str = "auto",
    ) -> str:
        """
        Generate Cloudinary transformation URL.
        
        Args:
            image_url: Original Cloudinary image URL
            width: Target width
            height: Target height
            crop: Crop mode
            quality: Quality setting
        
        Returns:
            Transformed URL
        """
        if not image_url or "cloudinary" not in image_url:
            return image_url
        
        transformations = []
        
        if width or height:
            t = {}
            if width:
                t["width"] = width
            if height:
                t["height"] = height
            t["crop"] = crop
            transformations.append(t)
        
        transformations.append({"quality": quality})
        
        # Build transformation string
        transform_str = "/".join([
            ",".join([f"{k}_{v}" for k, v in t.items()])
            for t in transformations
        ])
        
        # Insert into URL
        if "/upload/" in image_url:
            return image_url.replace("/upload/", f"/upload/{transform_str}/")
        
        return image_url


# === SINGLETON INSTANCE ===
cloudinary_service = CloudinaryService()