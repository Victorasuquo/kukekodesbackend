"""
SQLAlchemy models for gamification and progress tracking.
Includes: Streak, Badge, BadgeAward models.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Index, UniqueConstraint, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, date

from app.db.postgres import Base


# ============================================================================
# STREAK MODEL - Track user learning streaks
# ============================================================================

class Streak(Base):
    """Track user learning streaks (daily activity tracking)."""
    
    __tablename__ = "streaks"
    
    # === PRIMARY KEY ===
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # === FOREIGN KEY ===
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    
    # === STREAK TRACKING ===
    current_streak_count = Column(Integer, default=0, nullable=False)
    longest_streak_count = Column(Integer, default=0, nullable=False)
    
    # === ACTIVITY TRACKING ===
    last_activity_date = Column(DateTime, nullable=True)
    
    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # === RELATIONSHIPS ===
    user = relationship("User", back_populates="streak")
    
    def __repr__(self) -> str:
        return f"<Streak {self.user_id}: {self.current_streak_count}🔥>"
    
    def increment_streak(self) -> bool:
        """
        Increment streak if activity is today (not yesterday).
        Returns True if streak was incremented, False if already incremented today.
        """
        last_activity = self.last_activity_date.date() if self.last_activity_date else None
        today = date.today()
        yesterday = date.fromordinal(today.toordinal() - 1)
        
        # First activity or activity from yesterday
        if last_activity is None or last_activity == yesterday:
            self.current_streak_count += 1
            self.last_activity_date = datetime.utcnow()
            
            # Update longest streak if current exceeds it
            if self.current_streak_count > self.longest_streak_count:
                self.longest_streak_count = self.current_streak_count
            
            return True
        
        # Activity already today
        elif last_activity == today:
            return False
        
        # Gap in streak (more than 1 day since last activity)
        else:
            self.current_streak_count = 1
            self.last_activity_date = datetime.utcnow()
            return True
    
    def break_streak(self) -> None:
        """Break the current streak (e.g., for inactivity)."""
        self.current_streak_count = 0
        self.last_activity_date = None


# ============================================================================
# BADGE MODEL - Gamification badges/achievements
# ============================================================================

class Badge(Base):
    """Badge definitions - achievements users can earn."""
    
    __tablename__ = "badges"
    
    # === PRIMARY KEY ===
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # === BADGE INFO ===
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    icon_url = Column(String(500), nullable=True)  # Cloudinary URL
    icon_emoji = Column(String(10), nullable=True)  # Fallback emoji (e.g., "🏆")
    
    # === BADGE CRITERIA ===
    criteria_type = Column(
        String(50),
        nullable=False,
        index=True,
    )  # e.g., "lessons_completed", "streak_days", "course_completion", "quiz_score"
    criteria_value = Column(Integer, nullable=False)  # e.g., 10 lessons, 7 days, 90% score
    
    # === BADGE LEVEL ===
    level = Column(String(50), default="bronze", nullable=False)  # bronze, silver, gold, platinum
    xp_reward = Column(Integer, default=10, nullable=False)  # XP points awarded
    
    # === STATUS ===
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # === RELATIONSHIPS ===
    awards = relationship("BadgeAward", back_populates="badge", cascade="all, delete-orphan")
    
    # === INDEXES ===
    __table_args__ = (
        Index("idx_badge_criteria", "criteria_type", "criteria_value"),
        Index("idx_badge_active", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<Badge {self.name} ({self.level})>"


# ============================================================================
# BADGE AWARD MODEL - Tracks which users earned which badges
# ============================================================================

class BadgeAward(Base):
    """Records badge awards to users."""
    
    __tablename__ = "badge_awards"
    
    # === PRIMARY KEY ===
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # === FOREIGN KEYS ===
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    badge_id = Column(
        UUID(as_uuid=True),
        ForeignKey("badges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # === AWARD CONTEXT ===
    earned_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    context = Column(Text, nullable=True)  # JSON or text describing how/why earned (e.g., '{"lesson_id": "...", "course_id": "..."}')
    
    # === CONSTRAINTS ===
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge_award"),
        Index("idx_badge_award_user_earned", "user_id", "earned_at"),
        Index("idx_badge_award_badge_earned", "badge_id", "earned_at"),
    )
    
    # === RELATIONSHIPS ===
    user = relationship("User", back_populates="badge_awards")
    badge = relationship("Badge", back_populates="awards")
    
    def __repr__(self) -> str:
        return f"<BadgeAward {self.user_id} -> {self.badge_id} @ {self.earned_at}>"


# ============================================================================
# LEADERBOARD MODEL - User rankings
# ============================================================================

class Leaderboard(Base):
    """User leaderboard rankings (weekly/monthly/all-time)."""
    
    __tablename__ = "leaderboards"
    
    # === PRIMARY KEY ===
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # === FOREIGN KEY ===
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # === LEADERBOARD TYPE ===
    period = Column(String(50), nullable=False, index=True)  # "all_time", "monthly", "weekly"
    
    # === RANKING DATA ===
    rank = Column(Integer, nullable=False)  # Position in leaderboard
    total_xp = Column(Integer, default=0, nullable=False)
    lessons_completed = Column(Integer, default=0, nullable=False)
    courses_completed = Column(Integer, default=0, nullable=False)
    badge_count = Column(Integer, default=0, nullable=False)
    
    # === TIMESTAMPS ===
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # === CONSTRAINTS ===
    __table_args__ = (
        UniqueConstraint("user_id", "period", name="uq_user_leaderboard_period"),
        Index("idx_leaderboard_period_rank", "period", "rank"),
        Index("idx_leaderboard_total_xp", "period", "total_xp"),
    )
    
    def __repr__(self) -> str:
        return f"<Leaderboard {self.period} - #{self.rank}: {self.total_xp} XP>"
