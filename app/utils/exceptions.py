"""
Custom exception classes for the Kukekodes LMS application.
Used for domain-specific error handling and validation.
"""

from fastapi import HTTPException, status


# ============================================================================
# VALIDATION ERRORS
# ============================================================================

class ValidationError(HTTPException):
    """Raised when input validation fails."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class InvalidEmailError(ValidationError):
    """Raised when email format is invalid."""
    
    def __init__(self, detail: str = "Invalid email format"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class InvalidPasswordError(ValidationError):
    """Raised when password doesn't meet requirements."""
    
    def __init__(
        self,
        detail: str = "Password must be at least 8 characters, contain uppercase, lowercase, and numbers",
    ):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class InvalidURLError(ValidationError):
    """Raised when URL format is invalid."""
    
    def __init__(self, detail: str = "Invalid URL format"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# CONFLICT ERRORS (409)
# ============================================================================

class ConflictError(HTTPException):
    """Raised when resource already exists or conflicts with existing data."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_409_CONFLICT):
        super().__init__(status_code=status_code, detail=detail)


class DuplicateEmailError(ConflictError):
    """Raised when email already exists in system."""
    
    def __init__(self, detail: str = "Email already registered"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class DuplicateEnrollmentError(ConflictError):
    """Raised when user already enrolled in course."""
    
    def __init__(self, detail: str = "User already enrolled in this course"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class DuplicateResourceError(ConflictError):
    """Raised when trying to create duplicate resource."""
    
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


# ============================================================================
# NOT FOUND ERRORS (404)
# ============================================================================

class NotFoundError(HTTPException):
    """Raised when resource is not found."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_404_NOT_FOUND):
        super().__init__(status_code=status_code, detail=detail)


class UserNotFoundError(NotFoundError):
    """Raised when user is not found."""
    
    def __init__(self, detail: str = "User not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class CourseNotFoundError(NotFoundError):
    """Raised when course is not found."""
    
    def __init__(self, detail: str = "Course not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class LessonNotFoundError(NotFoundError):
    """Raised when lesson is not found."""
    
    def __init__(self, detail: str = "Lesson not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ModuleNotFoundError(NotFoundError):
    """Raised when module is not found."""
    
    def __init__(self, detail: str = "Module not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class EnrollmentNotFoundError(NotFoundError):
    """Raised when enrollment is not found."""
    
    def __init__(self, detail: str = "Enrollment not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class BadgeNotFoundError(NotFoundError):
    """Raised when badge is not found."""
    
    def __init__(self, detail: str = "Badge not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


# ============================================================================
# AUTHENTICATION/AUTHORIZATION ERRORS (401, 403)
# ============================================================================

class AuthenticationError(HTTPException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication failed", status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(status_code=status_code, detail=detail)


class InvalidCredentialsError(AuthenticationError):
    """Raised when email/password combination is invalid."""
    
    def __init__(self, detail: str = "Invalid email or password"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class InvalidTokenError(AuthenticationError):
    """Raised when token is invalid or expired."""
    
    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(HTTPException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, detail: str = "Insufficient permissions", status_code: int = status.HTTP_403_FORBIDDEN):
        super().__init__(status_code=status_code, detail=detail)


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user doesn't have required role."""
    
    def __init__(self, detail: str = "Insufficient permissions for this action"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class NotAdminError(AuthorizationError):
    """Raised when non-admin tries admin action."""
    
    def __init__(self, detail: str = "Only admins can perform this action"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class NotInstructorError(AuthorizationError):
    """Raised when non-instructor tries instructor action."""
    
    def __init__(self, detail: str = "Only instructors can perform this action"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class NotOwnerError(AuthorizationError):
    """Raised when user tries to modify resource they don't own."""
    
    def __init__(self, detail: str = "You can only modify your own resources"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


# ============================================================================
# BUSINESS LOGIC ERRORS (422, 400)
# ============================================================================

class BusinessLogicError(HTTPException):
    """Raised when business logic constraint is violated."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY):
        super().__init__(status_code=status_code, detail=detail)


class CourseNotPublishedError(BusinessLogicError):
    """Raised when trying to enroll in unpublished course."""
    
    def __init__(self, detail: str = "This course is not yet published"):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class InvalidCourseStateError(BusinessLogicError):
    """Raised when course is in invalid state for operation."""
    
    def __init__(self, detail: str = "Course is in an invalid state for this operation"):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class MinimumLessonsRequiredError(BusinessLogicError):
    """Raised when course doesn't have minimum lessons to publish."""
    
    def __init__(self, min_lessons: int = 1):
        detail = f"Course must have at least {min_lessons} lesson(s) to publish"
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class InvalidProgressStateError(BusinessLogicError):
    """Raised when trying invalid progress operation."""
    
    def __init__(self, detail: str = "Invalid progress operation"):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class AlreadyCompletedError(BusinessLogicError):
    """Raised when trying to complete already-completed item."""
    
    def __init__(self, detail: str = "This item is already marked as complete"):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


# ============================================================================
# EXTERNAL SERVICE ERRORS (502, 503)
# ============================================================================

class ExternalServiceError(HTTPException):
    """Raised when external service fails."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(status_code=status_code, detail=detail)


class EmailServiceError(ExternalServiceError):
    """Raised when email service fails."""
    
    def __init__(self, detail: str = "Failed to send email"):
        super().__init__(detail=detail, status_code=status.HTTP_502_BAD_GATEWAY)


class CloudinaryServiceError(ExternalServiceError):
    """Raised when Cloudinary service fails."""
    
    def __init__(self, detail: str = "Failed to upload media"):
        super().__init__(detail=detail, status_code=status.HTTP_502_BAD_GATEWAY)


class YouTubeServiceError(ExternalServiceError):
    """Raised when YouTube API fails."""
    
    def __init__(self, detail: str = "Failed to fetch video metadata"):
        super().__init__(detail=detail, status_code=status.HTTP_502_BAD_GATEWAY)


class AIServiceError(ExternalServiceError):
    """Raised when AI service fails."""
    
    def __init__(self, detail: str = "Failed to process AI request"):
        super().__init__(detail=detail, status_code=status.HTTP_502_BAD_GATEWAY)
