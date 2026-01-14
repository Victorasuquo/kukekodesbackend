"""
Security utilities: JWT token generation/validation, password hashing, CORS setup.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# === PASSWORD HASHING ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


# === JWT TOKEN MANAGEMENT ===
class TokenData:
    """Token payload data."""
    
    def __init__(
        self,
        user_id: str,
        email: str,
        role: str,
        username: Optional[str] = None,
    ):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.username = username


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
    username: Optional[str] = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User's unique identifier
        email: User's email
        role: User's role (admin, instructor, student)
        expires_delta: Optional custom expiration time
        username: Optional username
    
    Returns:
        Encoded JWT token
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.now(timezone.utc) + expires_delta
    
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "username": username,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    
    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    
    return encoded_jwt


def create_refresh_token(user_id: str, email: str) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        user_id: User's unique identifier
        email: User's email
    
    Returns:
        Encoded JWT refresh token
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    
    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        logger.error(f"Token decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_token(token: str) -> Dict[str, Any]:
    """Verify and return token payload."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


# === BEARER TOKEN SECURITY SCHEME ===
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Dependency to extract and validate current user from Bearer token.
    
    Args:
        credentials: HTTP Bearer token
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid
    """
    return await verify_token(credentials.credentials)


async def get_current_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Dependency to ensure current user is an admin.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Current user data if admin
    
    Raises:
        HTTPException: If user is not an admin
    """
    role = current_user.get("role")
    if role not in ["admin", "instructor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins/instructors can access this resource",
        )
    return current_user


async def get_current_student(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Dependency to ensure current user is a student (or higher privilege).
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Current user data
    
    Raises:
        HTTPException: If user is not authenticated
    """
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """
    Dependency for optional authentication.
    Returns None if no token, or decoded token if provided.
    """
    if credentials is None:
        return None
    try:
        return await verify_token(credentials.credentials)
    except HTTPException:
        return None


# === PASSWORD RESET TOKEN ===
def create_password_reset_token(email: str) -> str:
    """Create a password reset token."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
    )
    
    payload = {
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "password_reset",
    }
    
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token and return email.
    
    Returns:
        Email if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        email = payload.get("email")
        token_type = payload.get("type")
        
        if token_type != "password_reset":
            return None
        
        return email
    except JWTError:
        return None


# === CSRF & SECURITY HEADERS ===
CORS_CONFIG = {
    "allow_origins": settings.CORS_ORIGINS,
    "allow_credentials": settings.CORS_CREDENTIALS,
    "allow_methods": settings.CORS_METHODS,
    "allow_headers": settings.CORS_HEADERS,
}

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}