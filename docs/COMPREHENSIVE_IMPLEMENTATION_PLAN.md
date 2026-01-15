# Kukekodes Learning Management System - Comprehensive Implementation Plan

**Date:** January 15, 2026  
**Version:** 2.0 - Complete Architecture & Scalable Design  
**Status:** Ready for Implementation

---

## Executive Summary

Kukekodes is a **global learning platform** designed to teach coding and AI skills through an intuitive, gamified, and AI-powered learning experience. This document outlines a complete, production-ready, scalable architecture using:

- **FastAPI** - High-performance async Python framework
- **PostgreSQL** (Supabase) - Relational data (courses, users, progress tracking)
- **MongoDB** - Activity logs, analytics, dynamic content
- **SendGrid** - Email notifications & confirmations
- **Cloudinary** - Media uploads (profile pictures, course covers)
- **YouTube API** - Video integration (we don't host videos directly)
- **Google Gemini API** - AI Coach for intelligent tutoring

---

## PART 1: Project Understanding & Core Concepts

### What is Kukekodes?

A **Learning Management System (LMS)** with the following core features:

#### 🎯 Core Learning Flow

```
ADMIN/INSTRUCTOR:
1. Create Course (Title, Description, Tags)
   └─ Automatically saved as DRAFT
   └─ Metadata stored (tags, skill level, category)
   
2. Create Module (Unit) under Course
   └─ Title: "Module 1: Introduction to Machine Learning"
   └─ Description with learning objectives
   └─ Set order/sequence
   
3. Add Lessons (Videos) under Module
   └─ Add YouTube video URL
   └─ System extracts video ID, duration, thumbnail
   └─ Add lesson description, resources
   └─ Set order within module
   
4. Preview & Publish Course
   └─ Minimum requirements: ≥1 module, ≥1 lesson per module
   └─ Set course status: PUBLISHED
   └─ Send notification to enrolled users

STUDENT EXPERIENCE:
1. Browse & Enroll in Course
2. Start Lesson 1 → Watch Video
3. Lesson marked complete → Next lesson becomes available
4. Completion tracker shows progress (✅ Green marks)
5. Earn badges, streaks, XP for motivation
6. Access AI Coach for help anytime
7. Receive email notifications on milestones
```

#### 📊 Key Tracking Features

| Feature | Description | Database |
|---------|-------------|----------|
| **Progress Tracker** | Shows lesson/module/course completion status | PostgreSQL `user_progress` |
| **Green Marks** | Completed lessons marked with ✅ emoji | PostgreSQL `user_progress.is_completed` |
| **Streaks** | Consecutive days of learning | PostgreSQL `streaks` |
| **Badges** | Achievement system (First Lesson, 7-Day Streak, etc.) | PostgreSQL `badges`, `user_badges` |
| **XP Points** | Experience points for gamification | PostgreSQL `enrollments` (extended) |
| **Time Tracking** | Minutes spent per lesson | PostgreSQL `user_progress.time_spent_minutes` |
| **Quiz Scores** | Assessment tracking per lesson | PostgreSQL `user_progress.quiz_score` |
| **Email Notifications** | Milestones, completions, reminders | SendGrid API |

---

## PART 2: Database Architecture

### PostgreSQL Schema (Relational Data)

#### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    username VARCHAR(100) UNIQUE,
    bio TEXT,
    profile_picture_url VARCHAR(500),  -- Cloudinary URL
    country VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferred_language VARCHAR(10) DEFAULT 'en',
    role ENUM('student', 'instructor', 'admin') DEFAULT 'student',
    is_active BOOLEAN DEFAULT TRUE,
    is_email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    
    INDEX idx_user_email_active (email, is_active),
    INDEX idx_user_role (role),
    INDEX idx_user_created_at (created_at)
);
```

#### Courses Table
```sql
CREATE TABLE courses (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    slug VARCHAR(255) UNIQUE,
    tags VARCHAR(50)[],  -- ["Python", "Beginner", "AI"]
    skill_level ENUM('beginner', 'intermediate', 'advanced'),
    category VARCHAR(100),
    instructor_id UUID NOT NULL REFERENCES users(id),
    cover_image_url VARCHAR(500),  -- Cloudinary URL
    thumbnail_url VARCHAR(500),
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
    is_free BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    total_enrollments INT DEFAULT 0,
    average_rating VARCHAR(5),
    total_reviews INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    
    INDEX idx_course_instructor_status (instructor_id, status),
    INDEX idx_course_status_created (status, created_at)
);
```

#### Modules Table
```sql
CREATE TABLE modules (
    id UUID PRIMARY KEY,
    course_id UUID NOT NULL REFERENCES courses(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    order INT NOT NULL,  -- Sequence within course
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_module_course_order (course_id, order)
);
```

#### Lessons Table
```sql
CREATE TABLE lessons (
    id UUID PRIMARY KEY,
    module_id UUID NOT NULL REFERENCES modules(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    youtube_url VARCHAR(500),  -- Full YouTube URL
    youtube_video_id VARCHAR(50),  -- Extracted video ID
    duration_minutes INT,  -- Auto-fetched from YouTube
    thumbnail_url VARCHAR(500),  -- YouTube thumbnail
    transcript TEXT,  -- Optional
    resources JSON,  -- {"links": [...], "files": [...]}
    order INT NOT NULL,  -- Sequence within module
    status ENUM('draft', 'published') DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_lesson_module_order (module_id, order),
    INDEX idx_lesson_youtube_id (youtube_video_id)
);
```

#### Enrollments Table
```sql
CREATE TABLE enrollments (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    course_id UUID NOT NULL REFERENCES courses(id),
    completion_percentage FLOAT DEFAULT 0.0,
    is_completed BOOLEAN DEFAULT FALSE,
    current_module_id UUID REFERENCES modules(id),
    current_lesson_id UUID REFERENCES lessons(id),
    total_time_spent_minutes INT DEFAULT 0,
    enrolled_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    last_accessed_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (user_id, course_id),
    INDEX idx_enrollment_user_completed (user_id, is_completed),
    INDEX idx_enrollment_course_enrolled (course_id, enrolled_at)
);
```

#### User Progress Table
```sql
CREATE TABLE user_progress (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    lesson_id UUID NOT NULL REFERENCES lessons(id),
    module_id UUID NOT NULL REFERENCES modules(id),
    course_id UUID NOT NULL REFERENCES courses(id),
    is_completed BOOLEAN DEFAULT FALSE,
    time_spent_minutes INT DEFAULT 0,
    quiz_score FLOAT,  -- 0-100
    quiz_attempts INT DEFAULT 0,
    started_at TIMESTAMP DEFAULT NOW(),
    watched_at TIMESTAMP,  -- When first watched
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (user_id, lesson_id),
    INDEX idx_progress_user_course_completed (user_id, course_id, is_completed),
    INDEX idx_progress_lesson_completed (lesson_id, is_completed)
);
```

#### Streaks Table
```sql
CREATE TABLE streaks (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    current_streak INT DEFAULT 0,
    longest_streak INT DEFAULT 0,
    last_activity_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (user_id),
    INDEX idx_streak_user (user_id)
);
```

#### Badges Table
```sql
CREATE TABLE badges (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon_url VARCHAR(500),  -- Cloudinary URL
    badge_type ENUM('achievement', 'milestone', 'streak') DEFAULT 'achievement',
    requirement_type VARCHAR(50),  -- 'lesson_complete', '7_day_streak', etc.
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_badge_type (badge_type)
);

CREATE TABLE user_badges (
    user_id UUID NOT NULL REFERENCES users(id),
    badge_id UUID NOT NULL REFERENCES badges(id),
    earned_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (user_id, badge_id)
);
```

### MongoDB Collections (Unstructured Data)

#### Activity Logs
```javascript
db.activity_logs.insertOne({
    _id: ObjectId(),
    user_id: "uuid",
    action: "lesson_completed",
    resource_type: "lesson",
    resource_id: "uuid",
    metadata: {
        course_id: "uuid",
        module_id: "uuid",
        time_spent: 15,
        quiz_score: 85.5
    },
    timestamp: ISODate()
});
```

#### Analytics
```javascript
db.analytics.insertOne({
    _id: ObjectId(),
    user_id: "uuid",
    metric_type: "course_progress",
    data: {
        course_id: "uuid",
        progress_percentage: 45.5,
        lessons_completed: 5,
        total_lessons: 11,
        time_spent_hours: 3.5
    },
    timestamp: ISODate()
});
```

---

## PART 3: API Architecture & Endpoints

### Authentication Endpoints

#### POST `/api/v1/auth/register`
**Create a new user account**

**Request:**
```json
{
    "email": "student@example.com",
    "password": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe",
    "country": "USA"
}
```

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "student@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student",
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "created_at": "2026-01-15T10:30:00Z"
}
```

**Security Measures:**
- Password hashed with bcrypt
- Email validation
- Account activation email sent
- Rate limiting: 5 attempts per minute per IP
- Duplicate email checking

---

#### POST `/api/v1/auth/login`
**Authenticate user and get tokens**

**Request:**
```json
{
    "email": "student@example.com",
    "password": "SecurePassword123!"
}
```

**Response:**
```json
{
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "expires_in": 900,
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "student@example.com",
        "role": "student"
    }
}
```

**Security Measures:**
- Verify password against hash
- Generate JWT access token (15 minutes)
- Generate refresh token (7 days)
- Log login activity to MongoDB
- Update last_login_at timestamp

---

#### POST `/api/v1/auth/refresh-token`
**Get new access token using refresh token**

**Request:**
```json
{
    "refresh_token": "eyJhbGc..."
}
```

**Response:**
```json
{
    "access_token": "eyJhbGc...",
    "expires_in": 900
}
```

---

### Course Management Endpoints (Admin/Instructor)

#### POST `/api/v1/courses`
**Create a new course**

**Authentication:** Required (Admin/Instructor only)

**Request:**
```json
{
    "title": "Machine Learning Fundamentals",
    "description": "Learn the basics of ML with Python",
    "tags": ["Python", "Machine Learning", "AI"],
    "skill_level": "beginner",
    "category": "Data Science",
    "is_free": true
}
```

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Machine Learning Fundamentals",
    "description": "Learn the basics of ML with Python",
    "tags": ["Python", "Machine Learning", "AI"],
    "skill_level": "beginner",
    "category": "Data Science",
    "status": "draft",
    "instructor_id": "550e8400-e29b-41d4-a716-446655440000",
    "is_free": true,
    "total_enrollments": 0,
    "created_at": "2026-01-15T10:30:00Z"
}
```

**Business Logic:**
- Course created in DRAFT status
- Metadata automatically validated
- Course slug auto-generated from title
- Cloudinary URLs set to null (can be updated later)
- Timestamps recorded

---

#### PUT `/api/v1/courses/{course_id}`
**Update course details**

**Authentication:** Required (Course Instructor only)

**Request:**
```json
{
    "title": "Machine Learning Fundamentals (Updated)",
    "description": "Advanced ML with Python and TensorFlow",
    "tags": ["Python", "TensorFlow", "Deep Learning"],
    "skill_level": "intermediate",
    "category": "Data Science"
}
```

**Response:** Updated course object

**Business Logic:**
- Only draft courses can be modified
- Published courses can only update certain fields
- Validation on tags, skill level, category
- Update timestamp recorded

---

#### POST `/api/v1/courses/{course_id}/modules`
**Add a module (unit) to course**

**Authentication:** Required (Course Instructor only)

**Request:**
```json
{
    "title": "Module 1: Introduction to ML",
    "description": "Understand what machine learning is and its applications",
    "order": 1
}
```

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "course_id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Module 1: Introduction to ML",
    "description": "Understand what machine learning is and its applications",
    "order": 1,
    "lessons": [],
    "created_at": "2026-01-15T10:35:00Z"
}
```

**Business Logic:**
- Module order must be unique within course
- Minimum 1 module required to publish course
- Update course.required_modules_count
- Cascading delete if course deleted

---

#### POST `/api/v1/courses/{course_id}/modules/{module_id}/lessons`
**Add a lesson (video) to module**

**Authentication:** Required (Course Instructor only)

**Request:**
```json
{
    "title": "What is Machine Learning?",
    "description": "Introduction to ML concepts",
    "youtube_url": "https://www.youtube.com/watch?v=HcqpanDMVVE",
    "order": 1
}
```

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "module_id": "550e8400-e29b-41d4-a716-446655440002",
    "title": "What is Machine Learning?",
    "description": "Introduction to ML concepts",
    "youtube_url": "https://www.youtube.com/watch?v=HcqpanDMVVE",
    "youtube_video_id": "HcqpanDMVVE",
    "duration_minutes": 12,
    "thumbnail_url": "https://i.ytimg.com/vi/HcqpanDMVVE/maxresdefault.jpg",
    "order": 1,
    "status": "draft",
    "created_at": "2026-01-15T10:40:00Z"
}
```

**Business Logic:**
- Call YouTube API to extract: video ID, duration, thumbnail
- Lesson created in DRAFT status
- Minimum 1 lesson per module required to publish
- Update course.required_lessons_count
- Store metadata extracted from YouTube

---

#### PUT `/api/v1/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}`
**Update lesson**

**Request:**
```json
{
    "title": "Updated Lesson Title",
    "description": "Updated description",
    "resources": {
        "links": ["https://example.com/resource1"],
        "files": ["https://example.com/notes.pdf"]
    }
}
```

**Business Logic:**
- Cannot change YouTube URL for published lessons
- Can update description, resources, metadata
- Only draft lessons can be deleted

---

#### POST `/api/v1/courses/{course_id}/publish`
**Publish a course**

**Authentication:** Required (Course Instructor only)

**Request:**
```json
{
    "publish": true
}
```

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "status": "published",
    "published_at": "2026-01-15T11:00:00Z"
}
```

**Validation Checklist:**
- ✅ Course has title & description
- ✅ At least 1 module
- ✅ Each module has at least 1 lesson
- ✅ All lessons have YouTube URLs

**Business Logic:**
- Course status changed to PUBLISHED
- published_at timestamp set
- All lessons automatically PUBLISHED
- Send notifications to enrolled users
- Log action to MongoDB activity_logs

---

#### POST `/api/v1/courses/{course_id}/preview`
**Preview course as student would see**

**Response:** Full course structure with all modules and lessons

---

### Student Course Endpoints

#### GET `/api/v1/courses`
**List all published courses with filtering**

**Query Parameters:**
- `skill_level=beginner|intermediate|advanced`
- `category=Data Science|Web Development|AI`
- `tags=Python,AI`
- `page=1`
- `limit=20`
- `search=machine learning`

**Response:**
```json
{
    "data": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "title": "Machine Learning Fundamentals",
            "description": "...",
            "skill_level": "beginner",
            "category": "Data Science",
            "instructor_id": "...",
            "cover_image_url": "...",
            "is_free": true,
            "total_enrollments": 45,
            "status": "published",
            "created_at": "..."
        }
    ],
    "meta": {
        "total": 150,
        "page": 1,
        "limit": 20,
        "total_pages": 8
    }
}
```

**Business Logic:**
- Only return PUBLISHED courses
- Pagination with default 20 per page
- Filter by skill level, category, tags
- Sort by newest, popular, trending
- Cache results in Redis for 1 hour

---

#### GET `/api/v1/courses/{course_id}`
**Get course details (published courses)**

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Machine Learning Fundamentals",
    "description": "...",
    "skill_level": "beginner",
    "category": "Data Science",
    "instructor_id": "...",
    "instructor": {
        "id": "...",
        "first_name": "John",
        "last_name": "Doe",
        "profile_picture_url": "..."
    },
    "cover_image_url": "...",
    "total_enrollments": 45,
    "average_rating": "4.5",
    "total_reviews": 12,
    "modules": [
        {
            "id": "...",
            "title": "Module 1: Introduction",
            "description": "...",
            "order": 1,
            "lessons": [
                {
                    "id": "...",
                    "title": "What is ML?",
                    "description": "...",
                    "duration_minutes": 12,
                    "order": 1,
                    "thumbnail_url": "..."
                }
            ]
        }
    ]
}
```

---

### Enrollment Endpoints

#### POST `/api/v1/enrollments/{course_id}`
**Enroll student in course**

**Authentication:** Required (Student)

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "course_id": "550e8400-e29b-41d4-a716-446655440001",
    "enrolled_at": "2026-01-15T11:30:00Z",
    "completion_percentage": 0.0,
    "is_completed": false,
    "current_lesson_id": null
}
```

**Business Logic:**
- Create enrollment record
- Initialize user_progress records for all lessons
- Check for duplicate enrollment
- Send welcome email to student
- Log enrollment to MongoDB activity_logs

---

#### GET `/api/v1/enrollments`
**Get user's enrolled courses**

**Authentication:** Required

**Response:**
```json
{
    "data": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440004",
            "course": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "title": "Machine Learning Fundamentals",
                "cover_image_url": "..."
            },
            "completion_percentage": 35.5,
            "is_completed": false,
            "enrolled_at": "2026-01-15T11:30:00Z",
            "last_accessed_at": "2026-01-15T12:00:00Z"
        }
    ]
}
```

---

### Progress Tracking Endpoints

#### POST `/api/v1/progress/mark-lesson-complete/{lesson_id}`
**Mark a lesson as complete**

**Authentication:** Required (Student)

**Request:**
```json
{
    "time_spent_minutes": 15,
    "quiz_score": 85.5
}
```

**Response:**
```json
{
    "success": true,
    "lesson_status": "completed",
    "lesson_marked_green": true,
    "module_progress": {
        "completed": 3,
        "total": 5,
        "percentage": 60.0
    },
    "course_progress": {
        "percentage": 60,
        "completed_lessons": 6,
        "total_lessons": 10
    },
    "next_lesson": {
        "id": "550e8400-e29b-41d4-a716-446655440005",
        "title": "Supervised Learning",
        "module_id": "550e8400-e29b-41d4-a716-446655440002"
    },
    "streak": {
        "current": 7,
        "longest": 14,
        "incremented": true
    },
    "badges_earned": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440006",
            "name": "First Lesson Complete",
            "icon_url": "..."
        }
    ]
}
```

**Automatic Actions:**
1. ✅ Mark user_progress.is_completed = true
2. ✅ Record time_spent_minutes
3. ✅ Record quiz_score
4. ✅ Calculate module progress percentage
5. ✅ Calculate course progress percentage
6. ✅ Increment streak (if not already completed today)
7. ✅ Check and award badges
8. ✅ Find next lesson
9. ✅ Send completion email
10. ✅ Log to MongoDB activity_logs & analytics

**Business Logic:**
- Validate lesson belongs to enrolled course
- Prevent double completion marking
- Recalculate enrollment.completion_percentage
- Check badge conditions (first lesson, streaks, etc.)
- Update last_accessed_at timestamp

---

#### GET `/api/v1/progress/lesson/{lesson_id}`
**Get progress on a specific lesson**

**Response:**
```json
{
    "lesson_id": "550e8400-e29b-41d4-a716-446655440003",
    "is_completed": true,
    "time_spent_minutes": 15,
    "quiz_score": 85.5,
    "quiz_attempts": 1,
    "started_at": "2026-01-15T11:45:00Z",
    "watched_at": "2026-01-15T11:45:30Z",
    "completed_at": "2026-01-15T12:00:00Z",
    "status_emoji": "✅"
}
```

---

#### GET `/api/v1/progress/module/{module_id}`
**Get progress on entire module**

**Response:**
```json
{
    "module_id": "550e8400-e29b-41d4-a716-446655440002",
    "title": "Module 1: Introduction to ML",
    "completion_percentage": 60.0,
    "lessons_completed": 3,
    "lessons_total": 5,
    "lessons": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440003",
            "title": "What is ML?",
            "is_completed": true,
            "status_emoji": "✅",
            "order": 1
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440004",
            "title": "ML Applications",
            "is_completed": true,
            "status_emoji": "✅",
            "order": 2
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440005",
            "title": "Supervised Learning",
            "is_completed": false,
            "status_emoji": "🔲",
            "order": 3
        }
    ]
}
```

---

#### GET `/api/v1/progress/course/{course_id}`
**Get full course progress**

**Response:**
```json
{
    "course_id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Machine Learning Fundamentals",
    "completion_percentage": 45.5,
    "lessons_completed": 5,
    "lessons_total": 11,
    "modules": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "title": "Module 1: Introduction",
            "order": 1,
            "completion_percentage": 60.0,
            "lessons_completed": 3,
            "lessons_total": 5
        }
    ],
    "last_accessed_at": "2026-01-15T12:00:00Z",
    "enrolled_at": "2026-01-15T11:30:00Z"
}
```

---

### Gamification Endpoints

#### GET `/api/v1/users/me/streaks`
**Get user's learning streak**

**Response:**
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "current_streak": 7,
    "longest_streak": 14,
    "last_activity_date": "2026-01-15",
    "streak_message": "🔥 Keep it up! 7 days in a row!"
}
```

---

#### GET `/api/v1/users/me/badges`
**Get user's earned badges**

**Response:**
```json
{
    "data": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440006",
            "name": "First Lesson Complete",
            "description": "Completed your first lesson",
            "badge_type": "achievement",
            "icon_url": "...",
            "earned_at": "2026-01-15T12:00:00Z"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440007",
            "name": "7-Day Streak",
            "description": "Learned for 7 consecutive days",
            "badge_type": "streak",
            "icon_url": "...",
            "earned_at": "2026-01-15T08:00:00Z"
        }
    ]
}
```

---

#### GET `/api/v1/leaderboard`
**Get top learners (public leaderboard)**

**Query Parameters:**
- `period=week|month|all_time`
- `limit=10`

**Response:**
```json
{
    "data": [
        {
            "rank": 1,
            "user": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "john_doe",
                "profile_picture_url": "..."
            },
            "total_lessons_completed": 45,
            "current_streak": 14,
            "badges_count": 8,
            "total_learning_hours": 32.5
        }
    ]
}
```

---

### AI Coach Endpoints

#### POST `/api/v1/ai/chat`
**Chat with AI Coach**

**Authentication:** Required

**Request:**
```json
{
    "message": "How do I apply gradient descent to this problem?",
    "context": {
        "lesson_id": "550e8400-e29b-41d4-a716-446655440003",
        "course_id": "550e8400-e29b-41d4-a716-446655440001"
    },
    "mode": "tutor"  // or "debugger", "mentor"
}
```

**Response:**
```json
{
    "response": "Great question! Gradient descent is an optimization algorithm...",
    "suggestions": [
        "Review the previous lesson on derivatives",
        "Check out this external resource: https://..."
    ],
    "related_lessons": [
        {
            "id": "...",
            "title": "Calculus for ML"
        }
    ]
}
```

**Business Logic:**
- Call Google Gemini API with context
- Include course/lesson context in prompt
- Log conversation to MongoDB
- Provide personalized suggestions based on progress

---

### User Dashboard Endpoints

#### GET `/api/v1/users/me`
**Get current user profile**

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "student@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "username": "john_doe",
    "profile_picture_url": "...",
    "bio": "Passionate learner",
    "country": "USA",
    "timezone": "EST",
    "role": "student",
    "created_at": "2026-01-15T10:30:00Z",
    "stats": {
        "courses_enrolled": 3,
        "courses_completed": 1,
        "lessons_completed": 25,
        "total_learning_hours": 32.5,
        "badges_earned": 8,
        "current_streak": 7
    }
}
```

---

#### PUT `/api/v1/users/me`
**Update user profile**

**Request:**
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "username": "john_doe",
    "bio": "Updated bio",
    "timezone": "PST",
    "preferred_language": "es"
}
```

---

#### POST `/api/v1/users/me/profile-picture`
**Upload profile picture**

**Request:** Multipart form-data with image file

**Response:**
```json
{
    "profile_picture_url": "https://res.cloudinary.com/kukekodes/image/upload/..."
}
```

**Business Logic:**
- Call CloudinaryService.upload_profile_picture()
- Validate image format (JPG, PNG, WebP)
- Resize to 200x200px
- Update user.profile_picture_url

---

### Notification Endpoints

#### GET `/api/v1/notifications`
**Get user's notifications**

**Query Parameters:**
- `read=true|false`
- `limit=20`

**Response:**
```json
{
    "data": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440008",
            "type": "lesson_completed",
            "title": "Great job!",
            "message": "You completed 'What is ML?'",
            "read": false,
            "created_at": "2026-01-15T12:00:00Z"
        }
    ]
}
```

---

#### PUT `/api/v1/notifications/{notification_id}/read`
**Mark notification as read**

---

#### PUT `/api/v1/users/me/notification-preferences`
**Update notification preferences**

**Request:**
```json
{
    "email_notifications_enabled": true,
    "receive_weekly_summary": true,
    "receive_achievement_notifications": true
}
```

---

### Admin Analytics Endpoints

#### GET `/api/v1/admin/analytics/dashboard`
**Get analytics dashboard**

**Authentication:** Required (Admin only)

**Response:**
```json
{
    "summary": {
        "total_users": 1250,
        "total_courses": 25,
        "total_enrollments": 5432,
        "active_users_today": 345,
        "average_completion_rate": 68.5
    },
    "courses": [
        {
            "id": "...",
            "title": "Machine Learning Fundamentals",
            "enrollments": 234,
            "completion_rate": 72.3,
            "average_rating": 4.7
        }
    ],
    "user_metrics": {
        "new_users_today": 12,
        "active_users_past_7_days": 890,
        "retention_rate": 65.2
    }
}
```

---

## PART 4: Security Implementation

### Authentication & Authorization

```python
# JWT Token Structure
{
    "sub": "user_id",           # User's unique identifier
    "email": "user@example.com",
    "role": "student|instructor|admin",
    "username": "john_doe",
    "exp": 1705334400,          # Expiration time
    "iat": 1705330800,          # Issued at
    "type": "access"            # Token type
}
```

### Security Layers

#### Layer 1: Input Validation
- **Pydantic Models:** Strict validation on all requests
- **Email Format:** RFC 5322 compliance
- **Password Strength:** Min 8 chars, special chars, numbers
- **File Upload:** Size limits, type validation
- **SQL Injection Prevention:** SQLAlchemy ORM parameterized queries
- **XSS Prevention:** HTML escaping in responses

#### Layer 2: Authentication
- **JWT Tokens:** Symmetric HS256 algorithm
- **Access Tokens:** 15-minute expiration
- **Refresh Tokens:** 7-day expiration
- **Token Validation:** Signature, expiration, type verification
- **Password Hashing:** bcrypt with salt rounds=12

#### Layer 3: Authorization
- **Role-Based Access Control (RBAC):**
  - `ADMIN`: Full system access
  - `INSTRUCTOR`: Create/manage courses, view analytics
  - `STUDENT`: Enroll, complete lessons, access AI coach
- **Resource Ownership:** Users can only modify their own resources
- **Dependency Injectors:** FastAPI dependencies enforce authorization

#### Layer 4: API Security
- **CORS:** Restricted to frontend domains
- **HTTPS Only:** All production endpoints use HTTPS
- **Rate Limiting:**
  - Auth endpoints: 5 requests/minute per IP
  - API endpoints: 100 requests/minute per user
  - Sliding window algorithm
- **Request Logging:** All requests logged to MongoDB
- **Security Headers:**
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000`

#### Layer 5: Database Security
- **Connection Pooling:** SQLAlchemy pooling with 20 max connections
- **Prepared Statements:** All queries parameterized
- **Sensitive Data:** Passwords hashed, never logged
- **Audit Trail:** MongoDB activity_logs track all changes
- **Data Encryption:** Sensitive fields encrypted at rest (optional)

#### Layer 6: External Service Security
- **API Key Management:** Stored in .env, not in code
- **SendGrid:** API keys rotated quarterly
- **Cloudinary:** Upload tokens generated per request
- **YouTube API:** Quota monitoring and rate limiting
- **Gemini API:** Request validation and timeout handling

### .env Configuration (Template)
```bash
# === APP ===
ENVIRONMENT=production
DEBUG=False
APP_NAME="Kukekodes Learning Platform"
APP_VERSION="1.0.0"

# === DATABASE ===
DATABASE_URL=postgresql://user:password@db.supabase.co:5432/kukekodes
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net
MONGODB_DB_NAME=kukekodes_analytics

# === REDIS (Optional) ===
REDIS_URL=redis://localhost:6379

# === JWT & SECURITY ===
JWT_SECRET=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# === CORS ===
CORS_ORIGINS=["https://frontend.kukekodes.com", "https://app.kukekodes.com"]
CORS_CREDENTIALS=True
CORS_METHODS=["*"]
CORS_HEADERS=["*"]

# === SENDGRID ===
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@kukekodes.com

# === YOUTUBE ===
YOUTUBE_API_KEY=AIzaSyD...

# === CLOUDINARY ===
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=xxxxxxxxx
CLOUDINARY_API_SECRET=yyyyyyyyy

# === GOOGLE GEMINI ===
GEMINI_API_KEY=AIzaSyD...

# === EMAIL ===
EMAIL_VERIFICATION_REQUIRED=False
PASSWORD_RESET_EXPIRE_MINUTES=30

# === LOGGING ===
LOG_LEVEL=INFO
LOG_FORMAT=json

# === RATE LIMITING ===
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_AUTH_REQUESTS=5

# === PAGINATION ===
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100

# === COURSE ===
MAX_VIDEO_DURATION_HOURS=4
MIN_COURSE_MODULES=1
MIN_MODULE_LESSONS=1
```

---

## PART 5: Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2) ✅ MOSTLY COMPLETE
- [x] FastAPI setup & configuration
- [x] PostgreSQL connection & models
- [x] MongoDB connection & logging
- [x] User authentication (register, login, refresh)
- [x] Security layer (JWT, password hashing, CORS)
- [x] User & Profile models
- [x] Email service integration (SendGrid)
- [x] Cloudinary service integration

### Phase 2: Course Management (Weeks 3-4) ⚠️ IN PROGRESS
- [x] Course CRUD operations
- [x] Module CRUD operations
- [x] Lesson/Video integration
- [x] YouTube API integration
- [ ] Course publishing workflow (NEEDS IMPLEMENTATION)
- [ ] Course preview functionality (NEEDS IMPLEMENTATION)

### Phase 3: Enrollment & Progress (Weeks 5-6) ⚠️ PARTIALLY DONE
- [x] Enrollment CRUD
- [x] Progress tracking models
- [x] Mark lesson complete endpoint
- [x] Progress calculation logic
- [ ] Progress tracking UI integration (FRONTEND)
- [ ] Next lesson recommendation (NEEDS OPTIMIZATION)

### Phase 4: Gamification (Weeks 7-8) ⚠️ PARTIALLY DONE
- [x] Badge model & logic
- [x] Streak tracking
- [ ] Badge award automation (NEEDS TESTING)
- [ ] Leaderboard ranking (NEEDS OPTIMIZATION)
- [ ] XP point system (OPTIONAL)

### Phase 5: AI Coach (Week 9) ⚠️ NOT STARTED
- [ ] Gemini API integration
- [ ] Tutor mode implementation
- [ ] Debugger mode implementation
- [ ] Mentor mode implementation
- [ ] Context-aware chat history

### Phase 6: Admin Dashboard (Week 10) ⚠️ NOT STARTED
- [ ] Analytics endpoints
- [ ] User management
- [ ] Course statistics
- [ ] Report generation

### Phase 7: Testing & Deployment (Weeks 11-12) ⚠️ NOT STARTED
- [ ] Unit tests (Pytest)
- [ ] Integration tests
- [ ] Load testing
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Production deployment

---

## PART 6: Scalability & Performance Considerations

### Database Optimization
```python
# Indexes created for performance
user_progress: (user_id, course_id, is_completed)
enrollments: (user_id, is_completed)
courses: (instructor_id, status)
lessons: (module_id, order)

# Pagination prevents memory overload
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Query optimization with select_in_load for relationships
from sqlalchemy.orm import selectinload
session.query(Course)\
    .options(selectinload(Course.modules))\
    .filter(Course.status == 'published')
```

### Caching Strategy
```python
# Redis caching for frequently accessed data
CACHE_TTL_COURSES = 3600  # 1 hour
CACHE_TTL_PROGRESS = 300  # 5 minutes
CACHE_TTL_LEADERBOARD = 600  # 10 minutes
```

### Async Processing
```python
# Email notifications sent asynchronously
from celery import Celery

app = Celery('kukekodes')

@app.task
async def send_lesson_completion_email(user_id: str, lesson_id: str):
    # This runs in background, doesn't block API response
    pass
```

### Database Connection Pooling
```python
# SQLAlchemy connection pool settings
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,  # Verify connections
)
```

### CDN for Media
```python
# Cloudinary serves all media through CDN
# Automatic image optimization and transformation
cloudinary.utils.cloudinary_url(public_id, transformation=[
    {"width": 600, "height": 300, "crop": "fill"},
    {"quality": "auto"}
])
```

---

## PART 7: Error Handling & Validation

### Custom Exception Hierarchy
```python
class KukekodesException(Exception):
    """Base exception for Kukekodes."""
    pass

class ResourceNotFoundError(KukekodesException):
    """Resource not found."""
    pass

class UnauthorizedError(KukekodesException):
    """User not authorized."""
    pass

class ValidationError(KukekodesException):
    """Validation failed."""
    pass

class ExternalServiceError(KukekodesException):
    """External service (YouTube, Sendgrid) error."""
    pass
```

### Global Exception Handler
```python
@app.exception_handler(KukekodesException)
async def kukekodes_exception_handler(request: Request, exc: KukekodesException):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.__class__.__name__,
            "detail": str(exc),
            "request_id": request.headers.get("X-Request-ID")
        }
    )
```

---

## PART 8: Testing Strategy

### Unit Tests
```python
# Test progress calculation logic
def test_mark_lesson_complete():
    # Setup
    user = create_test_user()
    course = create_test_course()
    lesson = create_test_lesson(course)
    
    # Action
    progress = mark_lesson_complete(user, lesson)
    
    # Assert
    assert progress.is_completed == True
    assert progress.completed_at is not None
```

### Integration Tests
```python
# Test full enrollment + progress flow
async def test_enrollment_to_completion():
    # Setup
    user = create_test_user()
    course = create_test_course()
    
    # Enroll
    enrollment = await client.post(f"/enrollments/{course.id}")
    
    # Complete lessons
    for lesson in course.modules[0].lessons:
        await client.post(f"/progress/mark-lesson-complete/{lesson.id}")
    
    # Assert enrollment completed
    enrollment = await get_enrollment(user, course)
    assert enrollment.is_completed == True
```

### Load Testing
```python
# Locust load test
from locust import HttpUser, task, between

class LearnerUser(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def browse_courses(self):
        self.client.get("/courses")
    
    @task
    def mark_complete(self):
        self.client.post(f"/progress/mark-lesson-complete/lesson_id")
```

---

## PART 9: Deployment Architecture

### Docker Containerization
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY .env .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (Development)
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/kukekodes
      - MONGODB_URI=mongodb://mongo:27017
    depends_on:
      - postgres
      - mongo
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=kukekodes
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
  
  mongo:
    image: mongo:6
```

### Production Deployment (AWS/GCP/DigitalOcean)
```yaml
# Kubernetes Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kukekodes-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kukekodes-api
  template:
    metadata:
      labels:
        app: kukekodes-api
    spec:
      containers:
      - name: api
        image: your-registry/kukekodes-api:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: kukekodes-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## PART 10: Success Metrics & KPIs

### User Engagement
- **Daily Active Users (DAU):** Target 500+
- **Course Completion Rate:** Target 70%+
- **Average Time per Lesson:** 12-15 minutes
- **Return Users (7-day retention):** Target 60%+

### Course Quality
- **Average Course Rating:** Target 4.5+/5.0
- **Students per Course:** Target 100+
- **Lessons per Course:** Minimum 5

### System Performance
- **API Response Time:** P95 < 200ms
- **Database Query Time:** P95 < 50ms
- **Error Rate:** < 0.1%
- **Uptime:** 99.9%+

### Business Metrics
- **User Growth:** 20% month-over-month
- **Course Creation Rate:** 5 new courses/week
- **Instructor Engagement:** 80% of instructors create 2+ courses

---

## PART 11: Next Steps & Action Items

### Immediate (This Week)
- [ ] Set up .env with all API keys
- [ ] Deploy PostgreSQL and MongoDB (Supabase & MongoDB Atlas)
- [ ] Test course creation and publishing workflow
- [ ] Implement course preview endpoint
- [ ] Complete progress tracking endpoints

### Short-term (2-3 Weeks)
- [ ] Implement full gamification system
- [ ] Add AI Coach integration
- [ ] Create admin analytics dashboard
- [ ] Write comprehensive unit tests
- [ ] Add API documentation (Swagger/OpenAPI)

### Medium-term (1 Month)
- [ ] Implement caching layer (Redis)
- [ ] Add background job processing (Celery)
- [ ] Performance optimization & load testing
- [ ] Implement advanced search & filtering
- [ ] Add notification preferences UI

### Long-term (2-3 Months)
- [ ] Video hosting optimization
- [ ] Machine learning for course recommendations
- [ ] Community features (forums, Q&A)
- [ ] Advanced analytics & reporting
- [ ] Mobile app backend API
- [ ] Real-time notifications (WebSockets)

---

## Conclusion

This implementation plan provides a **scalable, secure, and production-ready** Learning Management System for Kukekodes. The architecture follows industry best practices:

✅ **Clean Code Structure:** Modular design with separation of concerns  
✅ **Security at All Layers:** Authentication, authorization, input validation  
✅ **Performance Optimized:** Indexing, caching, async processing  
✅ **Scalable Architecture:** Connection pooling, pagination, CDN  
✅ **Comprehensive Testing:** Unit, integration, and load testing  
✅ **Production Ready:** Docker, Kubernetes, CI/CD pipeline  

By following this plan, Kukekodes will be positioned to serve thousands of students while maintaining code quality and security standards.

---

**Document Version:** 2.0  
**Last Updated:** January 15, 2026  
**Status:** Ready for Implementation
