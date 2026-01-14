# Kukekodes Backend - Setup & Deployment Guide

## Project Overview

Kukekodes is a global learning platform for coding and AI skills. This is the FastAPI backend that handles:
- User authentication (registration/login)
- Admin course creation & management
- Module and lesson management with YouTube integration
- Progress tracking with email notifications via SendGrid
- AI Coach integration (Gemini)
- Community forums and gamification

## Technology Stack

- **Backend**: FastAPI (Python)
- **Databases**: PostgreSQL (Supabase) + MongoDB (Atlas)
- **Authentication**: JWT tokens
- **Email**: SendGrid
- **APIs**: YouTube, Gemini, Cloudinary
- **Deployment**: Docker, Railway/Heroku

## Quick Start

### 1. Prerequisites

- Python 3.10+
- PostgreSQL database (Supabase recommended)
- MongoDB instance (Atlas recommended)
- SendGrid API key
- YouTube API key
- Git

### 2. Clone & Setup

```bash
# Clone repository
git clone <repo-url>
cd kukekodes-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your actual credentials
# IMPORTANT: Never commit .env file
```

#### Key Environment Variables:

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/kukekodes
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/

# Security (Change these!)
JWT_SECRET=your-long-random-secret-key-at-least-32-chars
DEBUG=false

# External Services
SENDGRID_API_KEY=SG.xxxxx
YOUTUBE_API_KEY=xxxxx
GEMINI_API_KEY=xxxxx
```

### 4. Initialize Database

```bash
# The database tables will be created automatically on app startup
# But you can pre-create them with:
python -c "from app.db.postgres import init_db; init_db()"
```

### 5. Run Development Server

```bash
# Start FastAPI development server
uvicorn app.main:app --reload

# Server runs on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

## API Workflow

### Phase 1: Admin Creates Course

#### Step 1: Create Course
```bash
curl -X POST http://localhost:8000/api/v1/courses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{
    "title": "Python Fundamentals",
    "description": "Learn Python from zero to job-ready",
    "tags": ["python", "beginner"],
    "skill_level": "beginner",
    "is_free": true
  }'

# Response includes course_id
```

#### Step 2: Create Module Under Course
```bash
curl -X POST http://localhost:8000/api/v1/modules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{
    "course_id": "<COURSE_ID>",
    "title": "Module 1: Getting Started",
    "description": "Introduction to Python",
    "order": 1
  }'

# Response includes module_id
```

#### Step 3: Add Lesson with YouTube URL
```bash
curl -X POST http://localhost:8000/api/v1/lessons \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{
    "module_id": "<MODULE_ID>",
    "title": "What is Python?",
    "description": "Introduction video",
    "youtube_url": "https://www.youtube.com/watch?v=...",
    "order": 1
  }'

# Backend automatically:
# - Extracts video ID
# - Fetches duration from YouTube API
# - Fetches thumbnail
# - Stores lesson
```

#### Step 4: Preview Course
```bash
curl http://localhost:8000/api/v1/courses/<COURSE_ID>/preview \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# Returns validation status and any errors
```

#### Step 5: Publish Course
```bash
curl -X POST http://localhost:8000/api/v1/courses/<COURSE_ID>/publish \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{}'

# Validates structure and publishes
# Course is now visible to students
```

---

### Phase 2: Student Registers & Learns

#### Step 1: Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "MyPassword123",
    "first_name": "John",
    "last_name": "Doe",
    "country": "Nigeria"
  }'

# Response includes access_token & refresh_token
# Welcome email sent via SendGrid
```

#### Step 2: Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "MyPassword123"
  }'

# Returns tokens for authenticated requests
```

#### Step 3: Enroll in Course
```bash
curl -X POST http://localhost:8000/api/v1/enrollments \
  -H "Authorization: Bearer <STUDENT_TOKEN>" \
  -d '{
    "course_id": "<COURSE_ID>"
  }'

# Student can now access course content
```

#### Step 4: Watch Lesson & Mark Complete
```bash
# Get lesson details
curl http://localhost:8000/api/v1/lessons/<LESSON_ID> \
  -H "Authorization: Bearer <STUDENT_TOKEN>"

# After watching, mark lesson complete
curl -X POST http://localhost:8000/api/v1/progress/mark-lesson-complete/<LESSON_ID> \
  -H "Authorization: Bearer <STUDENT_TOKEN>" \
  -d '{
    "time_spent_minutes": 15
  }'

# Backend automatically:
# 1. Marks lesson as completed ✅
# 2. Updates module progress
# 3. Updates course progress %
# 4. Increments streak counter
# 5. Checks for badges
# 6. Sends completion email via SendGrid
# 7. Recommends next lesson
```

---

## Email Notifications (SendGrid)

### Automatic Emails Sent

1. **Welcome Email** - After registration
   - Subject: "Welcome to Kukekodes! 🚀"
   - HTML template with dashboard link
   - Non-blocking (sent async)

2. **Lesson Completed** - After marking lesson complete
   - Subject: "Great work! You completed '<lesson>' 🎉"
   - Shows progress percentage
   - Shows next lesson recommendation

3. **Streak Milestone** - Every 7 days
   - Subject: "You're on a 7-day streak! 🔥"
   - Motivational message

4. **Course Completed** - When course is 100% complete
   - Subject: "Congratulations! You completed '<course>' 🏆"
   - Certificate info
   - What's next suggestions

### Email Templates

Located in `app/services/email_service.py`:
- `WelcomeEmailTemplate`
- `LessonCompletedEmailTemplate`
- `StreakMilestoneEmailTemplate`
- `CourseCompletedEmailTemplate`

All are fully customizable HTML templates.

---

## Database Schema

### PostgreSQL Tables

```
users                    (user accounts)
├── id, email, password_hash
├── first_name, last_name, country
├── role (student/instructor/admin)
└── created_at, updated_at

courses                  (course definitions)
├── id, title, description
├── instructor_id (FK to users)
├── status (draft/published/archived)
├── tags, skill_level, category
└── created_at, published_at

modules                  (course units)
├── id, course_id (FK)
├── title, description, order
└── created_at

lessons                  (individual videos)
├── id, module_id (FK)
├── title, youtube_url, youtube_video_id
├── duration_minutes, thumbnail_url
├── order, status
└── created_at

enrollments              (user course progress)
├── id, user_id, course_id (unique pair)
├── completion_percentage, is_completed
├── current_lesson_id, current_module_id
└── enrolled_at, completed_at

user_progress            (lesson-level tracking)
├── id, user_id, lesson_id (unique pair)
├── module_id, course_id
├── is_completed, time_spent_minutes
└── completed_at

streaks                  (gamification)
├── user_id (unique)
├── current_streak_count
├── longest_streak_count
└── last_activity_date

badges                   (achievements)
├── id, name, description
├── criteria (JSON: type, count)
└── icon_url

notifications            (user notifications)
├── id, user_id
├── title, message, type
├── is_read, email_sent
└── created_at
```

### MongoDB Collections

```
activities               (user actions log)
├── user_id, action, entity_id
├── entity_type, metadata
└── timestamp

ai_interactions          (AI coach conversations)
├── user_id, lesson_id
├── question, response
├── agent_mode (tutor/debugger/mentor)
└── timestamp

forum_threads
├── id, course_id, user_id
├── title, content, tags
├── replies_count, upvotes
└── created_at

analytics                (user engagement)
├── user_id, course_id
├── engagement_score, time_spent
├── quiz_scores, completion_rate
└── updated_at
```

---

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t kukekodes-backend .

# Run container
docker run -p 8000:8000 --env-file .env kukekodes-backend

# With docker-compose (includes PostgreSQL, MongoDB, Redis)
docker-compose up -d
```

### Railway/Heroku Deployment

```bash
# Login
heroku login

# Create app
heroku create kukekodes-backend

# Set environment variables
heroku config:set DATABASE_URL=postgresql://...
heroku config:set MONGODB_URI=mongodb+srv://...
heroku config:set JWT_SECRET=...
# ... set other required variables

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

### Environment for Production

```env
ENVIRONMENT=production
DEBUG=false
JWT_SECRET=<generate-strong-random-key>
SENDGRID_API_KEY=<production-key>
DATABASE_URL=<production-postgres>
MONGODB_URI=<production-mongodb>
CORS_ORIGINS=["https://yourdomain.com"]
```

---

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_auth.py
```

### Example Test

```python
# tests/test_auth.py
def test_user_registration(client):
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPassword123",
        "first_name": "Test",
        "last_name": "User",
    })
    assert response.status_code == 201
    assert "access_token" in response.json()["token"]
```

---

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Common Issues & Solutions

### PostgreSQL Connection Error
```
Error: could not connect to server: Connection refused
```
**Solution**: Ensure PostgreSQL is running and DATABASE_URL is correct

### MongoDB Connection Error
```
Error: [Errno -2] Name or service not known
```
**Solution**: Check MONGODB_URI and ensure internet connection for Atlas

### SendGrid Email Not Sending
```
Error: 401 Unauthorized
```
**Solution**: Verify SENDGRID_API_KEY is correct and valid

### YouTube API Quota Exceeded
**Solution**: 
- Implement caching for metadata
- Request quota increase from Google
- Use fallback thumbnail URL

---

## Performance Optimization

### Database Optimization
```python
# Use indexes (already in models)
# Batch operations where possible
# Use connection pooling (configured in postgres.py)
```

### Caching Strategy
```python
# Cache:
# - Published courses list (1 hour)
# - User progress (5 minutes)
# - YouTube metadata (24 hours)
# - Badge definitions (on startup)
```

### Email Queue
```python
# Use background tasks to avoid blocking
# Implement retry logic for failed emails
# Batch emails for efficiency
```

---

## Security Checklist

- [ ] Change JWT_SECRET in production
- [ ] Enable HTTPS only
- [ ] Set secure CORS origins
- [ ] Enable rate limiting
- [ ] Use environment variables for all secrets
- [ ] Enable database encryption
- [ ] Set up CSRF protection
- [ ] Implement API key rotation
- [ ] Enable audit logging
- [ ] Regular security updates

---

## Support & Contribution

For issues or contributions, please:
1. Check existing issues
2. Create detailed bug reports
3. Follow code style (black, isort, flake8)
4. Add tests for new features
5. Update documentation

---

## License

Proprietary - Kukekodes Learning Platform

---

Last Updated: January 2025