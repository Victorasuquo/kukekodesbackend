"""
Gamification business logic: Badges, Streaks, Leaderboards.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import logging

from app.models.progress import Badge, BadgeAward, Streak, Leaderboard
from app.models.enrollment import UserProgress, Enrollment
from app.models.user import User

logger = logging.getLogger(__name__)


class GamificationService:
    """Service for gamification features."""
    
    # ========================================================================
    # BADGES
    # ========================================================================
    
    @staticmethod
    def get_user_badges(db: Session, user_id: str) -> List[BadgeAward]:
        """Get all badges earned by user with their award details."""
        badge_awards = db.query(BadgeAward).filter(
            BadgeAward.user_id == user_id,
        ).order_by(BadgeAward.earned_at.desc()).all()
        
        return badge_awards
    
    @staticmethod
    def get_user_badge_objects(db: Session, user_id: str) -> List[Badge]:
        """Get all badge objects earned by user."""
        badges = db.query(Badge).join(BadgeAward).filter(
            BadgeAward.user_id == user_id,
        ).order_by(Badge.name).all()
        
        return badges
    
    @staticmethod
    def get_all_badges(db: Session) -> List[Badge]:
        """Get all badges available in system."""
        badges = db.query(Badge).filter(Badge.is_active == True).all()
        return badges
    
    # ========================================================================
    # STREAKS
    # ========================================================================
    
    @staticmethod
    def get_user_streak(db: Session, user_id: str) -> Optional[Streak]:
        """Get user's streak."""
        streak = db.query(Streak).filter(Streak.user_id == user_id).first()
        return streak
    
    @staticmethod
    def get_streak_emoji(streak_count: int) -> str:
        """Get fire emoji based on streak count."""
        if streak_count == 0:
            return "🔲"
        elif streak_count < 7:
            return "🔥"
        elif streak_count < 30:
            return "🔥🔥"
        elif streak_count < 60:
            return "🔥🔥🔥"
        elif streak_count < 90:
            return "🔥🔥🔥🔥"
        else:
            return "🔥🔥🔥🔥🔥"
    
    # ========================================================================
    # LEADERBOARDS
    # ========================================================================
    
    @staticmethod
    def get_global_leaderboard(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Tuple], int]:
        """
        Get global leaderboard by lessons completed.
        
        Returns:
            List of (user_id, user_name, profile_pic, lessons_completed, courses_completed, xp_points)
        """
        # Subquery: lessons completed per user
        lessons_completed = db.query(
            UserProgress.user_id,
            func.count(UserProgress.lesson_id).label('lessons_count'),
        ).filter(
            UserProgress.is_completed == True,
        ).group_by(UserProgress.user_id).subquery()
        
        # Subquery: courses completed per user
        courses_completed = db.query(
            Enrollment.user_id,
            func.count(Enrollment.course_id).label('courses_count'),
        ).filter(
            Enrollment.is_completed == True,
        ).group_by(Enrollment.user_id).subquery()
        
        # Main query
        results = db.query(
            User.id,
            User.first_name.concat(' ', User.last_name).label('user_name'),
            User.profile_picture_url,
            lessons_completed.c.lessons_count,
            courses_completed.c.courses_count,
        ).outerjoin(
            lessons_completed, User.id == lessons_completed.c.user_id,
        ).outerjoin(
            courses_completed, User.id == courses_completed.c.user_id,
        ).filter(
            User.is_active == True,
        ).order_by(
            lessons_completed.c.lessons_count.desc(),
            courses_completed.c.courses_count.desc(),
        ).offset(skip).limit(limit).all()
        
        # Total count
        total = db.query(User).filter(User.is_active == True).count()
        
        # Add XP calculation
        final_results = [
            (
                result[0],
                result[1],
                result[2],
                result[3] or 0,
                result[4] or 0,
                (result[3] or 0) * 10 + (result[4] or 0) * 100,  # XP calculation
            )
            for result in results
        ]
        
        return final_results, total
    
    @staticmethod
    def get_streak_leaderboard(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Tuple], int]:
        """Get leaderboard by current streaks."""
        results = db.query(
            User.id,
            User.first_name.concat(' ', User.last_name).label('user_name'),
            User.profile_picture_url,
            Streak.current_streak_count,
            Streak.longest_streak_count,
        ).outerjoin(
            Streak, User.id == Streak.user_id,
        ).filter(
            User.is_active == True,
        ).order_by(
            Streak.current_streak_count.desc(),
        ).offset(skip).limit(limit).all()
        
        total = db.query(User).filter(User.is_active == True).count()
        
        return results, total
    
    @staticmethod
    def get_country_leaderboard(
        db: Session,
        country: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Tuple], int]:
        """Get leaderboard for a specific country."""
        # Subquery: lessons completed per user
        lessons_completed = db.query(
            UserProgress.user_id,
            func.count(UserProgress.lesson_id).label('lessons_count'),
        ).filter(
            UserProgress.is_completed == True,
        ).group_by(UserProgress.user_id).subquery()
        
        # Subquery: courses completed per user
        courses_completed = db.query(
            Enrollment.user_id,
            func.count(Enrollment.course_id).label('courses_count'),
        ).filter(
            Enrollment.is_completed == True,
        ).group_by(Enrollment.user_id).subquery()
        
        # Main query
        results = db.query(
            User.id,
            User.first_name.concat(' ', User.last_name).label('user_name'),
            User.profile_picture_url,
            lessons_completed.c.lessons_count,
            courses_completed.c.courses_count,
        ).outerjoin(
            lessons_completed, User.id == lessons_completed.c.user_id,
        ).outerjoin(
            courses_completed, User.id == courses_completed.c.user_id,
        ).filter(
            and_(
                User.is_active == True,
                User.country == country,
            ),
        ).order_by(
            lessons_completed.c.lessons_count.desc(),
        ).offset(skip).limit(limit).all()
        
        # Total count
        total = db.query(User).filter(
            and_(
                User.is_active == True,
                User.country == country,
            ),
        ).count()
        
        # Add XP
        final_results = [
            (
                result[0],
                result[1],
                result[2],
                result[3] or 0,
                result[4] or 0,
                (result[3] or 0) * 10 + (result[4] or 0) * 100,
            )
            for result in results
        ]
        
        return final_results, total
    
    @staticmethod
    def get_weekly_leaderboard(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Tuple], int]:
        """Get leaderboard by lessons completed this week."""
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Subquery: lessons completed this week
        lessons_this_week = db.query(
            UserProgress.user_id,
            func.count(UserProgress.lesson_id).label('lessons_count'),
        ).filter(
            and_(
                UserProgress.is_completed == True,
                UserProgress.completed_at >= one_week_ago,
            ),
        ).group_by(UserProgress.user_id).subquery()
        
        # Main query
        results = db.query(
            User.id,
            User.first_name.concat(' ', User.last_name).label('user_name'),
            User.profile_picture_url,
            lessons_this_week.c.lessons_count,
        ).outerjoin(
            lessons_this_week, User.id == lessons_this_week.c.user_id,
        ).filter(
            User.is_active == True,
        ).order_by(
            lessons_this_week.c.lessons_count.desc(),
        ).offset(skip).limit(limit).all()
        
        total = db.query(User).filter(User.is_active == True).count()
        
        return results, total
    
    @staticmethod
    def get_user_rank(db: Session, user_id: str) -> dict:
        """Get user's rank on global leaderboard."""
        # Count users with more lessons completed
        user_lessons = db.query(func.count(UserProgress.lesson_id)).filter(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.is_completed == True,
            ),
        ).scalar() or 0
        
        rank = db.query(func.count(UserProgress.user_id.distinct())).filter(
            and_(
                UserProgress.is_completed == True,
            ),
        ).group_by(
            UserProgress.user_id,
        ).filter(
            func.count(UserProgress.lesson_id) > user_lessons,
        ).count()
        
        rank = rank + 1
        
        # Get user info
        user = db.query(User).filter(User.id == user_id).first()
        
        return {
            "user_id": user_id,
            "user_name": user.get_full_name() if user else None,
            "global_rank": rank,
            "lessons_completed": user_lessons,
        }