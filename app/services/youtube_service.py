"""
YouTube API integration service.
Fetches video metadata, duration, thumbnails, etc.
"""

import logging
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for YouTube API operations."""
    
    YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"
    TIMEOUT = settings.EXTERNAL_API_TIMEOUT
    
    def __init__(self):
        """Initialize YouTube service."""
        self.api_key = settings.YOUTUBE_API_KEY
        if not self.api_key:
            logger.warning("YOUTUBE_API_KEY not configured. YouTube metadata fetching will be disabled.")
    
    def extract_video_id(self, youtube_url: str) -> Optional[str]:
        """
        Extract YouTube video ID from various URL formats.
        
        Supports:
        - https://www.youtube.com/watch?v=dQw4w9WgXcQ
        - https://youtu.be/dQw4w9WgXcQ
        - https://www.youtube.com/embed/dQw4w9WgXcQ
        - dQw4w9WgXcQ (raw ID)
        
        Args:
            youtube_url: YouTube URL or video ID
        
        Returns:
            Video ID or None if invalid
        """
        if not youtube_url:
            return None
        
        youtube_url = youtube_url.strip()
        
        # If it's already a video ID (11 alphanumeric chars)
        if len(youtube_url) == 11 and youtube_url.replace("-", "").replace("_", "").isalnum():
            return youtube_url
        
        # Extract from different URL formats
        patterns = [
            r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]+)",
            r"(?:youtube\.com\/watch\?.*v=)([a-zA-Z0-9_-]+)",
            r"(?:youtube\.com\/v\/)([a-zA-Z0-9_-]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        
        return None
    
    async def get_video_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch video metadata from YouTube API.
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            Dictionary with video metadata or None if failed
        """
        if not self.api_key:
            logger.warning("Cannot fetch YouTube metadata: API key not configured")
            return self._get_fallback_metadata(video_id)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.YOUTUBE_API_BASE_URL}/videos",
                    params={
                        "id": video_id,
                        "key": self.api_key,
                        "part": "snippet,contentDetails,statistics",
                        "fields": "items(id,snippet(title,description,thumbnails),contentDetails(duration),statistics(viewCount))",
                    },
                    timeout=self.TIMEOUT,
                )
                
                if response.status_code != 200:
                    logger.error(f"YouTube API error: {response.status_code}")
                    return self._get_fallback_metadata(video_id)
                
                data = response.json()
                
                if not data.get("items"):
                    logger.warning(f"Video not found: {video_id}")
                    return None
                
                item = data["items"][0]
                
                # Parse ISO 8601 duration to minutes
                duration_minutes = self._parse_duration(
                    item.get("contentDetails", {}).get("duration", "")
                )
                
                # Get best thumbnail
                thumbnails = item.get("snippet", {}).get("thumbnails", {})
                thumbnail_url = (
                    thumbnails.get("high", {}).get("url") or
                    thumbnails.get("medium", {}).get("url") or
                    thumbnails.get("default", {}).get("url")
                )
                
                return {
                    "video_id": video_id,
                    "title": item.get("snippet", {}).get("title"),
                    "description": item.get("snippet", {}).get("description"),
                    "duration_minutes": duration_minutes,
                    "thumbnail_url": thumbnail_url,
                    "view_count": item.get("statistics", {}).get("viewCount", 0),
                }
        
        except httpx.TimeoutException:
            logger.error(f"YouTube API timeout for video {video_id}")
            return self._get_fallback_metadata(video_id)
        except Exception as e:
            logger.error(f"Error fetching YouTube metadata: {str(e)}")
            return self._get_fallback_metadata(video_id)
    
    def _get_fallback_metadata(self, video_id: str) -> Dict[str, Any]:
        """Get minimal fallback metadata when API is unavailable."""
        return {
            "video_id": video_id,
            "title": None,
            "description": None,
            "duration_minutes": None,
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            "view_count": 0,
        }
    
    @staticmethod
    def _parse_duration(iso_duration: str) -> Optional[int]:
        """
        Parse ISO 8601 duration format to minutes.
        Example: PT1H23M45S -> 83
        
        Args:
            iso_duration: ISO 8601 duration string
        
        Returns:
            Duration in minutes or None if parsing failed
        """
        if not iso_duration:
            return None
        
        try:
            # Pattern: PT[hours]H[minutes]M[seconds]S
            pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
            match = re.match(pattern, iso_duration)
            
            if not match:
                return None
            
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            
            total_minutes = (hours * 60) + minutes + (seconds / 60)
            return int(total_minutes)
        
        except Exception as e:
            logger.error(f"Error parsing duration {iso_duration}: {str(e)}")
            return None
    
    def get_youtube_thumbnail_url(self, video_id: str, quality: str = "high") -> str:
        """
        Get YouTube thumbnail URL without API call.
        
        Args:
            video_id: YouTube video ID
            quality: "high" (hqdefault), "medium" (mqdefault), "default"
        
        Returns:
            Thumbnail URL
        """
        quality_map = {
            "high": "maxresdefault.jpg",
            "medium": "mqdefault.jpg",
            "low": "default.jpg",
        }
        
        file = quality_map.get(quality, "hqdefault.jpg")
        return f"https://img.youtube.com/vi/{video_id}/{file}"


# === SINGLETON INSTANCE ===
youtube_service = YouTubeService()