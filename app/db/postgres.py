"""
PostgreSQL database connection and session management.
"""

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import NullPool, QueuePool
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# === DECLARATIVE BASE FOR ALL MODELS ===
Base = declarative_base()

# === DATABASE ENGINE CONFIGURATION ===
# Using QueuePool for connection pooling in production
# NullPool for serverless/edge environments (disable with: poolclass=NullPool)

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_size=5,  # Number of connections to maintain in pool
    max_overflow=10,  # Additional connections beyond pool_size
    pool_timeout=30,
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Test connections before using them
    connect_args={
        "connect_timeout": settings.DATABASE_TIMEOUT,
        "application_name": f"{settings.APP_NAME}/{settings.APP_VERSION}",
    },
)

# === SESSION FACTORY ===
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
    autoflush=False,
)


# === EVENT LISTENERS ===

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set connection pragmas."""
    if "postgresql" in settings.DATABASE_URL:
        # PostgreSQL-specific settings
        cursor = dbapi_connection.cursor()
        cursor.execute("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL READ COMMITTED")
        cursor.close()


@event.listens_for(Engine, "engine_disposed")
def receive_engine_disposed(engine):
    """Log when engine is disposed."""
    logger.info("Database engine disposed")


@event.listens_for(Engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log connection established."""
    logger.debug("Database connection established")


# === DATABASE SESSION DEPENDENCY ===

def get_db() -> Session:
    """
    FastAPI dependency to get database session.
    Use in route functions as: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# === DATABASE INITIALIZATION & MIGRATION ===

def init_db():
    """
    Initialize database by creating all tables.
    Called on app startup.
    """
    try:
        if not settings.AUTO_CREATE_TABLES:
            logger.info("Skipping metadata.create_all; database schema is managed by Alembic")
            return
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize database: {str(e)}")
        logger.warning("App will continue, but database operations may fail until connection is restored")
        # Don't raise - allow app to start in degraded mode for development


def drop_all_tables():
    """
    Drop all tables. Use with caution - for testing/reset only.
    """
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop tables: {str(e)}")
        raise


def get_db_session() -> Session:
    """
    Alternative method to get database session outside of FastAPI context.
    For background tasks, scripts, etc.
    """
    return SessionLocal()


def close_db_session(session: Session):
    """Close a database session."""
    if session:
        session.close()
