"""
Configuration management for Kukekodes backend.
Loads environment variables and provides app settings.
"""

from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # === APP SETTINGS ===
    APP_NAME: str = "Kukekodes Learning Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # === DATABASE ===
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/kukekodes"
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "kukekodes_analytics"
    AUTO_CREATE_TABLES: bool = True
    
    # === REDIS (Optional, for caching/sessions) ===
    REDIS_URL: Optional[str] = None
    
    # === JWT & SECURITY ===
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_COOKIE_NAME: str = "kukekodes_refresh"
    REFRESH_COOKIE_SECURE: bool = False
    REFRESH_COOKIE_SAMESITE: str = "lax"
    
    # === CORS ===
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]
    TRUSTED_HOSTS: list[str] = ["localhost", "127.0.0.1", "testserver"]
    
    # === EXTERNAL APIs ===
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@kukekodes.com"
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "KukeKodes <noreply@kukekodes.com>"
    RESEND_WEBHOOK_SECRET: str = ""
    
    YOUTUBE_API_KEY: str = ""
    
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    
    GEMINI_API_KEY: str = ""
    
    # === EMAIL SETTINGS ===
    EMAIL_VERIFICATION_REQUIRED: bool = False
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    
    # === LOGGING ===
    LOG_LEVEL: str = "INFO"
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
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow",
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Fail fast instead of launching production with development defaults."""
        if not self.is_production:
            return self

        errors = []
        if len(self.JWT_SECRET) < 32 or self.JWT_SECRET == "your-secret-key-change-in-production":
            errors.append("JWT_SECRET must be a non-default secret of at least 32 characters")
        if "*" in self.CORS_ORIGINS:
            errors.append("CORS_ORIGINS cannot contain '*' in production")
        if "*" in self.TRUSTED_HOSTS:
            errors.append("TRUSTED_HOSTS cannot contain '*' in production")
        if "localhost" in self.DATABASE_URL or "user:password" in self.DATABASE_URL:
            errors.append("DATABASE_URL must point to the production PostgreSQL database")
        if "localhost" in self.MONGODB_URI:
            errors.append("MONGODB_URI must point to the production MongoDB deployment")
        if self.AUTO_CREATE_TABLES:
            errors.append("AUTO_CREATE_TABLES must be false in production; use Alembic migrations")
        if not self.REFRESH_COOKIE_SECURE:
            errors.append("REFRESH_COOKIE_SECURE must be true in production")
        if not self.REDIS_URL:
            errors.append("REDIS_URL is required in production for rate limits and background jobs")
        if not self.RESEND_API_KEY:
            errors.append("RESEND_API_KEY is required in production")
        if not self.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required in production")
        if errors:
            raise ValueError("Invalid production configuration: " + "; ".join(errors))
        return self


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings for use throughout the app
settings = get_settings()
