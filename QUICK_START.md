# Quick Start Guide - Kukekodes Backend

## Local Development

### 1. Setup Virtual Environment
```bash
cd /Users/ghgfd/Documents/kukekodesbackend
python3.11 -m venv .kukekodes_venv
source .kukekodes_venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Create/update `.env` file with:
```
DATABASE_URL=postgresql://user:pass@db.supabase.co:5432/postgres
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/db
JWT_SECRET=your-secret-key-32-chars-minimum
ENVIRONMENT=development
DEBUG=true
```

### 4. Start Server
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 5. Access API
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Create Test Accounts

### Student Account
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "Student123",
    "first_name": "John",
    "last_name": "Student"
  }'
```

### Instructor Account
```bash
python create_instructor.py
# Email: instructor@example.com
# Password: InstructorPass123
```

---

## Common Tasks

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"Student123"}'
```

### Create Course (Instructor)
```bash
curl -X POST http://localhost:8000/api/v1/courses \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Basics",
    "description": "Learn Python fundamentals",
    "skill_level": "beginner",
    "category": "Programming",
    "is_free": true,
    "tags": ["Python", "Programming"]
  }'
```

### List Courses
```bash
curl http://localhost:8000/api/v1/courses \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Create Module
```bash
curl -X POST http://localhost:8000/api/v1/modules \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "COURSE_ID",
    "title": "Module 1: Basics",
    "description": "Learn the basics",
    "order": 1
  }'
```

### Create Lesson
```bash
curl -X POST http://localhost:8000/api/v1/lessons \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_id": "MODULE_ID",
    "title": "What is Python?",
    "description": "Introduction to Python",
    "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "order": 1
  }'
```

---

## File Structure
```
/Users/ghgfd/Documents/kukekodesbackend/
├── app/
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Configuration
│   ├── security.py             # Auth & CORS
│   ├── dependencies.py         # Dependency injection
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic
│   ├── api/v1/                 # API routes
│   ├── db/                     # Database config
│   ├── middleware/             # Custom middleware
│   └── utils/                  # Utilities
├── vercel.json                 # Vercel config
├── api/index.py                # Serverless entry
├── requirements.txt            # Dependencies
├── .env                        # Environment variables
├── DEPLOYMENT.md               # Deployment guide
└── READY_FOR_DEPLOYMENT.md    # Status summary
```

---

## Environment Variables

### Required
- `DATABASE_URL` - PostgreSQL connection
- `JWT_SECRET` - Minimum 32 characters

### Optional
- `MONGODB_URI` - MongoDB connection
- `SENDGRID_API_KEY` - Email service
- `CLOUDINARY_*` - Image storage
- `YOUTUBE_API_KEY` - Video metadata
- `GEMINI_API_KEY` - AI features

---

## Database

### Initialize DB
Tables are auto-created on startup. To reset:
```python
from app.db.postgres import drop_all_tables, init_db
drop_all_tables()
init_db()
```

### Migrations
For schema changes:
```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

---

## Troubleshooting

### Import Errors
- Ensure all models are imported in `app/models/__init__.py`
- Check Python version (3.11+)

### Database Connection
- Verify `DATABASE_URL` is correct
- Check network access to Supabase
- Ensure SSL mode in URL if required

### CORS Errors
- Currently allows all origins
- Update `app/security.py` to restrict

### Token Errors
- Tokens expire in 15 minutes
- Use refresh token to get new access token
- Verify `JWT_SECRET` is consistent

---

## Testing

Run tests:
```bash
pytest
```

With coverage:
```bash
pytest --cov=app tests/
```

---

## Performance Tips

1. Enable query logging in development:
   ```python
   # app/db/postgres.py
   engine = create_engine(DATABASE_URL, echo=True)
   ```

2. Use pagination for large datasets:
   ```bash
   GET /api/v1/courses?page=1&page_size=10
   ```

3. Add indexes for common filters
4. Cache frequently accessed data
5. Use connection pooling (already configured)

---

## Deployment Checklist

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations complete
- [ ] CORS origin restricted to frontend
- [ ] JWT_SECRET is strong (32+ chars)
- [ ] Email service configured
- [ ] Error logging enabled
- [ ] Rate limiting enabled
- [ ] HTTPS enforced
- [ ] Database backups enabled

---

## Support & Documentation

- **API Docs**: http://localhost:8000/docs (interactive)
- **API Schema**: http://localhost:8000/openapi.json
- **Test Data**: See `TEST_DATA.py`
- **Deployment**: See `DEPLOYMENT.md`

---

**Last Updated**: January 15, 2026
**Status**: ✅ Production Ready
