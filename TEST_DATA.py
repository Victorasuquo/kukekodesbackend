"""
FastAPI Test Data & Examples
Testing guide with curl commands and JSON payloads for all endpoints
"""

# ============================================================================
# HEALTH CHECK & ROOT ENDPOINTS
# ============================================================================

# GET /health
# Response: 200 OK
# curl -X GET http://localhost:8000/health

# GET /
# Response: 200 OK
# curl -X GET http://localhost:8000/

# Expected Response:
"""
{
  "message": "Welcome to Kukekodes Learning Platform API",
  "version": "1.0.0",
  "docs": "http://localhost:8000/docs"
}
"""


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

# 1. POST /api/v1/auth/register - Register new user
# curl -X POST http://localhost:8000/api/v1/auth/register \
#   -H "Content-Type: application/json" \
#   -d '{
#     "email": "john.doe@example.com",
#     "password": "SecurePass123",
#     "first_name": "John",
#     "last_name": "Doe",
#     "country": "Nigeria"
#   }'

REGISTER_REQUEST = {
    "email": "john.doe@example.com",
    "password": "SecurePass123",
    "first_name": "John",
    "last_name": "Doe",
    "country": "Nigeria"
}

# Expected Response: 201 CREATED
REGISTER_RESPONSE = {
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "username": None,
        "profile_picture_url": None,
        "country": "Nigeria",
        "role": "student",
        "is_active": True,
        "created_at": "2026-01-15T16:30:00"
    },
    "token": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 900
    },
    "message": "User registered successfully"
}


# 2. POST /api/v1/auth/login - Login user
# curl -X POST http://localhost:8000/api/v1/auth/login \
#   -H "Content-Type: application/json" \
#   -d '{
#     "email": "john.doe@example.com",
#     "password": "SecurePass123"
#   }'

LOGIN_REQUEST = {
    "email": "john.doe@example.com",
    "password": "SecurePass123"
}

# Expected Response: 200 OK
LOGIN_RESPONSE = {
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "student",
        "is_active": True
    },
    "token": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 900
    },
    "message": "Login successful"
}


# 3. POST /api/v1/auth/refresh-token - Refresh access token
# curl -X POST http://localhost:8000/api/v1/auth/refresh-token \
#   -H "Content-Type: application/json" \
#   -d '{
#     "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
#   }'

REFRESH_TOKEN_REQUEST = {
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

# Expected Response: 200 OK
REFRESH_TOKEN_RESPONSE = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 900
}


# 4. POST /api/v1/auth/admin/create - Create admin user (admin only)
# curl -X POST http://localhost:8000/api/v1/auth/admin/create \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
#   -d '{
#     "email": "admin@kukekodes.com",
#     "password": "AdminPass123",
#     "first_name": "Admin",
#     "last_name": "User"
#   }'

ADMIN_CREATE_REQUEST = {
    "email": "admin@kukekodes.com",
    "password": "AdminPass123",
    "first_name": "Admin",
    "last_name": "User"
}

# Expected Response: 201 CREATED
ADMIN_CREATE_RESPONSE = {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "email": "admin@kukekodes.com",
    "first_name": "Admin",
    "last_name": "User",
    "role": "admin",
    "is_active": True,
    "created_at": "2026-01-15T16:35:00"
}


# 5. POST /api/v1/auth/logout - Logout user
# curl -X POST http://localhost:8000/api/v1/auth/logout \
#   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Expected Response: 200 OK
LOGOUT_RESPONSE = {
    "success": True,
    "message": "Logged out successfully"
}


# ============================================================================
# COURSES ENDPOINTS
# ============================================================================

# 1. POST /api/v1/courses - Create course (instructor/admin only)
# curl -X POST http://localhost:8000/api/v1/courses \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
#   -d '{
#     "title": "Python Basics for Beginners",
#     "description": "Learn the fundamentals of Python programming from scratch...",
#     "tags": ["Python", "Programming", "Beginner", "Backend"],
#     "skill_level": "beginner",
#     "category": "Programming",
#     "is_free": true
#   }'

CREATE_COURSE_REQUEST = {
    "title": "Python Basics for Beginners",
    "description": "Learn the fundamentals of Python programming from scratch. This comprehensive course covers variables, functions, loops, and more.",
    "tags": ["Python", "Programming", "Beginner", "Backend"],
    "skill_level": "beginner",
    "category": "Programming",
    "is_free": "True"
}

# Expected Response: 201 CREATED
CREATE_COURSE_RESPONSE = {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "title": "Python Basics for Beginners",
    "description": "Learn the fundamentals of Python programming from scratch...",
    "tags": ["Python", "Programming", "Beginner", "Backend"],
    "skill_level": "beginner",
    "category": "Programming",
    "instructor_id": "550e8400-e29b-41d4-a716-446655440002",
    "status": "draft",
    "is_free": True,
    "total_enrollments": 0,
    "created_at": "2026-01-15T16:40:00",
    "published_at": None
}


# 2. GET /api/v1/courses - List courses (paginated)
# curl -X GET "http://localhost:8000/api/v1/courses?page=1&page_size=10&skill_level=beginner"

# Expected Response: 200 OK
LIST_COURSES_RESPONSE = {
    "data": [
        {
            "id": "660e8400-e29b-41d4-a716-446655440000",
            "title": "Python Basics for Beginners",
            "description": "Learn Python fundamentals...",
            "tags": ["Python", "Programming"],
            "skill_level": "beginner",
            "category": "Programming",
            "instructor_id": "550e8400-e29b-41d4-a716-446655440002",
            "status": "published",
            "is_free": True,
            "total_enrollments": 156,
            "created_at": "2026-01-15T16:40:00",
            "published_at": "2026-01-15T17:00:00"
        },
        {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "title": "Advanced Python: OOP & Design Patterns",
            "description": "Master advanced Python concepts...",
            "tags": ["Python", "OOP"],
            "skill_level": "advanced",
            "category": "Programming",
            "instructor_id": "550e8400-e29b-41d4-a716-446655440002",
            "status": "published",
            "is_free": False,
            "total_enrollments": 89,
            "created_at": "2026-01-14T10:20:00",
            "published_at": "2026-01-14T11:00:00"
        }
    ],
    "meta": {
        "total": 45,
        "page": 1,
        "page_size": 10,
        "total_pages": 5
    }
}


# 3. GET /api/v1/courses/{course_id} - Get course details
# curl -X GET http://localhost:8000/api/v1/courses/660e8400-e29b-41d4-a716-446655440000

# Expected Response: 200 OK
GET_COURSE_RESPONSE = {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "title": "Python Basics for Beginners",
    "description": "Learn the fundamentals of Python programming...",
    "tags": ["Python", "Programming", "Beginner"],
    "skill_level": "beginner",
    "category": "Programming",
    "instructor_id": "550e8400-e29b-41d4-a716-446655440002",
    "status": "published",
    "is_free": True,
    "cover_image_url": "https://res.cloudinary.com/...",
    "thumbnail_url": "https://res.cloudinary.com/...",
    "is_featured": True,
    "average_rating": "4.8",
    "total_reviews": 234,
    "total_enrollments": 156,
    "total_estimated_hours": 12,
    "modules": [
        {
            "id": "770e8400-e29b-41d4-a716-446655440000",
            "course_id": "660e8400-e29b-41d4-a716-446655440000",
            "title": "Module 1: Python Basics",
            "description": "Introduction to Python syntax and fundamentals",
            "order": 1,
            "lessons": [
                {
                    "id": "880e8400-e29b-41d4-a716-446655440000",
                    "module_id": "770e8400-e29b-41d4-a716-446655440000",
                    "title": "What is Python?",
                    "description": "Introduction to Python",
                    "youtube_url": "https://www.youtube.com/watch?v=...",
                    "youtube_video_id": "dQw4w9WgXcQ",
                    "duration_minutes": 15,
                    "thumbnail_url": "https://i.ytimg.com/...",
                    "order": 1,
                    "status": "published",
                    "created_at": "2026-01-15T16:45:00"
                },
                {
                    "id": "880e8400-e29b-41d4-a716-446655440001",
                    "module_id": "770e8400-e29b-41d4-a716-446655440000",
                    "title": "Setting up your environment",
                    "description": "Install Python and set up IDE",
                    "youtube_url": "https://www.youtube.com/watch?v=...",
                    "youtube_video_id": "AbCdEfGhI1j",
                    "duration_minutes": 20,
                    "thumbnail_url": "https://i.ytimg.com/...",
                    "order": 2,
                    "status": "published",
                    "created_at": "2026-01-15T16:46:00"
                }
            ],
            "created_at": "2026-01-15T16:45:00"
        }
    ],
    "created_at": "2026-01-15T16:40:00",
    "published_at": "2026-01-15T17:00:00"
}


# 4. PUT /api/v1/courses/{course_id} - Update course
# curl -X PUT http://localhost:8000/api/v1/courses/660e8400-e29b-41d4-a716-446655440000 \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
#   -d '{
#     "title": "Python Basics for Complete Beginners",
#     "description": "Updated description...",
#     "tags": ["Python", "Programming", "Beginner"],
#     "is_featured": true
#   }'

UPDATE_COURSE_REQUEST = {
    "title": "Python Basics for Complete Beginners",
    "description": "Updated comprehensive guide to Python fundamentals...",
    "tags": ["Python", "Programming", "Beginner", "Web"],
    "is_featured": True
}

# Expected Response: 200 OK
UPDATE_COURSE_RESPONSE = {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "title": "Python Basics for Complete Beginners",
    "description": "Updated comprehensive guide...",
    "tags": ["Python", "Programming", "Beginner", "Web"],
    "is_featured": True,
    "status": "published",
    "message": "Course updated successfully"
}


# 5. DELETE /api/v1/courses/{course_id} - Delete course
# curl -X DELETE http://localhost:8000/api/v1/courses/660e8400-e29b-41d4-a716-446655440000 \
#   -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN"

# Expected Response: 200 OK
DELETE_COURSE_RESPONSE = {
    "success": True,
    "message": "Course deleted successfully"
}


# 6. GET /api/v1/courses/{course_id}/preview - Preview course
# curl -X GET http://localhost:8000/api/v1/courses/660e8400-e29b-41d4-a716-446655440000/preview

# Expected Response: 200 OK
COURSE_PREVIEW_RESPONSE = {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "title": "Python Basics for Beginners",
    "description": "Learn Python fundamentals...",
    "modules_count": 5,
    "lessons_count": 24,
    "total_duration_minutes": 720,
    "status": "draft",
    "is_publishable": True,
    "validation_errors": []
}


# 7. POST /api/v1/courses/{course_id}/publish - Publish course
# curl -X POST http://localhost:8000/api/v1/courses/660e8400-e29b-41d4-a716-446655440000/publish \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
#   -d '{}'

# Expected Response: 200 OK
PUBLISH_COURSE_RESPONSE = {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "title": "Python Basics for Beginners",
    "status": "published",
    "published_at": "2026-01-15T17:30:00",
    "message": "Course published successfully"
}


# ============================================================================
# MODULES ENDPOINTS
# ============================================================================

# 1. POST /api/v1/modules - Create module
# curl -X POST http://localhost:8000/api/v1/modules \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
#   -d '{
#     "course_id": "660e8400-e29b-41d4-a716-446655440000",
#     "title": "Module 2: Variables & Data Types",
#     "description": "Learn about Python variables and data types",
#     "order": 2
#   }'

CREATE_MODULE_REQUEST = {
    "course_id": "660e8400-e29b-41d4-a716-446655440000",
    "title": "Module 2: Variables & Data Types",
    "description": "Learn about Python variables, data types, and type conversion",
    "order": 2
}

# Expected Response: 201 CREATED
CREATE_MODULE_RESPONSE = {
    "id": "770e8400-e29b-41d4-a716-446655440001",
    "course_id": "660e8400-e29b-41d4-a716-446655440000",
    "title": "Module 2: Variables & Data Types",
    "description": "Learn about Python variables, data types, and type conversion",
    "order": 2,
    "lessons": [],
    "created_at": "2026-01-15T17:35:00"
}


# 2. GET /api/v1/modules/{module_id} - Get module
# curl -X GET http://localhost:8000/api/v1/modules/770e8400-e29b-41d4-a716-446655440001

# Expected Response: 200 OK
GET_MODULE_RESPONSE = {
    "id": "770e8400-e29b-41d4-a716-446655440001",
    "course_id": "660e8400-e29b-41d4-a716-446655440000",
    "title": "Module 2: Variables & Data Types",
    "description": "Learn about Python variables and data types",
    "order": 2,
    "lessons": [
        {
            "id": "880e8400-e29b-41d4-a716-446655440002",
            "module_id": "770e8400-e29b-41d4-a716-446655440001",
            "title": "Variables in Python",
            "description": "Understanding Python variables",
            "youtube_url": "https://www.youtube.com/watch?v=...",
            "youtube_video_id": "xyz123",
            "duration_minutes": 18,
            "order": 1,
            "status": "published"
        }
    ],
    "created_at": "2026-01-15T17:35:00"
}


# 3. PUT /api/v1/modules/{module_id} - Update module
# curl -X PUT http://localhost:8000/api/v1/modules/770e8400-e29b-41d4-a716-446655440001 \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
#   -d '{
#     "title": "Module 2: Python Variables & Data Types (Updated)",
#     "order": 3
#   }'

UPDATE_MODULE_REQUEST = {
    "title": "Module 2: Python Variables & Data Types (Updated)",
    "description": "Comprehensive guide to variables and data types",
    "order": 3
}

# Expected Response: 200 OK
UPDATE_MODULE_RESPONSE = {
    "id": "770e8400-e29b-41d4-a716-446655440001",
    "course_id": "660e8400-e29b-41d4-a716-446655440000",
    "title": "Module 2: Python Variables & Data Types (Updated)",
    "description": "Comprehensive guide to variables and data types",
    "order": 3,
    "message": "Module updated successfully"
}


# 4. DELETE /api/v1/modules/{module_id} - Delete module
# curl -X DELETE http://localhost:8000/api/v1/modules/770e8400-e29b-41d4-a716-446655440001 \
#   -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN"

# Expected Response: 200 OK
DELETE_MODULE_RESPONSE = {
    "success": True,
    "message": "Module deleted successfully"
}


# ============================================================================
# LESSONS ENDPOINTS
# ============================================================================

# 1. POST /api/v1/lessons - Create lesson
# curl -X POST http://localhost:8000/api/v1/lessons \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
#   -d '{
#     "module_id": "770e8400-e29b-41d4-a716-446655440001",
#     "title": "Understanding Python Variables",
#     "description": "Deep dive into Python variables and naming conventions",
#     "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
#     "order": 1
#   }'

CREATE_LESSON_REQUEST = {
    "module_id": "770e8400-e29b-41d4-a716-446655440001",
    "title": "Understanding Python Variables",
    "description": "Deep dive into Python variables and naming conventions",
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "order": 1
}

# Expected Response: 201 CREATED
CREATE_LESSON_RESPONSE = {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "module_id": "770e8400-e29b-41d4-a716-446655440001",
    "title": "Understanding Python Variables",
    "description": "Deep dive into Python variables",
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "youtube_video_id": "dQw4w9WgXcQ",
    "duration_minutes": 24,
    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "order": 1,
    "status": "published",
    "created_at": "2026-01-15T17:40:00"
}


# 2. GET /api/v1/lessons/{lesson_id} - Get lesson
# curl -X GET http://localhost:8000/api/v1/lessons/880e8400-e29b-41d4-a716-446655440003

# Expected Response: 200 OK
GET_LESSON_RESPONSE = {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "module_id": "770e8400-e29b-41d4-a716-446655440001",
    "title": "Understanding Python Variables",
    "description": "Deep dive into Python variables",
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "youtube_video_id": "dQw4w9WgXcQ",
    "duration_minutes": 24,
    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "transcript": "Welcome to this lesson on Python variables...",
    "resources": {
        "code_examples": "https://github.com/.../variables.py",
        "exercise": "https://example.com/exercise"
    },
    "order": 1,
    "status": "published",
    "created_at": "2026-01-15T17:40:00"
}


# 3. PUT /api/v1/lessons/{lesson_id} - Update lesson
# curl -X PUT http://localhost:8000/api/v1/lessons/880e8400-e29b-41d4-a716-446655440003 \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
#   -d '{
#     "title": "Mastering Python Variables",
#     "youtube_url": "https://www.youtube.com/watch?v=newVideoId"
#   }'

UPDATE_LESSON_REQUEST = {
    "title": "Mastering Python Variables",
    "description": "Advanced guide to Python variables and scoping",
    "youtube_url": "https://www.youtube.com/watch?v=newVideoId"
}

# Expected Response: 200 OK
UPDATE_LESSON_RESPONSE = {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "module_id": "770e8400-e29b-41d4-a716-446655440001",
    "title": "Mastering Python Variables",
    "description": "Advanced guide to Python variables and scoping",
    "youtube_video_id": "newVideoId",
    "duration_minutes": 28,
    "order": 1,
    "status": "published",
    "message": "Lesson updated successfully"
}


# 4. DELETE /api/v1/lessons/{lesson_id} - Delete lesson
# curl -X DELETE http://localhost:8000/api/v1/lessons/880e8400-e29b-41d4-a716-446655440003 \
#   -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN"

# Expected Response: 200 OK
DELETE_LESSON_RESPONSE = {
    "success": True,
    "message": "Lesson deleted successfully"
}


# ============================================================================
# TESTING WORKFLOW
# ============================================================================

"""
RECOMMENDED TESTING WORKFLOW:

1. Health Check:
   GET /health
   GET /

2. Authentication:
   POST /api/v1/auth/register (creates student account)
   POST /api/v1/auth/login (get tokens)
   
   For admin endpoints, you'll need instructor/admin token:
   POST /api/v1/auth/admin/create (admin only)

3. Create Course Content:
   POST /api/v1/courses (create course)
   POST /api/v1/modules (add module to course)
   POST /api/v1/lessons (add lessons to module)
   
4. Preview & Publish:
   GET /api/v1/courses/{id}/preview (check if ready)
   POST /api/v1/courses/{id}/publish (publish course)

5. View Published Content:
   GET /api/v1/courses (list all)
   GET /api/v1/courses/{id} (course details)
   GET /api/v1/modules/{id} (module details)
   GET /api/v1/lessons/{id} (lesson details)

6. Cleanup:
   DELETE /api/v1/lessons/{id}
   DELETE /api/v1/modules/{id}
   DELETE /api/v1/courses/{id}

IMPORTANT NOTES:
- Replace YOUR_INSTRUCTOR_TOKEN with actual access token from login
- Replace YOUR_ADMIN_TOKEN with admin's access token
- For updates and deletes, use PUT/DELETE methods
- All timestamps are ISO 8601 format
- UUIDs in examples are placeholders - actual IDs will differ
"""
