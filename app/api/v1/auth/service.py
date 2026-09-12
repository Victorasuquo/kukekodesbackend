"""
Authentication business logic.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Tuple
from uuid import UUID
import logging

from app.models.user import User, UserRole, UserProfile
from app.models.progress import Streak
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.services.email_service import email_service
from app.dependencies import ValidationError, ConflictError

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service with business logic."""
    
    @staticmethod
    def register_user(
        db: Session,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        country: Optional[str] = None,
    ) -> User:
        """
        Register a new user.
        
        Args:
            db: Database session
            email: User email
            password: User password (plain)
            first_name: First name
            last_name: Last name
            country: Optional country
        
        Returns:
            Created user object
        
        Raises:
            ConflictError: If email already exists
        """
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email.lower()).first()
        if existing_user:
            raise ConflictError(f"Email '{email}' is already registered")
        
        # Create new user
        user = User(
            email=email.lower(),
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            country=country,
            role=UserRole.STUDENT,
            is_active=True,
        )
        
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"User registered: {user.email}")
            
            # Create user profile
            profile = UserProfile(user_id=user.id)
            db.add(profile)
            
            # Create streak tracker
            streak = Streak(user_id=user.id)
            db.add(streak)
            
            db.commit()
            
            # Send welcome email (non-blocking)
            try:
                email_service.send_welcome_email(
                    user_email=user.email,
                    user_name=user.first_name,
                    dashboard_url="https://kukekodes.com/dashboard",
                )
            except Exception as e:
                logger.error(f"Failed to send welcome email: {str(e)}")
            
            return user
        
        except IntegrityError:
            db.rollback()
            raise ConflictError("Email already registered")
        except Exception as e:
            db.rollback()
            logger.error(f"Error registering user: {str(e)}")
            raise
    
    @staticmethod
    def create_admin(
        db: Session,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        by_admin_id: UUID,
    ) -> User:
        """
        Create a new admin user (admin-only operation).
        
        Args:
            db: Database session
            email: Admin email
            password: Admin password
            first_name: First name
            last_name: Last name
            by_admin_id: ID of admin creating this user
        
        Returns:
            Created admin user
        
        Raises:
            ConflictError: If email exists
        """
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email.lower()).first()
        if existing_user:
            raise ConflictError(f"Email '{email}' is already registered")
        
        # Create admin user
        admin_user = User(
            email=email.lower(),
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN,
            is_active=True,
            is_email_verified=True,
        )
        
        try:
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            logger.info(f"Admin user created: {admin_user.email} by {by_admin_id}")
            
            return admin_user
        except IntegrityError:
            db.rollback()
            raise ConflictError("Email already registered")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating admin: {str(e)}")
            raise
    
    @staticmethod
    def login_user(
        db: Session,
        email: str,
        password: str,
    ) -> Tuple[User, str, str]:
        """
        Authenticate user and return tokens.
        
        Args:
            db: Database session
            email: User email
            password: User password (plain)
        
        Returns:
            Tuple of (user, access_token, refresh_token)
        
        Raises:
            ValidationError: If credentials are invalid
        """
        user = db.query(User).filter(User.email == email.lower()).first()
        
        if not user or not verify_password(password, user.password_hash):
            raise ValidationError("Invalid email or password")
        
        if not user.is_active:
            raise ValidationError("User account is inactive")
        
        # Create tokens
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role.value,
            username=user.username,
        )
        
        refresh_token = create_refresh_token(
            user_id=str(user.id),
            email=user.email,
        )
        
        # Update last login
        from datetime import datetime
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"User logged in: {user.email}")
        
        return user, access_token, refresh_token
    
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> str:
        """
        Create new access token from refresh token.
        
        Args:
            refresh_token: Refresh token
        
        Returns:
            New access token
        
        Raises:
            ValidationError: If token is invalid
        """
        try:
            payload = decode_token(refresh_token)
            
            # Verify it's a refresh token
            if payload.get("type") != "refresh":
                raise ValidationError("Invalid token type")
            
            user_id = payload.get("sub")
            email = payload.get("email")
            
            if not user_id or not email:
                raise ValidationError("Invalid token data")

            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                raise ValidationError("User account is inactive or unavailable")
            if user.email.lower() != email.lower():
                raise ValidationError("Invalid token data")
            
            # Create new access token
            access_token = create_access_token(
                user_id=user_id,
                email=user.email,
                role=user.role.value,
                username=user.username,
            )
            
            return access_token
        
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise ValidationError("Invalid or expired refresh token")
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error fetching user: {str(e)}")
            return None
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            return db.query(User).filter(User.email == email.lower()).first()
        except Exception as e:
            logger.error(f"Error fetching user: {str(e)}")
            return None
    
    @staticmethod
    def update_user_profile(
        db: Session,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        bio: Optional[str] = None,
        country: Optional[str] = None,
        timezone: Optional[str] = None,
        profile_picture_url: Optional[str] = None,
    ) -> User:
        """Update user profile information."""
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError("User not found")
        
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if bio:
            user.bio = bio
        if country:
            user.country = country
        if timezone:
            user.timezone = timezone
        if profile_picture_url:
            user.profile_picture_url = profile_picture_url
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User profile updated: {user.email}")
        
        return user
    
    @staticmethod
    def deactivate_user(db: Session, user_id: str) -> None:
        """Deactivate user account."""
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError("User not found")
        
        user.is_active = False
        db.commit()
        
        logger.info(f"User deactivated: {user.email}")
