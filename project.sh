#!/bin/bash


# Top-level files
touch .env.example .gitignore requirements.txt docker-compose.yml Dockerfile README.md wsgi.py

# App core
mkdir -p app
touch app/__init__.py app/main.py app/config.py app/security.py app/dependencies.py app/health.py

# API
mkdir -p app/api/v1
touch app/api/__init__.py app/api/v1/__init__.py

# Feature modules
MODULES=(
  auth users courses modules lessons progress enrollments
  community gamification notifications ai admin
)

for module in "${MODULES[@]}"; do
  mkdir -p "app/api/v1/$module"
  touch "app/api/v1/$module/__init__.py"
  touch "app/api/v1/$module/routes.py"
  touch "app/api/v1/$module/schemas.py"
  touch "app/api/v1/$module/service.py"
done

# Extra module files
touch app/api/v1/courses/models.py
touch app/api/v1/modules/models.py
touch app/api/v1/lessons/models.py
touch app/api/v1/progress/models.py
touch app/api/v1/enrollments/models.py
touch app/api/v1/community/models.py
touch app/api/v1/gamification/models.py
touch app/api/v1/notifications/models.py
touch app/api/v1/ai/agents.py

# Models
mkdir -p app/models
touch app/models/__init__.py app/models/user.py app/models/course.py app/models/module.py \
      app/models/lesson.py app/models/enrollment.py app/models/progress.py \
      app/models/badge.py app/models/community.py app/models/notification.py

# Schemas
mkdir -p app/schemas
touch app/schemas/__init__.py app/schemas/common.py app/schemas/user.py \
      app/schemas/course.py app/schemas/module.py app/schemas/lesson.py \
      app/schemas/progress.py app/schemas/ai.py

# Services
mkdir -p app/services
touch app/services/__init__.py app/services/email_service.py \
      app/services/youtube_service.py app/services/cloudinary_service.py \
      app/services/ai_service.py app/services/analytics_service.py \
      app/services/storage_service.py

# Utils
mkdir -p app/utils
touch app/utils/__init__.py app/utils/logger.py app/utils/exceptions.py \
      app/utils/validators.py app/utils/decorators.py

# Middleware
mkdir -p app/middleware
touch app/middleware/__init__.py app/middleware/error_handler.py \
      app/middleware/rate_limiter.py app/middleware/request_logger.py

# DB
mkdir -p app/db/migrations/versions
touch app/db/__init__.py app/db/postgres.py app/db/mongodb.py

# Tests
mkdir -p app/tests
touch app/tests/__init__.py app/tests/conftest.py app/tests/test_auth.py \
      app/tests/test_courses.py app/tests/test_progress.py \
      app/tests/test_ai.py app/tests/test_integration.py

echo "✅ Kukekodes backend project structure created successfully"
