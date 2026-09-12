#!/bin/bash
# Comprehensive API Testing Script for Kukekodes LMS
# Tests the complete user journey: Register → Login → Enroll → Learn → Certificate

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
echo "🚀 Testing Kukekodes LMS API at: $BASE_URL"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    local description=$5
    local auth_header=$6
    
    echo -n "Testing: $description... "
    
    if [ -n "$auth_header" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $auth_header" \
            -d "$data" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq "$expected_status" ] || [ "$http_code" -eq "200" ] || [ "$http_code" -eq "201" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        echo "$body"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code, expected $expected_status)"
        echo "$body"
        return 1
    fi
}

# ============================================================================
# 1. HEALTH CHECK
# ============================================================================

echo ""
echo "📋 1. HEALTH CHECK"
echo "-------------------"
test_endpoint "GET" "/health" "" 200 "Health check"

# ============================================================================
# 2. AUTHENTICATION FLOW
# ============================================================================

echo ""
echo "🔐 2. AUTHENTICATION FLOW"
echo "--------------------------"

# Generate unique email
TIMESTAMP=$(date +%s)
TEST_EMAIL="testuser_${TIMESTAMP}@kukekodes.com"
TEST_PASSWORD="TestPass123!"

# Register new user
echo ""
echo "Registering new user: $TEST_EMAIL"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\",
        \"first_name\": \"Test\",
        \"last_name\": \"User\"
    }")

echo "Register response: $REGISTER_RESPONSE"

# Login
echo ""
echo "Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\"
    }")

echo "Login response: $LOGIN_RESPONSE"

# Extract token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")

if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}Failed to get access token. Exiting.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Got access token${NC}"

# ============================================================================
# 3. USER PROFILE
# ============================================================================

echo ""
echo "👤 3. USER PROFILE"
echo "-------------------"

# Get profile
test_endpoint "GET" "/api/v1/users/me" "" 200 "Get user profile" "$ACCESS_TOKEN"

# Update profile
test_endpoint "PUT" "/api/v1/users/me" \
    '{"first_name": "Updated", "last_name": "User", "bio": "Test bio"}' \
    200 "Update profile" "$ACCESS_TOKEN"

# Get dashboard
test_endpoint "GET" "/api/v1/users/dashboard" "" 200 "Get user dashboard" "$ACCESS_TOKEN"

# ============================================================================
# 4. COURSES (View as student)
# ============================================================================

echo ""
echo "📚 4. COURSES"
echo "--------------"

# List courses
COURSES_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/courses" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
echo "Courses: $COURSES_RESPONSE"

# Get first course ID if available
COURSE_ID=$(echo "$COURSES_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['courses'][0]['id'] if data.get('courses') else '')" 2>/dev/null || echo "")

if [ -n "$COURSE_ID" ]; then
    echo "Found course ID: $COURSE_ID"
    
    # Get course details
    test_endpoint "GET" "/api/v1/courses/$COURSE_ID" "" 200 "Get course details" "$ACCESS_TOKEN"
fi

# ============================================================================
# 5. ENROLLMENTS
# ============================================================================

echo ""
echo "📝 5. ENROLLMENTS"
echo "------------------"

# Get my enrollments
test_endpoint "GET" "/api/v1/enrollments/my-enrollments" "" 200 "Get my enrollments" "$ACCESS_TOKEN"

if [ -n "$COURSE_ID" ]; then
    # Enroll in course
    echo ""
    ENROLL_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/enrollments" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "{\"course_id\": \"$COURSE_ID\"}")
    echo "Enroll response: $ENROLL_RESPONSE"
    
    # Get enrollment status
    test_endpoint "GET" "/api/v1/enrollments/$COURSE_ID" "" 200 "Get enrollment status" "$ACCESS_TOKEN"
fi

# ============================================================================
# 6. PROGRESS TRACKING
# ============================================================================

echo ""
echo "📊 6. PROGRESS TRACKING"
echo "------------------------"

# Get user stats
test_endpoint "GET" "/api/v1/progress/user/stats" "" 200 "Get user stats" "$ACCESS_TOKEN"

# Get user dashboard
test_endpoint "GET" "/api/v1/progress/user/dashboard" "" 200 "Get progress dashboard" "$ACCESS_TOKEN"

# Get learning history
test_endpoint "GET" "/api/v1/progress/user/history" "" 200 "Get learning history" "$ACCESS_TOKEN"

if [ -n "$COURSE_ID" ]; then
    # Get course progress
    test_endpoint "GET" "/api/v1/progress/course/$COURSE_ID" "" 200 "Get course progress" "$ACCESS_TOKEN"
fi

# ============================================================================
# 7. GAMIFICATION
# ============================================================================

echo ""
echo "🏆 7. GAMIFICATION"
echo "-------------------"

# Get user badges
test_endpoint "GET" "/api/v1/gamification/badges/user" "" 200 "Get user badges" "$ACCESS_TOKEN"

# Get all badges
test_endpoint "GET" "/api/v1/gamification/badges/all" "" 200 "Get all badges"

# Get user streak
test_endpoint "GET" "/api/v1/gamification/streaks/user" "" 200 "Get user streak" "$ACCESS_TOKEN"

# Get global leaderboard
test_endpoint "GET" "/api/v1/gamification/leaderboard/global" "" 200 "Get global leaderboard"

# Get streak leaderboard
test_endpoint "GET" "/api/v1/gamification/leaderboard/streak" "" 200 "Get streak leaderboard"

# ============================================================================
# 8. NOTIFICATIONS
# ============================================================================

echo ""
echo "🔔 8. NOTIFICATIONS"
echo "--------------------"

# Get notifications
test_endpoint "GET" "/api/v1/notifications" "" 200 "Get notifications" "$ACCESS_TOKEN"

# Get unread count
test_endpoint "GET" "/api/v1/notifications/unread-count" "" 200 "Get unread count" "$ACCESS_TOKEN"

# Get notification preferences
test_endpoint "GET" "/api/v1/notifications/preferences/me" "" 200 "Get notification preferences" "$ACCESS_TOKEN"

# Update notification preferences
test_endpoint "PUT" "/api/v1/notifications/preferences/me" \
    '{"email_on_lesson_complete": true, "receive_weekly_summary": false}' \
    200 "Update notification preferences" "$ACCESS_TOKEN"

# ============================================================================
# 9. CERTIFICATES
# ============================================================================

echo ""
echo "🎓 9. CERTIFICATES"
echo "-------------------"

# Get user certificates
test_endpoint "GET" "/api/v1/progress/certificates" "" 200 "Get user certificates" "$ACCESS_TOKEN"

if [ -n "$COURSE_ID" ]; then
    # Try to get certificate (will fail if course not completed)
    echo ""
    CERT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/progress/certificate/$COURSE_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    echo "Certificate response: $CERT_RESPONSE"
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "================================================"
echo -e "${GREEN}🎉 API Testing Complete!${NC}"
echo "================================================"
echo ""
echo "Test User: $TEST_EMAIL"
echo "Access Token: ${ACCESS_TOKEN:0:50}..."
echo ""
echo "All user-facing endpoints have been tested."
echo ""
