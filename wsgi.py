"""
WSGI entry point for Vercel deployment.
This file is required by Vercel to run the FastAPI application.
"""

from app.main import app

# For Vercel serverless functions
__all__ = ["app"]
