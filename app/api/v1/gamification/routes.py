"""
Gamification API endpoints: Badges, Streaks, Leaderboard.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging

from app.api.v1.gamification.service import GamificationService
from app.api.v1.gamification.schemas import (
    BadgeResponse,
    BadgeAwardResponse,
    StreakResponse,
    LeaderboardUserResponse,
)
from app.dependencies import (
    get_db,
    get_student_user,
    get_pagination,
    PaginationParams,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/gamification", tags=["Gamification"])


# ============================================================================
# BADGES ENDPOINTS
# ============================================================================

@router.get(
    "/badges/user",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get user badges",
)
async def get_user_badges(
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get all badges earned by current user.
    
    Returns:
    - List of earned badges with icons
    - When earned
    - Badge level
    """
    try:
        user_id = current_user.get("sub")
        
        badge_awards = GamificationService.get_user_badges(db=db, user_id=user_id)
        
        return {
            "user_id": user_id,
            "badges_earned": len(badge_awards),
            "badges": [
                BadgeAwardResponse(
                    id=award.id,
                    badge_id=award.badge.id,
                    badge_name=award.badge.name,
                    badge_description=award.badge.description,
                    badge_icon_url=award.badge.icon_url,
                    badge_icon_emoji=award.badge.icon_emoji,
                    badge_level=award.badge.level,
                    earned_at=award.earned_at,
                )
                for award in badge_awards
            ],
        }
    
    except Exception as e:
        logger.error(f"Error fetching badges: {str(e)}")
        raise


@router.get(
    "/badges/all",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get all badges",
)
async def get_all_badges(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get all available badges in the system."""
    try:
        badges = GamificationService.get_all_badges(db=db)
        
        return {
            "total_badges": len(badges),
            "badges": [
                BadgeResponse(
                    id=badge.id,
                    name=badge.name,
                    description=badge.description,
                    icon_url=badge.icon_url,
                    icon_emoji=badge.icon_emoji,
                    level=badge.level,
                    criteria_type=badge.criteria_type,
                    criteria_value=badge.criteria_value,
                    xp_reward=badge.xp_reward,
                )
                for badge in badges
            ],
        }
    
    except Exception as e:
        logger.error(f"Error fetching badges: {str(e)}")
        raise


# ============================================================================
# STREAK ENDPOINTS
# ============================================================================

@router.get(
    "/streaks/user",
    response_model=StreakResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user streak",
)
async def get_user_streak(
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> StreakResponse:
    """
    Get user's current and longest streaks.
    
    Returns:
    - Current streak (days)
    - Longest streak (days)
    - Last activity date
    """
    try:
        user_id = current_user.get("sub")
        
        streak = GamificationService.get_user_streak(db=db, user_id=user_id)
        
        return StreakResponse(
            user_id=user_id,
            current_streak_days=streak.current_streak_count,
            longest_streak_days=streak.longest_streak_count,
            last_activity_date=streak.last_activity_date.isoformat() if streak.last_activity_date else None,
            fire_emoji=GamificationService.get_streak_emoji(streak.current_streak_count),
        )
    
    except Exception as e:
        logger.error(f"Error fetching streak: {str(e)}")
        raise


# ============================================================================
# LEADERBOARD ENDPOINTS
# ============================================================================

@router.get(
    "/leaderboard/global",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get global leaderboard",
)
async def get_global_leaderboard(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get global leaderboard by total lessons completed.
    
    Top learners across all courses.
    """
    try:
        leaderboard, total = GamificationService.get_global_leaderboard(
            db=db,
            skip=pagination.skip,
            limit=pagination.limit,
        )
        
        return {
            "type": "global",
            "total_users": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "users": [
                LeaderboardUserResponse(
                    user_id=user_id,
                    user_name=user_name,
                    profile_picture_url=profile_pic,
                    rank=idx + 1,
                    lessons_completed=lessons_completed,
                    courses_completed=courses_completed,
                    xp_points=xp_points,
                )
                for idx, (user_id, user_name, profile_pic, lessons_completed, courses_completed, xp_points) in enumerate(leaderboard)
            ],
        }
    
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {str(e)}")
        raise


@router.get(
    "/leaderboard/streak",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get streak leaderboard",
)
async def get_streak_leaderboard(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get leaderboard by current learning streaks.
    
    Top streakers.
    """
    try:
        leaderboard, total = GamificationService.get_streak_leaderboard(
            db=db,
            skip=pagination.skip,
            limit=pagination.limit,
        )
        
        return {
            "type": "streaks",
            "total_users": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "users": [
                {
                    "rank": idx + 1,
                    "user_id": user_id,
                    "user_name": user_name,
                    "profile_picture_url": profile_pic,
                    "current_streak_days": streak_days,
                    "longest_streak_days": longest_streak,
                }
                for idx, (user_id, user_name, profile_pic, streak_days, longest_streak) in enumerate(leaderboard)
            ],
        }
    
    except Exception as e:
        logger.error(f"Error fetching streak leaderboard: {str(e)}")
        raise


@router.get(
    "/leaderboard/country/{country}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get country leaderboard",
)
async def get_country_leaderboard(
    country: str,
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get leaderboard for a specific country.
    
    Top learners in that country.
    """
    try:
        leaderboard, total = GamificationService.get_country_leaderboard(
            db=db,
            country=country,
            skip=pagination.skip,
            limit=pagination.limit,
        )
        
        return {
            "type": "country",
            "country": country,
            "total_users": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "users": [
                LeaderboardUserResponse(
                    user_id=user_id,
                    user_name=user_name,
                    profile_picture_url=profile_pic,
                    rank=idx + 1,
                    lessons_completed=lessons_completed,
                    courses_completed=courses_completed,
                    xp_points=xp_points,
                )
                for idx, (user_id, user_name, profile_pic, lessons_completed, courses_completed, xp_points) in enumerate(leaderboard)
            ],
        }
    
    except Exception as e:
        logger.error(f"Error fetching country leaderboard: {str(e)}")
        raise


@router.get(
    "/leaderboard/weekly",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get weekly leaderboard",
)
async def get_weekly_leaderboard(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get weekly leaderboard.
    
    Top learners this week (lessons completed).
    """
    try:
        leaderboard, total = GamificationService.get_weekly_leaderboard(
            db=db,
            skip=pagination.skip,
            limit=pagination.limit,
        )
        
        return {
            "type": "weekly",
            "total_users": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "users": [
                {
                    "rank": idx + 1,
                    "user_id": user_id,
                    "user_name": user_name,
                    "profile_picture_url": profile_pic,
                    "lessons_this_week": lessons_this_week,
                }
                for idx, (user_id, user_name, profile_pic, lessons_this_week) in enumerate(leaderboard)
            ],
        }
    
    except Exception as e:
        logger.error(f"Error fetching weekly leaderboard: {str(e)}")
        raise


# ============================================================================
# USER RANK ENDPOINTS
# ============================================================================

@router.get(
    "/rank/global",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get user's global rank",
)
async def get_user_global_rank(
    current_user: Dict[str, Any] = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get current user's rank on global leaderboard."""
    try:
        user_id = current_user.get("sub")
        
        rank_info = GamificationService.get_user_rank(
            db=db,
            user_id=user_id,
        )
        
        return rank_info
    
    except Exception as e:
        logger.error(f"Error fetching user rank: {str(e)}")
        raise