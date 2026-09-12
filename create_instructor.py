#!/usr/bin/env python
"""
Bootstrap script to create an instructor/admin user directly.
Usage: python create_instructor.py
"""

from app.db.postgres import SessionLocal, Base, engine, init_db
from app.models.user import User, UserRole
from app.models.course import Course  # Import all models to avoid mapper errors
from app.models.enrollment import Enrollment
from app.models.progress import Streak, Badge, BadgeAward, Leaderboard
from app.security import hash_password
from uuid import uuid4
from sqlalchemy.orm import Session
import sys

def create_instructor(db: Session, email: str, password: str, first_name: str, last_name: str, role: str = "instructor"):
    """Create an instructor user."""
    
    # Check if user exists
    existing = db.query(User).filter(User.email == email.lower()).first()
    if existing:
        print(f"❌ User {email} already exists")
        return None
    
    # Create user
    try:
        user = User(
            id=uuid4(),
            email=email,  # Don't call .lower() again - it's already done below
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=UserRole.INSTRUCTOR if role.lower() == "instructor" else UserRole.ADMIN,
            is_active=True,
            is_email_verified=True,
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ {role.title()} created successfully!")
        print(f"📧 Email: {user.email}")
        print(f"🆔 ID: {user.id}")
        print(f"👤 Name: {user.first_name} {user.last_name}")
        print(f"⭐ Role: {user.role.value}")
        
        return user
        
    except Exception as e:
        print(f"❌ Error creating {role}: {e}")
        db.rollback()
        return None

if __name__ == "__main__":
    # Initialize database
    print("🔧 Initializing database...")
    init_db()
    
    db = SessionLocal()
    
    try:
        # Create instructor
        print("\n📝 Creating instructor account...\n")
        instructor = create_instructor(
            db=db,
            email="admin@kukekodes.com",
            password="AdminPass123",
            first_name="Victor",
            last_name="Admin",
            role="admin"
        )
        
        if instructor:
            print("\n✅ You can now use this account to create courses!")
            print("\n📝 Test Login:")
            print(f"  Email: instructor@example.com")
            print(f"  Password: InstructorPass123")
            print(f"\n🚀 Create a course with:")
            print(f"  curl -X POST http://localhost:8000/api/v1/courses \\")
            print(f"    -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \\")
            print(f"    -H 'Content-Type: application/json' \\")
            print(f"    -d '{{\"title\": \"My Course\", \"description\": \"...\", ...}}'")
        
    finally:
        db.close()
