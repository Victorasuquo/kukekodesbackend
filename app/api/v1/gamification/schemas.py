"""
Pydantic models for gamification.
"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


# ============================================================================
# BADGE MODELS
# ============================================================================

class BadgeResponse(BaseModel):
    """Badge/achievement."""
    
    id: UUID
    name: str
    description: str
    icon_url: Optional[str]
    rarity: Optional[str]  # common, rare, epic, legendary


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