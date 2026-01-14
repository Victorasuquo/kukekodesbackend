"""
Configuration management for Kukekodes backend.
Loads environment variables and provides app settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # === APP SETTINGS ===
    APP_NAME: str = "Kukekodes Learning Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # === DATABASE ===
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/kukekodes"
    )
    MONGODB_URI: str = os.getenv(
        "MONGODB_URI",
        "mongodb://localhost:27017"
    )
    MONGODB_DB_NAME: str = "kukekodes_analytics"
    
    # === REDIS (Optional, for caching/sessions) ===
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    # === JWT & SECURITY ===
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # === CORS ===
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]
    
    # === EXTERNAL APIs ===
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL: str = os.getenv("SENDGRID_FROM_EMAIL", "noreply@kukekodes.com")
    
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # === EMAIL SETTINGS ===
    EMAIL_VERIFICATION_REQUIRED: bool = False
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    
    # === LOGGING ===
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "json"  # or "standard"
    
    # === RATE LIMITING ===
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100  # Per minute per user
    RATE_LIMIT_AUTH_REQUESTS: int = 5  # Per minute per IP for auth
    
    # === PAGINATION ===
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # === COURSE DEFAULTS ===
    MAX_VIDEO_DURATION_HOURS: int = 4  # Max 4 hours per lesson
    MIN_COURSE_MODULES: int = 1
    MIN_MODULE_LESSONS: int = 1
    
    # === TIMEOUTS ===
    EXTERNAL_API_TIMEOUT: int = 30
    DATABASE_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings for use throughout the app
settings = get_settings()