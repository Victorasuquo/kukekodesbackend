# Kukekodes Backend - Implementation Guide

## Phase 1: Admin Authentication & Dashboard (Week 1)

### ✅ Completed Files

1. **config.py** ✓
   - Environment configuration
   - Database URLs
   - API keys loading
   - Settings validation

2. **security.py** ✓
   - JWT token creation/validation
   - Password hashing (bcrypt)
   - Role-based access control
   - CORS configuration

3. **models/user.py** ✓
   - User table schema
   - UserRole enum (student, instructor, admin)
   - Profile relationships
   - Indexes for performance

4. **db/postgres.py** ✓
   - PostgreSQL connection pooling
   - SQLAlchemy session factory
   - Database initialization
   - Migration support

5. **db/mongodb.py** ✓
   - MongoDB connection
   - Collection management
   - Activity logging functions
   - Analytics helpers

6. **schemas/auth.py** ✓
   - Request/response models
   - Validation rules
   - User registration schema
   - Login schema

7. **api/v1/auth/service.py** ✓
   - User registration logic
   - Login & token generation
   - Admin user creation
   - Profile updates

8. **api/v1/auth/routes.py** ✓
   - POST /api/v1/auth/register - Public registration
   - POST /api/v1/auth/login - Public login
   - POST /api/v1/auth/refresh-token - Token refresh
   - POST /api/v1/auth/admin/create - Admin creation (admin only)

### 🔧 Manual Steps for Phase 1

```bash
# 1. Create project directory structure
mkdir -p kukekodes-backend
cd kukekodes-backend
mkdir -p app/api/v1/{auth,courses,modules,lessons,progress,enrollments}
mkdir -p app/{models,schemas,services,db,utils,middleware}
mkdir -p tests

# 2. Copy all files from the provided code

# 3. Create virtual environment
python -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup PostgreSQL
# Create database in Supabase or local PostgreSQL
createdb kukekodes

# 6. Create .env file
cp .env.example .env
# Edit .env with your credentials

# 7. Run server
uvicorn app.main:app --reload

# 8. Test endpoints
# Register: POST http://localhost:8000/api/v1/auth/register
# Login: POST http://localhost:8000/api/v1/auth/login
# Create Admin: POST http://localhost:8000/api/v1/auth/admin/create
```

### 📊 Test Admin Authentication

```bash
# 1. Create first admin user (bootstrap)
# For MVP, manually insert into database or create via script:

# Script: create_first_admin.py
from app.db.postgres import SessionLocal
from app.models.user import User, UserRole
from app.security import hash_password

db = SessionLocal()
admin = User(
    email="admin@kukekodes.com",
    password_hash=hash_password("AdminPassword123"),
    first_name="Admin",
    last_name="User",
    role=UserRole.ADMIN,
    is_active=True,
    is_email_verified=True,
)
db.add(admin)
db.commit()
print("Admin created successfully")

# 2. Login as admin
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@kukekodes.com",
    "password": "AdminPassword123"
  }'

# Save the access_token from response
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 3. Verify admin access
curl http://localhost:8000/api/v1/courses \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

## Phase 2: Course Creation & Management (Week 2)

### ✅ Completed Files

1. **models/course.py** ✓
   - Course table (title, description, status, instructor_id)
   - Module table (order, course_id)
   - Lesson table (youtube_url, duration, thumbnail_url)
   - All relationships and indexes

2. **services/youtube_service.py** ✓
   - Extract video ID from URL
   - Fetch video metadata (duration, thumbnail)
   - Parse ISO 8601 duration format
   - Fallback if API unavailable

3. **schemas/course.py** ✓
   - CourseCreateRequest
   - ModuleCreateRequest
   - LessonCreateRequest
   - All response models with pagination

4. **api/v1/courses/service.py** ✓
   - create_course() - Draft status
   - create_module() - Under course
   - create_lesson() - With YouTube validation
   - publish_course() - Validate structure
   - get_course_preview() - Show structure before publish

5. **api/v1/courses/routes.py** ✓
   - POST /api/v1/courses - Create course
   - GET /api/v1/courses - List published courses
   - GET /api/v1/courses/{id} - Course details
   - PUT /api/v1/courses/{id} - Update (draft only)
   - DELETE /api/v1/courses/{id} - Delete (draft only)
   - POST /api/v1/courses/{id}/publish - Publish course
   - GET /api/v1/courses/{id}/preview - Preview structure
   - POST /api/v1/modules - Create module
   - GET /api/v1/modules/{id} - Module details
   - PUT /api/v1/modules/{id} - Update module
   - DELETE /api/v1/modules/{id} - Delete module
   - POST /api/v1/lessons - Create lesson with YouTube
   - GET /api/v1/lessons/{id} - Lesson details
   - PUT /api/v1/lessons/{id} - Update lesson
   - DELETE /api/v1/lessons/{id} - Delete lesson

### 🔧 Manual Steps for Phase 2

```bash
# 1. Verify files are in place
# - app/models/course.py
# - app/services/youtube_service.py
# - app/schemas/course.py
# - app/api/v1/courses/service.py
# - app/api/v1/courses/routes.py

# 2. Set YouTube API key in .env
YOUTUBE_API_KEY=your_youtube_api_key_here

# 3. Restart server
# Ctrl+C and run again:
uvicorn app.main:app --reload

# 4. Create course as admin
ACCESS_TOKEN="<from phase 1>"

curl -X POST http://localhost:8000/api/v1/courses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "title": "Python for Beginners",
    "description": "Learn Python fundamentals in 30 days",
    "tags": ["python", "beginner"],
    "skill_level": "beginner",
    "is_free": true
  }'

# Save course_id from response
COURSE_ID="uuid..."

# 5. Create module under course
curl -X POST http://localhost:8000/api/v1/modules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "course_id": "'$COURSE_ID'",
    "title": "Module 1: Getting Started",
    "description": "Introduction to Python basics",
    "order": 1
  }'

# Save module_id
MODULE_ID="uuid..."

# 6. Create lesson with YouTube URL
curl -X POST http://localhost:8000/api/v1/lessons \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "module_id": "'$MODULE_ID'",
    "title": "What is Python?",
    "description": "Learn what Python is and why it matters",
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "order": 1
  }'

# 7. Preview course structure
curl http://localhost:8000/api/v1/courses/$COURSE_ID/preview \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Should return validation errors if incomplete

# 8. Publish course
curl -X POST http://localhost:8000/api/v1/courses/$COURSE_ID/publish \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{}'

# Should return published_at timestamp if successful
```

---

## Phase 3: Student Registration & Learning (Week 3)

### ✅ Completed Files

1. **models/enrollment.py** ✓
   - Enrollment table (user_id, course_id, completion_percentage)
   - UserProgress table (lesson-level tracking)
   - Streak table (current_streak_count, longest_streak_count)

2. **models/badge.py & notification.py** ✓
   - Badge model (criteria, icon_url)
   - Notification model (type, is_read, email_sent)
   - NotificationPreference model

3. **services/email_service.py** ✓
   - WelcomeEmailTemplate
   - LessonCompletedEmailTemplate
   - StreakMilestoneEmailTemplate
   - CourseCompletedEmailTemplate
   - EmailService class with SendGrid integration

4. **routes for progress tracking** (TO BE CREATED)
   - POST /api/v1/enrollments - Enroll in course
   - POST /api/v1/progress/mark-lesson-complete/{lesson_id} - Mark complete
   - GET /api/v1/progress/course/{course_id} - Course progress
   - GET /api/v1/progress/user/dashboard - Dashboard

### 🔧 Manual Steps for Phase 3

```bash
# 1. Set SendGrid API key in .env
SENDGRID_API_KEY=SG.xxxxx
SENDGRID_FROM_EMAIL=noreply@kukekodes.com

# 2. Restart server
uvicorn app.main:app --reload

# 3. Test student registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "StudentPassword123",
    "first_name": "John",
    "last_name": "Doe",
    "country": "Nigeria"
  }'

# Check student@example.com for welcome email

# Save access_token
STUDENT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 4. Enroll in course
curl -X POST http://localhost:8000/api/v1/enrollments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -d '{
    "course_id": "'$COURSE_ID'"
  }'

# 5. Mark lesson complete
curl -X POST http://localhost:8000/api/v1/progress/mark-lesson-complete/<LESSON_ID> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -d '{
    "time_spent_minutes": 12
  }'

# Check student email for lesson completion notification
# In response, should see:
# - lesson_status: "completed"
# - lesson_marked_green: true
# - module_progress: { completed: 1, total: 1 }
# - course_progress: { percentage: 100, completed: 1, total: 1 }
# - badges_earned: ["First Lesson Complete"]
# - streak: 1
```

---

## File Checklist

### Core Configuration
- [ ] app/__init__.py (empty)
- [ ] app/config.py ✓
- [ ] app/security.py ✓
- [ ] app/dependencies.py ✓
- [ ] app/main.py ✓

### Database
- [ ] app/db/__init__.py (empty)
- [ ] app/db/postgres.py ✓
- [ ] app/db/mongodb.py ✓

### Models
- [ ] app/models/__init__.py (empty)
- [ ] app/models/user.py ✓
- [ ] app/models/course.py ✓
- [ ] app/models/enrollment.py ✓
- [ ] app/models/progress.py ✓
- [ ] app/models/badge.py & notification.py ✓
- [ ] app/models/community.py (FOR LATER)

### Schemas
- [ ] app/schemas/__init__.py (empty)
- [ ] app/schemas/auth.py ✓
- [ ] app/schemas/course.py ✓
- [ ] app/schemas/progress.py (FOR LATER)
- [ ] app/schemas/common.py (FOR LATER)

### Services
- [ ] app/services/__init__.py (empty)
- [ ] app/services/email_service.py ✓
- [ ] app/services/youtube_service.py ✓
- [ ] app/services/analytics_service.py (FOR LATER)
- [ ] app/services/cloudinary_service.py (FOR LATER)

### API Routes
- [ ] app/api/__init__.py (empty)
- [ ] app/api/v1/__init__.py (empty)
- [ ] app/api/v1/auth/__init__.py (empty)
- [ ] app/api/v1/auth/routes.py ✓
- [ ] app/api/v1/auth/service.py ✓
- [ ] app/api/v1/auth/schemas.py (use schemas/auth.py)
- [ ] app/api/v1/courses/__init__.py (empty)
- [ ] app/api/v1/courses/routes.py ✓
- [ ] app/api/v1/courses/service.py ✓
- [ ] app/api/v1/courses/schemas.py (use schemas/course.py)
- [ ] app/api/v1/progress/__init__.py (empty)
- [ ] app/api/v1/progress/routes.py (FOR LATER)
- [ ] app/api/v1/progress/service.py (FOR LATER)
- [ ] app/api/v1/enrollments/__init__.py (empty)
- [ ] app/api/v1/enrollments/routes.py (FOR LATER)

### Root Files
- [ ] .env.example ✓
- [ ] requirements.txt ✓
- [ ] README.md ✓
- [ ] IMPLEMENTATION_GUIDE.md (THIS FILE)
- [ ] .gitignore (Create manually)
- [ ] docker-compose.yml (FOR LATER)
- [ ] Dockerfile (FOR LATER)

---

## Important Notes

### File Organization
```
When creating files, ensure:
1. app/api/v1/auth/routes.py imports from app.api.v1.auth.service
2. app/api/v1/auth/service.py imports from app.models and app.security
3. All routes imported in app/main.py
```

### Import Paths
```python
# Correct imports:
from app.config import settings
from app.db.postgres import get_db
from app.security import create_access_token
from app.models.user import User, UserRole
from app.services.email_service import email_service
```

### Database Initialization
```python
# On first run, database tables are created automatically
# If you need to reset:
from app.db.postgres import drop_all_tables, init_db
drop_all_tables()  # CAUTION: Deletes all data
init_db()
```

### Email Testing
```python
# To test SendGrid without real key:
# Set SENDGRID_API_KEY="" (empty)
# Emails will be logged to console instead

# To test with real emails:
# 1. Get SendGrid API key from https://sendgrid.com
# 2. Add to .env
# 3. Verify sender email
```

---

## Next Phases (Not Yet Implemented)

### Phase 4: Progress Tracking & Notifications
- Enrollment endpoints
- Progress tracking
- Streak system
- Badge earning logic
- Email notifications on events

### Phase 5: Community & Gamification
- Forum threads and replies
- Discussion endpoints
- Leaderboard
- XP system
- Badge showcase

### Phase 6: Admin Dashboard
- Analytics endpoints
- Course statistics
- User management
- Reports and exports

### Phase 7: AI Coach
- Gemini API integration
- Context-aware prompts
- Code debugging
- Tutor/debugger/mentor modes

---

## Troubleshooting

### ModuleNotFoundError: No module named 'app'
**Solution**: Ensure you're running from project root and using virtual environment

### PostgreSQL Connection Refused
**Solution**: 
1. Check DATABASE_URL in .env
2. Ensure PostgreSQL is running
3. For Supabase: copy correct connection string from project settings

### YouTube API Errors
**Solution**:
1. Verify YOUTUBE_API_KEY is correct
2. Check API is enabled in Google Cloud Console
3. Check quota hasn't been exceeded

### SendGrid Email Not Sending
**Solution**:
1. Verify SENDGRID_API_KEY
2. Check sender email is verified
3. Check recipient email is valid
4. Check email logs in SendGrid dashboard

---

## Testing Checklist

### Phase 1 Tests
- [ ] Register new user
- [ ] User receives welcome email
- [ ] Login with correct password fails with wrong password
- [ ] Access protected route without token returns 401
- [ ] Create admin user (admin only)
- [ ] Refresh token generates new access token

### Phase 2 Tests
- [ ] Create course (admin only)
- [ ] Regular student cannot create course
- [ ] Add module to course
- [ ] Add lesson with YouTube URL
- [ ] YouTube metadata is fetched and stored
- [ ] Preview course shows validation
- [ ] Publish course (validates structure)
- [ ] Cannot publish incomplete course
- [ ] Published course is visible to students

### Phase 3 Tests
- [ ] Student enrolls in course
- [ ] Student cannot enroll twice
- [ ] Mark lesson complete updates progress
- [ ] Progress tracking shows green checkmarks
- [ ] Email sent on lesson completion
- [ ] Streak increments on consecutive days
- [ ] Badges earned on milestones

---

## Performance Notes

- **Database Queries**: Ensure you're using `.first()` not `.all()` where possible
- **Email Sending**: Send async to avoid blocking requests
- **YouTube API**: Cache metadata to avoid repeated calls
- **List Pagination**: Always implement pagination for large datasets
- **Indexes**: Database models have indexes for common queries

---

## Security Reminders

1. **Never commit .env file** - Add to .gitignore
2. **Change JWT_SECRET in production** - Use strong random value
3. **Use HTTPS in production** - Not http://
4. **Enable CORS for your domain only** - Not "*"
5. **Rate limiting enabled** - Check settings
6. **Log failed login attempts** - For security monitoring
7. **Rotate API keys regularly** - SendGrid, YouTube, etc.

---

## Next Steps

1. Create project directory and copy all files
2. Set up PostgreSQL (Supabase)
3. Set up MongoDB (Atlas)
4. Create .env file with API keys
5. Install dependencies with pip
6. Run `uvicorn app.main:app --reload`
7. Test authentication endpoints
8. Test course creation workflow
9. Test student enrollment and progress tracking
10. Deploy to Railway/Heroku

---
