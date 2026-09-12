"""
Pydantic models for gamification.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# ============================================================================
# BADGE MODELS
# ============================================================================

class BadgeResponse(BaseModel):
    """Badge/achievement."""
    
    id: UUID
    name: str
    description: str
    icon_url: Optional[str] = None
    icon_emoji: Optional[str] = None
    level: Optional[str] = None  # bronze, silver, gold, platinum
    criteria_type: Optional[str] = None
    criteria_value: Optional[int] = None
    xp_reward: Optional[int] = None
    
    class Config:
        from_attributes = True


class BadgeAwardResponse(BaseModel):
    """Badge award with badge details and when earned."""
    
    id: UUID
    badge_id: UUID
    badge_name: str
    badge_description: str
    badge_icon_url: Optional[str] = None
    badge_icon_emoji: Optional[str] = None
    badge_level: Optional[str] = None
    earned_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# STREAK MODELS
# ============================================================================

class StreakResponse(BaseModel):
    """User's streak data."""
    
    user_id: UUID
    current_streak_days: int
    longest_streak_days: int
    last_activity_date: Optional[str]
    fire_emoji: str


# ============================================================================
# LEADERBOARD MODELS
# ============================================================================

class LeaderboardUserResponse(BaseModel):
    """User in leaderboard."""
    
    user_id: UUID
    user_name: str
    profile_picture_url: Optional[str]
    rank: int
    lessons_completed: int
    courses_completed: int
    xp_points: int


class UserRankResponse(BaseModel):
    """User's rank information."""
    
    user_id: UUID
    user_name: str
    global_rank: int
    lessons_completed: int
    courses_completed: int
    xp_points: int  