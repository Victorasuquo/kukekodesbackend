# Kukekodes Backend Architecture & Implementation Plan

## Executive Summary

A scalable, secure, and modular FastAPI backend for the kukekodes learning platform with MongoDB for operational data, PostgreSQL for relational data, SendGrid for notifications, and Cloudinary for media management.

---

## 1. Technology Stack

### Backend Framework
- **FastAPI**: Async Python web framework for high performance
- **Pydantic**: Data validation and serialization
- **SQLAlchemy ORM**: PostgreSQL ORM for relational data

### Databases
- **PostgreSQL (Supabase)**: User accounts, courses, modules, lessons, progress tracking, enrollments, badges
- **MongoDB**: Activity logs, analytics, dynamic content, unstructured user interactions
- **Redis** (optional, for caching): Session management, real-time notifications queue

### External Services
- **SendGrid**: Email notifications and reminders
- **Cloudinary**: Media file management (course assets, user profiles)
- **YouTube API**: Fetch video metadata and transcripts
- **Google Gemini API**: AI Coach integration

### Security
- **JWT (PyJWT)**: Token-based authentication
- **Bcrypt**: Password hashing
- **CORS**: Cross-origin resource sharing
- **Rate Limiting**: Prevent abuse
- **Input Validation**: Pydantic models with strict validation

---

## 2. Project Structure

```
kukekodes-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # Entry point, FastAPI app initialization
│   ├── config.py                        # Environment variables and settings
│   ├── security.py                      # JWT, password hashing, CORS
│   ├── dependencies.py                  # Shared dependencies (DB sessions, auth)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py            # Login, register, password reset
│   │   │   │   ├── schemas.py           # Request/response models
│   │   │   │   └── service.py           # Auth business logic
│   │   │   │
│   │   │   ├── users/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py            # User profile, settings
│   │   │   │   ├── schemas.py
│   │   │   │   └── service.py
│   │   │   │
│   │   │   ├── courses/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py            # Admin & learner endpoints
│   │   │   │   ├── schemas.py           # Course, Module, Lesson schemas
│   │   │   │   ├── service.py           # Course business logic
│   │   │   │   └── models.py            # Database models
│   │   │   │
│   │   │   ├── modules/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py            # Module CRUD
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   └── models.py
│   │   │   │
│   │   │   ├── lessons/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py            # Lesson CRUD and YouTube integration
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   └── models.py
│   │   │   │
│   │   │   ├── progress/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py            # Mark lesson complete, progress tracking
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   └── models.py
│   │   │   │
│   │   │   ├── enrollments/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py            # Enroll, unenroll
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   └── models.py
│   │   │   │
│   │   │   ├── community/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py            # Forums, Q&A
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   └── models.py
│   │   │   │
│   │   │   ├── gamification/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py            # Badges, streaks, XP
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   └── models.py
│   │   │   │
│   │   │   ├── notifications/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py            # Notification preferences
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   └── models.py
│   │   │   │
│   │   │   ├── ai/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py            # AI Coach chat endpoint
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py           # Gemini API integration
│   │   │   │   └── agents.py            # Tutor, debugger, mentor modes
│   │   │   │
│   │   │   └── admin/
│   │   │       ├── __init__.py
│   │   │       ├── routes.py            # Admin dashboard, analytics
│   │   │       ├── schemas.py
│   │   │       └── service.py
│   │   │
│   │   └── health.py                    # Health check endpoint
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                      # User, Profile models
│   │   ├── course.py                    # Course model
│   │   ├── module.py                    # Module model
│   │   ├── lesson.py                    # Lesson model
│   │   ├── enrollment.py                # Enrollment tracking
│   │   ├── progress.py                  # User progress per lesson
│   │   ├── badge.py                     # Badge system
│   │   ├── community.py                 # Forum, thread, reply models
│   │   └── notification.py              # Notification preferences
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py                    # Shared schemas (pagination, responses)
│   │   ├── user.py                      # User Pydantic models
│   │   ├── course.py                    # Course Pydantic models
│   │   ├── module.py
│   │   ├── lesson.py
│   │   ├── progress.py
│   │   └── ai.py                        # AI Coach request/response
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email_service.py             # SendGrid integration
│   │   ├── youtube_service.py           # YouTube API integration
│   │   ├── cloudinary_service.py        # Cloudinary integration
│   │   ├── ai_service.py                # Gemini API integration
│   │   ├── analytics_service.py         # MongoDB analytics
│   │   └── storage_service.py           # Database helpers
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py                    # Logging configuration
│   │   ├── exceptions.py                # Custom exceptions
│   │   ├── validators.py                # Custom validators
│   │   └── decorators.py                # Auth, role-based decorators
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── error_handler.py             # Global error handling
│   │   ├── rate_limiter.py              # Rate limiting
│   │   └── request_logger.py            # Request/response logging
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── postgres.py                  # PostgreSQL connection
│   │   ├── mongodb.py                   # MongoDB connection
│   │   └── migrations/                  # Alembic migrations (future)
│   │       └── versions/
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                  # Pytest fixtures
│       ├── test_auth.py
│       ├── test_courses.py
│       ├── test_progress.py
│       ├── test_ai.py
│       └── test_integration.py
│
├── .env.example                         # Environment template
├── .gitignore
├── requirements.txt                     # Python dependencies
├── docker-compose.yml                   # Docker services
├── Dockerfile
├── README.md
└── wsgi.py                              # Production entry point
```

---

## 3. Database Schema Overview

### PostgreSQL (Relational Data)

#### Users Table
```
users
├── id (PK)
├── email (UNIQUE)
├── password_hash
├── first_name
├── last_name
├── country
├── role (student, instructor, admin)
├── is_active
├── is_email_verified
├── created_at
├── updated_at
```

#### Courses Table
```
courses
├── id (PK)
├── title
├── description
├── tags (array or JSON)
├── skill_level (beginner, intermediate, advanced)
├── instructor_id (FK)
├── status (draft, published, archived)
├── is_free
├── created_at
├── updated_at
├── cover_image_url (Cloudinary)
```

#### Modules Table
```
modules
├── id (PK)
├── course_id (FK)
├── title
├── description
├── order (sequence)
├── created_at
├── updated_at
```

#### Lessons Table
```
lessons
├── id (PK)
├── module_id (FK)
├── title
├── description
├── youtube_video_id
├── youtube_url
├── duration_minutes
├── order (sequence within module)
├── transcript (nullable)
├── resources (JSON: links, PDFs)
├── status (draft, published)
├── created_at
├── updated_at
```

#### Enrollments Table
```
enrollments
├── id (PK)
├── user_id (FK)
├── course_id (FK)
├── enrolled_at
├── completion_percentage
├── is_completed
├── completed_at (nullable)
├── current_module_id (FK, nullable)
├── current_lesson_id (FK, nullable)
```

#### User Progress Table
```
user_progress
├── id (PK)
├── user_id (FK)
├── lesson_id (FK)
├── module_id (FK)
├── course_id (FK)
├── is_completed
├── time_spent_minutes
├── quiz_score (nullable)
├── watched_at
├── completed_at (nullable)
```

#### Badges Table
```
badges
├── id (PK)
├── name
├── description
├── icon_url (Cloudinary)
├── criteria (JSON: conditions for earning)
├── created_at
```

#### User Badges Table (M2M)
```
user_badges
├── id (PK)
├── user_id (FK)
├── badge_id (FK)
├── earned_at
```

#### Streaks Table
```
streaks
├── id (PK)
├── user_id (FK)
├── current_streak_count
├── longest_streak_count
├── last_activity_date
├── updated_at
```

#### Notifications Table
```
notifications
├── id (PK)
├── user_id (FK)
├── title
├── message
├── type (assignment, reminder, achievement)
├── is_read
├── created_at
```

### MongoDB (Unstructured Data)

#### Collections

```
activities
├── user_id
├── action (viewed_lesson, started_course, etc.)
├── entity_id (course_id, lesson_id)
├── timestamp
├── metadata (JSON)

ai_interactions
├── user_id
├── lesson_id
├── question
├── ai_response
├── agent_mode (tutor, debugger, mentor)
├── timestamp

forum_threads
├── id
├── course_id
├── user_id
├── title
├── content
├── tags
├── replies_count
├── upvotes
├── created_at

forum_replies
├── thread_id
├── user_id
├── content
├── upvotes
├── created_at

analytics
├── user_id
├── course_id
├── engagement_score
├── time_spent
├── quiz_scores
├── completion_rate
```

---

## 4. API Endpoint Structure

### Authentication
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh-token
POST   /api/v1/auth/logout
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password
```

### Courses (Admin)
```
POST   /api/v1/courses                      # Create course
GET    /api/v1/courses/{course_id}          # Get course details
PUT    /api/v1/courses/{course_id}          # Update course
DELETE /api/v1/courses/{course_id}          # Delete course
POST   /api/v1/courses/{course_id}/publish  # Publish course
GET    /api/v1/courses/{course_id}/preview  # Preview course
```

### Modules (Admin)
```
POST   /api/v1/modules                      # Create module (under course)
GET    /api/v1/modules/{module_id}
PUT    /api/v1/modules/{module_id}
DELETE /api/v1/modules/{module_id}
PUT    /api/v1/modules/{module_id}/reorder  # Reorder modules
```

### Lessons (Admin)
```
POST   /api/v1/lessons                      # Create lesson
GET    /api/v1/lessons/{lesson_id}
PUT    /api/v1/lessons/{lesson_id}
DELETE /api/v1/lessons/{lesson_id}
POST   /api/v1/lessons/{lesson_id}/youtube  # Add YouTube URL
GET    /api/v1/lessons/{lesson_id}/metadata # Fetch YouTube metadata
```

### Courses (Learner)
```
GET    /api/v1/courses                      # List published courses
GET    /api/v1/courses/{course_id}          # Get course details
POST   /api/v1/enrollments                  # Enroll in course
```

### Progress Tracking
```
POST   /api/v1/progress/mark-lesson-complete/{lesson_id}
GET    /api/v1/progress/course/{course_id}
GET    /api/v1/progress/user/dashboard
```

### AI Coach
```
POST   /api/v1/ai/chat                      # Chat with AI
POST   /api/v1/ai/explain/{lesson_id}
POST   /api/v1/ai/debug
POST   /api/v1/ai/practice-quiz/{lesson_id}
```

### Community
```
GET    /api/v1/forum/threads
POST   /api/v1/forum/threads                # Create thread
GET    /api/v1/forum/threads/{thread_id}
POST   /api/v1/forum/threads/{thread_id}/replies
```

### Gamification
```
GET    /api/v1/badges/user                  # Get user badges
GET    /api/v1/streaks/user
GET    /api/v1/leaderboard
```

### Notifications
```
GET    /api/v1/notifications
PUT    /api/v1/notifications/{id}/read
PUT    /api/v1/notifications/preferences
```

### Admin Dashboard
```
GET    /api/v1/admin/analytics/overview
GET    /api/v1/admin/analytics/courses/{course_id}
GET    /api/v1/admin/users
GET    /api/v1/admin/reports
```

---

## 5. Security Implementation

### Authentication & Authorization
```python
# JWT Tokens with refresh rotation
# Access token: 15 minutes
# Refresh token: 7 days
# Secure HTTP-only cookies (frontend)

# Role-based access control (RBAC)
- STUDENT: View published courses, enroll, track progress
- INSTRUCTOR: Create/edit courses, view student progress
- ADMIN: Full access, analytics, user management
```

### Data Protection
```
1. Password Hashing: Bcrypt (cost factor 12)
2. Input Validation: Pydantic models with sanitization
3. SQL Injection Prevention: SQLAlchemy ORM parameterized queries
4. CORS: Configured for specific origins
5. Rate Limiting: 
   - Auth endpoints: 5 requests/minute per IP
   - API endpoints: 100 requests/minute per user
6. Request Logging: All API calls logged to analytics DB
```

### API Security
```
1. Helmet Headers: X-Content-Type-Options, X-Frame-Options
2. HTTPS Only: Enforce in production
3. API Key Rotation: SendGrid, YouTube, Gemini keys from env
4. Timeout: 30 seconds on external API calls
5. Circuit Breaker: Fallback if external service fails
```

---

## 6. Course Publishing Workflow

### Step 1: Create Course (Admin)
```
POST /api/v1/courses
{
  "title": "Machine Learning for Beginners",
  "description": "...",
  "tags": ["ML", "AI", "Python"],
  "skill_level": "beginner",
  "instructor_id": "uuid"
}
Response: {course_id, status: "draft"}
```

### Step 2: Add Modules
```
POST /api/v1/modules
{
  "course_id": "uuid",
  "title": "Module 1: Introduction to ML",
  "description": "...",
  "order": 1
}
Response: {module_id, status: "draft"}
```

### Step 3: Add Lessons with YouTube URLs
```
POST /api/v1/lessons
{
  "module_id": "uuid",
  "title": "What is Machine Learning?",
  "youtube_url": "https://youtube.com/watch?v=...",
  "order": 1
}
# Backend:
# - Fetch metadata from YouTube API (title, duration, thumbnail)
# - Store video_id, duration, thumbnail_url
# - Generate transcript (optional, via YouTube API)
Response: {lesson_id, status: "draft", duration_minutes: 12}
```

### Step 4: Preview Course
```
GET /api/v1/courses/{course_id}/preview
# Shows structure: Course > Modules > Lessons (all with status indicators)
Response: Full course tree with all metadata
```

### Step 5: Publish Course
```
POST /api/v1/courses/{course_id}/publish
# Validates:
# - All lessons have YouTube URLs
# - At least 1 module with 1 lesson
# - Course has title, description, tags
Response: {status: "published", published_at: "2025-01-14T..."}
```

---

## 7. Progress Tracking Flow

### Architecture
```
User opens Lesson → GET /api/v1/lessons/{lesson_id}
                  → Frontend loads YouTube video
                  → User watches video
                  → 
User clicks "Mark Complete" → POST /api/v1/progress/mark-lesson-complete/{lesson_id}
                            →
Backend:
  1. Validate user enrolled in course
  2. Check previous lessons completed (optional)
  3. Create/update user_progress record
  4. Calculate module completion %
  5. Calculate course completion %
  6. Check for badge eligibility
  7. Update streak
  8. Trigger email notification
  9. Return next lesson recommendation

Response: {
  lesson_status: "completed",
  lesson_marked_green: true,
  module_progress: { completed: 3, total: 5 },
  course_progress: { percentage: 60, completed: 3, total: 5 },
  next_lesson: { id, title, module_id },
  badges_earned: ["First Lesson Complete"],
  streak: 7
}
```

### Database Updates on Completion
```
1. user_progress:
   - is_completed = true
   - completed_at = NOW()
   - time_spent_minutes = calculated

2. enrollments:
   - completion_percentage = (completed_lessons / total_lessons) * 100
   - is_completed = true (if all lessons done)
   - completed_at = NOW()
   - current_lesson_id = next lesson OR null

3. streaks:
   - current_streak_count += 1 (if last activity was yesterday)
   - last_activity_date = TODAY()

4. badges (check criteria):
   - "First Lesson" → earned if lessons_completed == 1
   - "7-Day Streak" → earned if streak == 7
   - "Course Complete" → earned if course == 100%

5. Notifications (email via SendGrid):
   - Subject: "Great work! Lesson completed"
   - Also trigger in-app notification
```

### Progress Visualization (Frontend)
```
Course Page:
├── Progress Bar: 60% complete
├── Module 1: ✓ (green)
│   ├── Lesson 1: ✓ (green)
│   ├── Lesson 2: ✓ (green)
│   ├── Lesson 3: ✓ (green)
│   └── Lesson 4: ... (not completed)
├── Module 2: (gray)
│   ├── Lesson 5: ... (not started)
│   └── Lesson 6: ... (locked until previous complete)
└── Streak: 7 days 🔥
```

---

## 8. External Services Integration

### SendGrid (Email Notifications)
```python
# Events that trigger emails:
1. New enrollment: "Welcome to course!"
2. Lesson completed: "Great work! Keep the streak!"
3. Streak milestone: "You're on a 7-day streak!"
4. Course completed: "Congratulations! Download certificate"
5. Weekly summary: "Here's your progress this week"
6. Assignment due: "Your assignment is due soon"

# Implementation:
- Async email queue (background task)
- Template management
- Unsubscribe links
- Rate: 1 email per 24 hours per type per user
```

### YouTube API
```python
# On lesson creation with YouTube URL:
1. Extract video ID from URL
2. Call YouTube API for metadata:
   - title
   - duration
   - thumbnail URL
   - channel info
3. Store in lessons table
4. Optional: Fetch transcript via YouTube API or Otter.ai

# Error handling:
- Invalid video ID → 400 error
- Video deleted → 404 error
- Rate limited → Retry with exponential backoff
```

### Cloudinary (Media Upload)
```python
# Use cases:
1. User profile pictures → transformation: 200x200, round
2. Course cover images → transformation: 600x300
3. Badge icons → transformation: 128x128
4. Certificate generation (future)

# Implementation:
- Upload to "kukekodes/courses", "kukekodes/profiles" folders
- Delete on resource removal
- CDN delivery via Cloudinary URL
```

### Gemini API (AI Coach)
```python
# Context injection:
{
  "system_prompt": "You are a patient programming tutor...",
  "user_context": {
    "current_lesson": "...",
    "user_code": "...",
    "quiz_history": [...],
    "skill_level": "beginner"
  },
  "user_message": "How do I fix this error?"
}

# Agent modes:
1. TUTOR: Explain concepts, not direct answers
2. DEBUGGER: Analyze code, suggest fixes
3. MENTOR: Career advice, learning strategies

# Safety:
- Block unsafe code suggestions
- Prevent giving answers to graded assessments
- Log all interactions for quality monitoring
```

---

## 9. Deployment & DevOps

### Docker Compose Stack
```yaml
services:
  api:
    build: .
    ports: 8000:8000
    env_file: .env
    depends_on: [postgres, mongodb, redis]
    
  postgres:
    image: postgres:16
    env: DATABASE_URL
    volumes: [postgres_data:/var/lib/postgresql/data]
    
  mongodb:
    image: mongo:7
    env: MONGODB_URI
    volumes: [mongo_data:/data/db]
    
  redis:
    image: redis:7-alpine
    ports: 6379:6379
```

### Environment Variables (.env)
```
# Database
DATABASE_URL=postgresql://user:pass@host:5432/kukekodes
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/kukekodes

# External APIs
SENDGRID_API_KEY=...
CLOUDINARY_API_KEY=...
YOUTUBE_API_KEY=...
GEMINI_API_KEY=...

# Security
JWT_SECRET=...
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["https://kukekodes.com", "http://localhost:3000"]

# Logging
LOG_LEVEL=INFO
```

---

## 10. Implementation Priority (MVP Phase)

### Phase 1: Core (Week 1-2)
- ✅ Auth service (register, login, JWT)
- ✅ User profiles
- ✅ Course CRUD (admin)
- ✅ Module CRUD
- ✅ Lesson CRUD with YouTube integration

### Phase 2: Learning (Week 3-4)
- ✅ Enrollments
- ✅ Progress tracking
- ✅ Mark lesson complete with grade updates
- ✅ Email notifications via SendGrid

### Phase 3: Engagement (Week 5-6)
- ✅ Gamification (streaks, badges, XP)
- ✅ Basic community forums
- ✅ AI Coach (simple mode)
- ✅ Leaderboard

### Phase 4: Polish (Week 7+)
- ✅ Analytics dashboard
- ✅ Advanced AI modes
- ✅ Live events/webinars
- ✅ Mobile optimization
- ✅ Performance optimization

---

## 11. Code Quality & Testing

### Testing Strategy
```
Unit Tests: 80% code coverage
- Auth logic, validation, calculations

Integration Tests: Key workflows
- Course creation → enrollment → progress
- AI coach interactions
- Email notifications

End-to-end Tests: Critical user paths
- User signup → enroll → complete course
- Admin course publishing
```

### CI/CD Pipeline
```
GitHub Actions:
1. Lint (black, flake8, isort)
2. Type Check (mypy)
3. Unit Tests (pytest)
4. Build Docker image
5. Push to container registry
6. Deploy to staging (Heroku/Railway)
7. Run smoke tests
8. Deploy to production
```

---

## 12. Monitoring & Logging

```
CloudWatch / ELK Stack:
- API response times
- Error rates by endpoint
- Database query performance
- External API failures
- User activity trends

Alerts:
- Error rate > 1%
- API response time > 2s
- Database connection pool exhausted
- External service timeout
```

---

## Next Steps

1. **Database Setup**: Create PostgreSQL & MongoDB schemas
2. **Project Initialization**: FastAPI boilerplate with async/await
3. **Auth Service**: JWT implementation
4. **Course Management**: Full CRUD with validation
5. **Progress Tracking**: Core logic & grade calculations
6. **Integration Tests**: Verify workflows
7. **Deployment**: Docker setup for Heroku/Railway/DigitalOcean

This architecture ensures scalability, security, and maintainability for kukekodes.