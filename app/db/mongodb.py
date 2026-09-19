"""
MongoDB connection and database management.
Used for analytics, activity logs, and unstructured data.
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from contextlib import contextmanager
import logging
from typing import Optional, Dict, Any, List

from app.config import settings

logger = logging.getLogger(__name__)

# === GLOBAL MONGODB CLIENT ===
_mongo_client: Optional[MongoClient] = None
_mongo_db: Optional[Database] = None


def connect_mongodb():
    """Establish MongoDB connection."""
    global _mongo_client, _mongo_db
    
    try:
        logger.info("Connecting to MongoDB...")
        _mongo_client = MongoClient(
            settings.MONGODB_URI,
            connectTimeoutMS=settings.DATABASE_TIMEOUT * 1000,
            serverSelectionTimeoutMS=5000,
            retryWrites=True,
            w="majority",
        )
        
        # Test connection
        _mongo_client.admin.command("ping")
        
        # Get database instance
        _mongo_db = _mongo_client[settings.MONGODB_DB_NAME]
        
        logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")
        
        # Create indexes
        create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise


def disconnect_mongodb():
    """Close MongoDB connection."""
    global _mongo_client
    
    if _mongo_client:
        try:
            logger.info("Disconnecting from MongoDB...")
            _mongo_client.close()
            _mongo_client = None
            logger.info("Disconnected from MongoDB")
        except Exception as e:
            logger.error(f"Error disconnecting from MongoDB: {str(e)}")


def get_mongodb() -> Database:
    """Get MongoDB database instance."""
    if _mongo_db is None:
        raise RuntimeError("MongoDB not connected. Call connect_mongodb() first.")
    return _mongo_db


def get_collection(collection_name: str) -> Collection:
    """Get MongoDB collection."""
    db = get_mongodb()
    return db[collection_name]


@contextmanager
def get_mongo_session():
    """Context manager for MongoDB operations."""
    try:
        yield get_mongodb()
    except Exception as e:
        logger.error(f"MongoDB operation error: {str(e)}")
        raise


def create_indexes():
    """Create MongoDB indexes for better query performance."""
    try:
        db = get_mongodb()
        
        # === ACTIVITIES COLLECTION ===
        db.activities.create_index([("user_id", ASCENDING)])
        db.activities.create_index([("timestamp", DESCENDING)])
        db.activities.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        logger.info("Indexes created for 'activities' collection")
        
        # === AI INTERACTIONS COLLECTION ===
        db.ai_interactions.create_index([("user_id", ASCENDING)])
        db.ai_interactions.create_index([("lesson_id", ASCENDING)])
        db.ai_interactions.create_index([("timestamp", DESCENDING)])
        logger.info("Indexes created for 'ai_interactions' collection")
        
        # === FORUM THREADS COLLECTION ===
        db.forum_threads.create_index([("course_id", ASCENDING)])
        db.forum_threads.create_index([("organization_id", ASCENDING)])
        db.forum_threads.create_index([("user_id", ASCENDING)])
        db.forum_threads.create_index([("created_at", DESCENDING)])
        db.forum_threads.create_index([("moderation_status", ASCENDING)])
        logger.info("Indexes created for 'forum_threads' collection")
        
        # === FORUM REPLIES COLLECTION ===
        db.forum_replies.create_index([("thread_id", ASCENDING)])
        db.forum_replies.create_index([("user_id", ASCENDING)])
        db.forum_replies.create_index([("created_at", DESCENDING)])
        db.forum_replies.create_index([("moderation_status", ASCENDING)])
        db.accountability_messages.create_index([("cluster_id", ASCENDING), ("created_at", DESCENDING)])
        db.accountability_messages.create_index([("created_at", DESCENDING)], expireAfterSeconds=31536000)
        db.accountability_read_cursors.create_index([("cluster_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
        logger.info("Indexes created for 'forum_replies' collection")
        
        # === ANALYTICS COLLECTION ===
        db.analytics.create_index([("user_id", ASCENDING)])
        db.analytics.create_index([("course_id", ASCENDING)])
        logger.info("Indexes created for 'analytics' collection")
        
    except Exception as e:
        logger.warning(f"Error creating MongoDB indexes: {str(e)}")


# === MONGODB COLLECTION OPERATIONS ===

def insert_activity(
    user_id: str,
    action: str,
    entity_id: str,
    entity_type: str = "unknown",
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Log user activity to MongoDB.
    
    Args:
        user_id: User's ID
        action: Action name (e.g., "viewed_lesson", "started_course")
        entity_id: Related entity ID
        entity_type: Type of entity
        metadata: Additional context
    
    Returns:
        Inserted document ID
    """
    from datetime import datetime
    
    doc = {
        "user_id": user_id,
        "action": action,
        "entity_id": entity_id,
        "entity_type": entity_type,
        "timestamp": datetime.utcnow(),
        "metadata": metadata or {},
    }
    
    collection = get_collection("activities")
    result = collection.insert_one(doc)
    return str(result.inserted_id)


def insert_ai_interaction(
    user_id: str,
    lesson_id: str,
    question: str,
    response: str,
    agent_mode: str = "tutor",
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Log AI coach interaction."""
    from datetime import datetime
    
    doc = {
        "user_id": user_id,
        "lesson_id": lesson_id,
        "question": question,
        "response": response,
        "agent_mode": agent_mode,
        "timestamp": datetime.utcnow(),
        "metadata": metadata or {},
    }
    
    collection = get_collection("ai_interactions")
    result = collection.insert_one(doc)
    return str(result.inserted_id)


def get_user_activities(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent user activities."""
    collection = get_collection("activities")
    return list(
        collection.find({"user_id": user_id})
        .sort("timestamp", DESCENDING)
        .limit(limit)
    )


def get_user_analytics(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user analytics data."""
    collection = get_collection("analytics")
    return collection.find_one({"user_id": user_id})


def update_user_analytics(
    user_id: str,
    analytics_data: Dict[str, Any],
) -> None:
    """Update user analytics."""
    collection = get_collection("analytics")
    collection.update_one(
        {"user_id": user_id},
        {"$set": analytics_data},
        upsert=True,
    )
