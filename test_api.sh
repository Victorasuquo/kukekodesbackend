#!/bin/bash
# Quick API Testing Script for Kukekodes Backend
# Save as: test_api.sh and run: bash test_api.sh

BASE_URL="http://localhost:8000"
STUDENT_EMAIL="student.$(date +%s)@example.com"
INSTRUCTOR_EMAIL="instructor.$(date +%s)@example.com"

echo "========================================"
echo "Kukekodes API Testing Script"
echo "========================================"
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# 1. HEALTH CHECK
# ============================================================================
echo -e "${BLUE}1. Health Check${NC}"
curl -s -X GET "$BASE_URL/health" | jq .
echo ""

# ============================================================================
# 2. ROOT ENDPOINT
# ============================================================================
echo -e "${BLUE}2. Root Endpoint${NC}"
curl -s -X GET "$BASE_URL/" | jq .
echo ""

# ============================================================================
# 3. REGISTER STUDENT
# ============================================================================
echo -e "${BLUE}3. Register Student${NC}"
echo "Email: $STUDENT_EMAIL"
STUDENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$STUDENT_EMAIL\",
    \"password\": \"SecurePass123\",
    \"first_name\": \"Test\",
    \"last_name\": \"Student\",
    \"country\": \"Nigeria\"
  }")

echo "$STUDENT_RESPONSE" | jq .

# Extract tokens
STUDENT_ACCESS_TOKEN=$(echo "$STUDENT_RESPONSE" | jq -r '.token.access_token')
STUDENT_REFRESH_TOKEN=$(echo "$STUDENT_RESPONSE" | jq -r '.token.refresh_token')
STUDENT_ID=$(echo "$STUDENT_RESPONSE" | jq -r '.user.id')

echo -e "${GREEN}✓ Student Access Token: ${STUDENT_ACCESS_TOKEN:0:20}...${NC}"
echo ""

# ============================================================================
# 4. REGISTER INSTRUCTOR
# ============================================================================
echo -e "${BLUE}4. Register Instructor${NC}"
echo "Email: $INSTRUCTOR_EMAIL"
INSTRUCTOR_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$INSTRUCTOR_EMAIL\",
    \"password\": \"InstructorPass123\",
    \"first_name\": \"Instructor\",
    \"last_name\": \"User\",
    \"country\": \"Nigeria\"
  }")

echo "$INSTRUCTOR_RESPONSE" | jq .

INSTRUCTOR_ACCESS_TOKEN=$(echo "$INSTRUCTOR_RESPONSE" | jq -r '.token.access_token')
INSTRUCTOR_ID=$(echo "$INSTRUCTOR_RESPONSE" | jq -r '.user.id')

echo -e "${GREEN}✓ Instructor Access Token: ${INSTRUCTOR_ACCESS_TOKEN:0:20}...${NC}"
echo ""

# ============================================================================
# 5. LOGIN STUDENT
# ============================================================================
echo -e "${BLUE}5. Login Student${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$STUDENT_EMAIL\",
    \"password\": \"SecurePass123\"
  }")

echo "$LOGIN_RESPONSE" | jq .
echo ""

# ============================================================================
# 6. CREATE COURSE (Instructor)
# ============================================================================
echo -e "${BLUE}6. Create Course (as Instructor)${NC}"
COURSE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/courses" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $INSTRUCTOR_ACCESS_TOKEN" \
  -d '{
    "title": "Python Basics for Beginners",
    "description": "Learn Python fundamentals including variables, data types, functions, and control flow. Perfect for beginners with no prior coding experience.",
    "tags": ["Python", "Programming", "Beginner"],
    "skill_level": "beginner",
    "category": "Programming",
    "is_free": true
  }')

echo "$COURSE_RESPONSE" | jq .

COURSE_ID=$(echo "$COURSE_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Course ID: $COURSE_ID${NC}"
echo ""

# ============================================================================
# 7. CREATE MODULE (in Course)
# ============================================================================
echo -e "${BLUE}7. Create Module${NC}"
MODULE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/modules" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $INSTRUCTOR_ACCESS_TOKEN" \
  -d "{
    \"course_id\": \"$COURSE_ID\",
    \"title\": \"Module 1: Python Basics\",
    \"description\": \"Learn Python fundamentals\",
    \"order\": 1
  }")

echo "$MODULE_RESPONSE" | jq .

MODULE_ID=$(echo "$MODULE_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Module ID: $MODULE_ID${NC}"
echo ""

# ============================================================================
# 8. CREATE LESSON (in Module)
# ============================================================================
echo -e "${BLUE}8. Create Lesson${NC}"
LESSON_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/lessons" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $INSTRUCTOR_ACCESS_TOKEN" \
  -d "{
    \"module_id\": \"$MODULE_ID\",
    \"title\": \"What is Python?\",
    \"description\": \"Introduction to Python programming\",
    \"youtube_url\": \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\",
    \"order\": 1
  }")

echo "$LESSON_RESPONSE" | jq .

LESSON_ID=$(echo "$LESSON_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Lesson ID: $LESSON_ID${NC}"
echo ""

# ============================================================================
# 9. LIST COURSES (as Student)
# ============================================================================
echo -e "${BLUE}9. List Courses (as Student)${NC}"
curl -s -X GET "$BASE_URL/api/v1/courses?page=1&page_size=10" \
  -H "Authorization: Bearer $STUDENT_ACCESS_TOKEN" | jq .
echo ""

# ============================================================================
# 10. GET COURSE DETAILS
# ============================================================================
echo -e "${BLUE}10. Get Course Details${NC}"
curl -s -X GET "$BASE_URL/api/v1/courses/$COURSE_ID" \
  -H "Authorization: Bearer $STUDENT_ACCESS_TOKEN" | jq .
echo ""

# ============================================================================
# 11. PREVIEW COURSE
# ============================================================================
echo -e "${BLUE}11. Preview Course (check if publishable)${NC}"
curl -s -X GET "$BASE_URL/api/v1/courses/$COURSE_ID/preview" \
  -H "Authorization: Bearer $INSTRUCTOR_ACCESS_TOKEN" | jq .
echo ""

# ============================================================================
# 12. PUBLISH COURSE
# ============================================================================
echo -e "${BLUE}12. Publish Course${NC}"
curl -s -X POST "$BASE_URL/api/v1/courses/$COURSE_ID/publish" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $INSTRUCTOR_ACCESS_TOKEN" \
  -d '{}' | jq .
echo ""

# ============================================================================
# 13. GET MODULE DETAILS
# ============================================================================
echo -e "${BLUE}13. Get Module Details${NC}"
curl -s -X GET "$BASE_URL/api/v1/modules/$MODULE_ID" \
  -H "Authorization: Bearer $STUDENT_ACCESS_TOKEN" | jq .
echo ""

# ============================================================================
# 14. GET LESSON DETAILS
# ============================================================================
echo -e "${BLUE}14. Get Lesson Details${NC}"
curl -s -X GET "$BASE_URL/api/v1/lessons/$LESSON_ID" \
  -H "Authorization: Bearer $STUDENT_ACCESS_TOKEN" | jq .
echo ""

# ============================================================================
# 15. UPDATE LESSON
# ============================================================================
echo -e "${BLUE}15. Update Lesson${NC}"
curl -s -X PUT "$BASE_URL/api/v1/lessons/$LESSON_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $INSTRUCTOR_ACCESS_TOKEN" \
  -d '{
    "title": "Introduction to Python",
    "description": "Updated description of Python introduction"
  }' | jq .
echo ""

# ============================================================================
# 16. UPDATE COURSE
# ============================================================================
echo -e "${BLUE}16. Update Course${NC}"
curl -s -X PUT "$BASE_URL/api/v1/courses/$COURSE_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $INSTRUCTOR_ACCESS_TOKEN" \
  -d '{
    "title": "Python Basics for Complete Beginners",
    "is_featured": true
  }' | jq .
echo ""

# ============================================================================
# 17. DELETE LESSON
# ============================================================================
echo -e "${BLUE}17. Delete Lesson${NC}"
curl -s -X DELETE "$BASE_URL/api/v1/lessons/$LESSON_ID" \
  -H "Authorization: Bearer $INSTRUCTOR_ACCESS_TOKEN" | jq .
echo ""

# ============================================================================
# 18. DELETE MODULE
# ============================================================================
echo -e "${BLUE}18. Delete Module${NC}"
curl -s -X DELETE "$BASE_URL/api/v1/modules/$MODULE_ID" \
  -H "Authorization: Bearer $INSTRUCTOR_ACCESS_TOKEN" | jq .
echo ""

# ============================================================================
# 19. DELETE COURSE
# ============================================================================
echo -e "${BLUE}19. Delete Course${NC}"
curl -s -X DELETE "$BASE_URL/api/v1/courses/$COURSE_ID" \
  -H "Authorization: Bearer $INSTRUCTOR_ACCESS_TOKEN" | jq .
echo ""

# ============================================================================
# LOGOUT
# ============================================================================
echo -e "${BLUE}20. Logout${NC}"
curl -s -X POST "$BASE_URL/api/v1/auth/logout" \
  -H "Authorization: Bearer $STUDENT_ACCESS_TOKEN" | jq .
echo ""

echo -e "${GREEN}========================================"
echo "✓ Testing Complete!"
echo "========================================${NC}"
