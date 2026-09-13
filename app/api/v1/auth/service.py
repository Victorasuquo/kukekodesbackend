"""Authentication business logic."""

import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import ConflictError, ValidationError
from app.models.identity import Credential, PasswordRecoveryToken, RefreshSession, SessionAudience
from app.models.notification import NotificationPreference
from app.models.progress import Streak
from app.models.user import User, UserProfile, UserRole
from app.security import create_access_token, hash_password, verify_password


class AuthService:
    """Authentication service with learner-id credentials and server sessions."""

    @staticmethod
    def normalize_email(email: Optional[str]) -> Optional[str]:
        return email.strip().lower() if email else None

    @staticmethod
    def token_hash(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_learner_id(db: Session) -> str:
        alphabet = string.ascii_uppercase + string.digits
        while True:
            suffix = "".join(secrets.choice(alphabet) for _ in range(8))
            learner_id = f"KK-{suffix}"
            if not db.query(User).filter(User.learner_id == learner_id).first():
                return learner_id

    @staticmethod
    def _ensure_credential(db: Session, user: User) -> Credential:
        credential = db.query(Credential).filter(Credential.user_id == user.id).first()
        if credential:
            return credential
        if not user.password_hash:
            raise ValidationError("Password credential is unavailable")
        credential = Credential(user_id=user.id, password_hash=user.password_hash, credential_version=1)
        db.add(credential)
        db.flush()
        return credential

    @staticmethod
    def _record_failed_login(db: Session, credential: Optional[Credential]) -> None:
        if not credential:
            return
        credential.failed_attempts += 1
        if credential.failed_attempts >= 5:
            credential.locked_until = datetime.utcnow() + timedelta(minutes=15)
        db.flush()

    @staticmethod
    def _touch_successful_login(db: Session, user: User, credential: Credential) -> None:
        user.last_login_at = datetime.utcnow()
        credential.failed_attempts = 0
        credential.locked_until = None
        db.flush()

    @staticmethod
    def user_response_payload(user: User) -> dict:
        return {
            "id": user.id,
            "learner_id": user.learner_id,
            "email": user.contact_email or user.email,
            "contact_email": user.contact_email or user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "profile_picture_url": user.profile_picture_url,
            "country": user.country,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
        }

    @staticmethod
    def register_user(
        db: Session,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        country: Optional[str] = None,
        is_minor: bool = False,
    ) -> User:
        """Register an adult learner with a generated learner ID."""
        if is_minor:
            raise ValidationError("Minor accounts must be provisioned by a guardian or organization")

        normalized_email = AuthService.normalize_email(email)
        password_hash = hash_password(password)
        user = User(
            learner_id=AuthService.generate_learner_id(db),
            contact_email=normalized_email,
            email=normalized_email or f"{secrets.token_hex(8)}@contact.invalid",
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            country=country,
            role=UserRole.STUDENT,
            is_active=True,
        )

        try:
            db.add(user)
            db.flush()
            db.add(Credential(user_id=user.id, password_hash=password_hash))
            db.add(UserProfile(user_id=user.id))
            db.add(Streak(user_id=user.id))
            db.add(NotificationPreference(user_id=user.id))
            db.commit()
            db.refresh(user)
            return user
        except Exception:
            db.rollback()
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
        normalized_email = AuthService.normalize_email(email)
        existing_admin = db.query(User).filter(
            or_(User.contact_email == normalized_email, User.email == normalized_email),
            User.role == UserRole.ADMIN,
        ).first()
        if existing_admin:
            raise ConflictError(f"Admin email '{email}' is already registered")

        password_hash = hash_password(password)
        admin_user = User(
            learner_id=AuthService.generate_learner_id(db),
            contact_email=normalized_email,
            email=normalized_email or f"{secrets.token_hex(8)}@contact.invalid",
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN,
            is_active=True,
            is_email_verified=True,
        )

        db.add(admin_user)
        db.flush()
        db.add(Credential(user_id=admin_user.id, password_hash=password_hash))
        db.commit()
        db.refresh(admin_user)
        return admin_user

    @staticmethod
    def authenticate_by_learner_id(db: Session, learner_id: str, password: str) -> User:
        user = db.query(User).filter(User.learner_id == learner_id.strip().upper()).first()
        credential = AuthService._ensure_credential(db, user) if user else None
        if not user or not credential or credential.revoked_at:
            raise ValidationError("Invalid learner ID or password")
        if credential.locked_until and credential.locked_until > datetime.utcnow():
            raise ValidationError("Account is temporarily locked. Try again later")
        if not verify_password(password, credential.password_hash):
            AuthService._record_failed_login(db, credential)
            db.commit()
            raise ValidationError("Invalid learner ID or password")
        if not user.is_active:
            raise ValidationError("User account is inactive")
        if user.role == UserRole.ADMIN:
            raise ValidationError("Use the admin login route for platform administrator accounts")
        AuthService._touch_successful_login(db, user, credential)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_admin_by_email(db: Session, email: str, password: str) -> User:
        normalized_email = AuthService.normalize_email(email)
        admins = db.query(User).filter(
            or_(User.contact_email == normalized_email, User.email == normalized_email),
            User.role == UserRole.ADMIN,
        ).all()
        if len(admins) != 1:
            raise ValidationError("Invalid admin email or password")
        user = admins[0]
        credential = AuthService._ensure_credential(db, user)
        if credential.revoked_at:
            raise ValidationError("Invalid admin email or password")
        if credential.locked_until and credential.locked_until > datetime.utcnow():
            raise ValidationError("Account is temporarily locked. Try again later")
        if not verify_password(password, credential.password_hash):
            AuthService._record_failed_login(db, credential)
            db.commit()
            raise ValidationError("Invalid admin email or password")
        if not user.is_active:
            raise ValidationError("User account is inactive")
        AuthService._touch_successful_login(db, user, credential)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def issue_session(
        db: Session,
        user: User,
        audience: SessionAudience,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[str, str]:
        credential = AuthService._ensure_credential(db, user)
        raw_refresh_token = secrets.token_urlsafe(48)
        refresh_session = RefreshSession(
            user_id=user.id,
            token_hash=AuthService.token_hash(raw_refresh_token),
            token_family=secrets.token_urlsafe(24),
            audience=audience,
            credential_version=credential.credential_version,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add(refresh_session)
        db.commit()
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.contact_email or user.email,
            role=user.role.value,
            username=user.username,
            audience=audience.value,
            credential_version=credential.credential_version,
        )
        return access_token, raw_refresh_token

    @staticmethod
    def refresh_session(db: Session, raw_refresh_token: str, audience: Optional[SessionAudience] = None) -> Tuple[str, str]:
        session = db.query(RefreshSession).filter(
            RefreshSession.token_hash == AuthService.token_hash(raw_refresh_token),
        ).first()
        if not session or session.revoked_at or session.expires_at <= datetime.utcnow():
            raise ValidationError("Invalid or expired refresh token")
        if audience and session.audience != audience:
            raise ValidationError("Invalid refresh token audience")

        user = db.query(User).filter(User.id == session.user_id).first()
        if not user or not user.is_active:
            raise ValidationError("User account is inactive or unavailable")

        credential = AuthService._ensure_credential(db, user)
        if credential.revoked_at or credential.credential_version != session.credential_version:
            session.revoked_at = datetime.utcnow()
            db.commit()
            raise ValidationError("Session is no longer valid")

        new_raw_refresh_token = secrets.token_urlsafe(48)
        session.rotated_at = datetime.utcnow()
        session.revoked_at = datetime.utcnow()
        db.add(
            RefreshSession(
                user_id=user.id,
                token_hash=AuthService.token_hash(new_raw_refresh_token),
                token_family=session.token_family,
                audience=session.audience,
                credential_version=credential.credential_version,
                user_agent=session.user_agent,
                ip_address=session.ip_address,
                expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                last_used_at=datetime.utcnow(),
            )
        )
        db.commit()
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.contact_email or user.email,
            role=user.role.value,
            username=user.username,
            audience=session.audience.value,
            credential_version=credential.credential_version,
        )
        return access_token, new_raw_refresh_token

    @staticmethod
    def revoke_refresh_session(db: Session, raw_refresh_token: Optional[str]) -> None:
        if not raw_refresh_token:
            return
        session = db.query(RefreshSession).filter(
            RefreshSession.token_hash == AuthService.token_hash(raw_refresh_token),
            RefreshSession.revoked_at.is_(None),
        ).first()
        if session:
            session.revoked_at = datetime.utcnow()
            db.commit()

    @staticmethod
    def revoke_all_sessions(db: Session, user_id: str) -> None:
        db.query(RefreshSession).filter(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
        ).update({"revoked_at": datetime.utcnow()})
        db.commit()

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def request_password_recovery(db: Session, contact_email: str, learner_id: str) -> Optional[str]:
        user = db.query(User).filter(
            User.learner_id == learner_id.strip().upper(),
            User.contact_email == AuthService.normalize_email(contact_email),
            User.is_active.is_(True),
        ).first()
        if not user:
            return None
        raw_token = secrets.token_urlsafe(48)
        db.add(
            PasswordRecoveryToken(
                user_id=user.id,
                token_hash=AuthService.token_hash(raw_token),
                expires_at=datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
            )
        )
        db.commit()
        return raw_token

    @staticmethod
    def confirm_password_recovery(db: Session, token: str, new_password: str) -> None:
        recovery = db.query(PasswordRecoveryToken).filter(
            PasswordRecoveryToken.token_hash == AuthService.token_hash(token),
        ).first()
        if not recovery or recovery.used_at or recovery.expires_at <= datetime.utcnow():
            raise ValidationError("Invalid or expired recovery token")
        user = db.query(User).filter(User.id == recovery.user_id).first()
        if not user:
            raise ValidationError("Invalid or expired recovery token")
        credential = AuthService._ensure_credential(db, user)
        credential.password_hash = hash_password(new_password)
        credential.credential_version += 1
        credential.password_changed_at = datetime.utcnow()
        credential.failed_attempts = 0
        credential.locked_until = None
        user.password_hash = credential.password_hash
        recovery.used_at = datetime.utcnow()
        db.query(RefreshSession).filter(
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
        ).update({"revoked_at": datetime.utcnow()})
        db.commit()
