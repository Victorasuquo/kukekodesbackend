# Kukekodes API Testing Guide

## Quick Start - Test All Endpoints

### Prerequisites
- App running: `uvicorn app.main:app --reload`
- Base URL: `http://localhost:8000`

---

## 1. HEALTH CHECK & ROOT

### GET /health
**Status Check**
```bash
curl -X GET http://localhost:8000/health
```

### GET /
**Welcome Message**
```bash
curl -X GET http://localhost:8000/
```

---

## 2. AUTHENTICATION FLOW

### Step 1: Register New User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "SecurePass123",
    "first_name": "Jane",
    "last_name": "Smith",
    "country": "Nigeria"
  }'
```

**Save the `access_token` and `refresh_token` from response!**

### Step 2: Login User
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "SecurePass123"
  }'
```

### Step 3: Refresh Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh-token \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN_HERE"
  }'
```

### Step 4: Create Admin User (Admin Only)
```bash
curl -X POST http://localhost:8000/api/v1/auth/admin/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "email": "instructor@kukekodes.com",
    "password": "InstructorPass123",
    "first_name": "John",
    "last_name": "Instructor"
  }'
```

### Step 5: Logout
```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 3. COURSES MANAGEMENT

### Create Course (Instructor/Admin Only)
```bash
curl -X POST http://localhost:8000/api/v1/courses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
  -d '{
    "title": "Python Basics for Beginners",
    "description": "Comprehensive guide to learning Python programming from scratch. Perfect for beginners with no prior coding experience.",
    "tags": ["Python", "Programming", "Beginner"],
    "skill_level": "beginner",
    "category": "Programming",
    "is_free": true
  }'
```

**Response includes `course_id` - Save this!**

### List All Courses
```bash
curl -X GET "http://localhost:8000/api/v1/courses?page=1&page_size=10"
```

### Get Course Details
```bash
curl -X GET http://localhost:8000/api/v1/courses/YOUR_COURSE_ID
```

### Update Course
```bash
curl -X PUT http://localhost:8000/api/v1/courses/YOUR_COURSE_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
  -d '{
    "title": "Python Basics for Complete Beginners",
    "tags": ["Python", "Programming", "Beginner", "Web"],
    "is_featured": true
  }'
```

### Preview Course (Check if publishable)
```bash
curl -X GET http://localhost:8000/api/v1/courses/YOUR_COURSE_ID/preview
```

### Publish Course
```bash
curl -X POST http://localhost:8000/api/v1/courses/YOUR_COURSE_ID/publish \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
  -d '{}'
```

### Delete Course
```bash
curl -X DELETE http://localhost:8000/api/v1/courses/YOUR_COURSE_ID \
  -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN"
```

---

## 4. MODULES MANAGEMENT

### Create Module in Course
```bash
curl -X POST http://localhost:8000/api/v1/modules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
  -d '{
    "course_id": "YOUR_COURSE_ID",
    "title": "Module 1: Python Basics",
    "description": "Learn Python fundamentals including variables, data types, and control flow",
    "order": 1
  }'
```

**Save the `module_id` from response!**

### Get Module Details
```bash
curl -X GET http://localhost:8000/api/v1/modules/YOUR_MODULE_ID
```

### Update Module
```bash
curl -X PUT http://localhost:8000/api/v1/modules/YOUR_MODULE_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
  -d '{
    "title": "Module 1: Python Fundamentals",
    "order": 1
  }'
```

### Delete Module
```bash
curl -X DELETE http://localhost:8000/api/v1/modules/YOUR_MODULE_ID \
  -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN"
```

---

## 5. LESSONS MANAGEMENT

### Create Lesson in Module
```bash
curl -X POST http://localhost:8000/api/v1/lessons \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
  -d '{
    "module_id": "YOUR_MODULE_ID",
    "title": "What is Python?",
    "description": "Introduction to Python programming language and its applications",
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "order": 1
  }'
```

**Save the `lesson_id` from response!**

### Get Lesson Details
```bash
curl -X GET http://localhost:8000/api/v1/lessons/YOUR_LESSON_ID
```

### Update Lesson
```bash
curl -X PUT http://localhost:8000/api/v1/lessons/YOUR_LESSON_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN" \
  -d '{
    "title": "Introduction to Python",
    "youtube_url": "https://www.youtube.com/watch?v=newVideoId"
  }'
```

### Delete Lesson
```bash
curl -X DELETE http://localhost:8000/api/v1/lessons/YOUR_LESSON_ID \
  -H "Authorization: Bearer YOUR_INSTRUCTOR_TOKEN"
```

---

## 6. COMPLETE TESTING WORKFLOW

### Phase 1: Setup & Authentication
```bash
# 1. Register a student
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test.student@example.com",
    "password": "TestPass123",
    "first_name": "Test",
    "last_name": "Student",
    "country": "Nigeria"
  }'
# Save: access_token → STUDENT_TOKEN, refresh_token → STUDENT_REFRESH

# 2. Register/Create an instructor (if needed)
# Use admin credentials or create through admin endpoint
```

### Phase 2: Course Creation
```bash
# 1. Create Course
COURSE_ID=$(curl -s -X POST http://localhost:8000/api/v1/courses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer INSTRUCTOR_TOKEN" \
  -d '{
    "title": "Complete Python Course",
    "description": "Learn Python from scratch",
    "tags": ["Python"],
    "skill_level": "beginner",
    "is_free": true
  }' | jq -r '.id')

# 2. Create Module
MODULE_ID=$(curl -s -X POST http://localhost:8000/api/v1/modules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer INSTRUCTOR_TOKEN" \
  -d "{
    \"course_id\": \"$COURSE_ID\",
    \"title\": \"Module 1: Getting Started\",
    \"description\": \"Setup and basics\",
    \"order\": 1
  }" | jq -r '.id')

# 3. Create Lesson
LESSON_ID=$(curl -s -X POST http://localhost:8000/api/v1/lessons \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer INSTRUCTOR_TOKEN" \
  -d "{
    \"module_id\": \"$MODULE_ID\",
    \"title\": \"Lesson 1: Hello World\",
    \"description\": \"Your first Python program\",
    \"youtube_url\": \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\",
    \"order\": 1
  }" | jq -r '.id')

# 4. View Course Preview
curl -X GET http://localhost:8000/api/v1/courses/$COURSE_ID/preview \
  -H "Authorization: Bearer INSTRUCTOR_TOKEN"

# 5. Publish Course
curl -X POST http://localhost:8000/api/v1/courses/$COURSE_ID/publish \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer INSTRUCTOR_TOKEN" \
  -d '{}'
```

### Phase 3: Student Access
```bash
# 1. List published courses
curl -X GET "http://localhost:8000/api/v1/courses?page=1&page_size=20"

# 2. Student views course details
curl -X GET http://localhost:8000/api/v1/courses/$COURSE_ID \
  -H "Authorization: Bearer STUDENT_TOKEN"

# 3. View module details
curl -X GET http://localhost:8000/api/v1/modules/$MODULE_ID \
  -H "Authorization: Bearer STUDENT_TOKEN"

# 4. View lesson details
curl -X GET http://localhost:8000/api/v1/lessons/$LESSON_ID \
  -H "Authorization: Bearer STUDENT_TOKEN"
```

### Phase 4: Cleanup
```bash
# 1. Delete Lesson
curl -X DELETE http://localhost:8000/api/v1/lessons/$LESSON_ID \
  -H "Authorization: Bearer INSTRUCTOR_TOKEN"

# 2. Delete Module
curl -X DELETE http://localhost:8000/api/v1/modules/$MODULE_ID \
  -H "Authorization: Bearer INSTRUCTOR_TOKEN"

# 3. Delete Course
curl -X DELETE http://localhost:8000/api/v1/courses/$COURSE_ID \
  -H "Authorization: Bearer INSTRUCTOR_TOKEN"
```

---

## 7. TESTING WITH POSTMAN

1. **Import Collection**: Create a new Postman collection
2. **Set Variables**:
   - `base_url`: `http://localhost:8000`
   - `student_token`: (from register/login response)
   - `instructor_token`: (from instructor login)
   - `course_id`: (from create course response)
   - `module_id`: (from create module response)
   - `lesson_id`: (from create lesson response)

3. **Use Variables in URLs**:
   - `{{base_url}}/api/v1/courses`
   - `{{base_url}}/api/v1/courses/{{course_id}}`

4. **Headers**:
   - `Authorization: Bearer {{student_token}}`

---

## 8. ERROR RESPONSES

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```
**Fix**: Add valid token in Authorization header

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions for this action"
}
```
**Fix**: Use instructor/admin token for course management

### 404 Not Found
```json
{
  "detail": "Course not found"
}
```
**Fix**: Verify correct course_id

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "ensure this value has at least 3 characters",
      "type": "value_error.string.min_length"
    }
  ]
}
```
**Fix**: Check field requirements and validation rules

---

## 9. TIPS FOR TESTING

✅ **Always test in order**: Register → Login → Create content → Publish → View → Delete

✅ **Save IDs**: Keep course_id, module_id, lesson_id for follow-up requests

✅ **Use jq**: Parse JSON responses easily: `curl ... | jq '.id'`

✅ **Check logs**: Monitor app logs for errors and debug info

✅ **Test authorization**: Try requests without tokens to verify 401 responses

✅ **Test validation**: Send invalid data to verify error handling

✅ **Test pagination**: Use page and page_size parameters

---

## 10. COMMON ISSUES & FIXES

| Issue | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Missing/expired token | Login again and get new token |
| 403 Forbidden | Wrong role | Use appropriate user role token |
| 404 Not Found | Invalid ID | Verify ID exists and is correct |
| 422 Validation | Invalid data | Check field types and constraints |
| 500 Server Error | Unexpected error | Check app logs, report issue |

---

**Happy Testing! 🚀**
