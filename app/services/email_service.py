"""
Email service using SendGrid for notifications.
Handles welcome emails, completion notifications, reminders, etc.
"""

import httpx
from typing import Optional, List, Dict, Any
import logging
from abc import ABC, abstractmethod
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class EmailTemplate(ABC):
    """Base class for email templates."""
    
    subject: str
    html_content: str
    text_content: str
    
    @abstractmethod
    def render(self, **context) -> tuple[str, str, str]:
        """Render template and return (subject, html, text)."""
        pass


class WelcomeEmailTemplate(EmailTemplate):
    """Welcome email for new users."""
    
    def render(self, user_name: str, dashboard_url: str, **context) -> tuple[str, str, str]:
        subject = f"Welcome to {settings.APP_NAME}! 🚀"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                    <h1 style="color: #2c3e50;">Welcome, {user_name}!</h1>
                    <p style="color: #555; font-size: 16px; line-height: 1.6;">
                        You've successfully joined <strong>{settings.APP_NAME}</strong>. 
                        We're excited to help you learn coding and AI skills for free.
                    </p>
                    
                    <h2 style="color: #3498db; margin-top: 30px;">Get Started in 3 Steps:</h2>
                    <ol style="color: #555; font-size: 14px; line-height: 1.8;">
                        <li>Browse our free courses on Python, AI, and more</li>
                        <li>Enroll in a course that interests you</li>
                        <li>Start learning with interactive lessons and AI support</li>
                    </ol>
                    
                    <div style="margin-top: 30px; text-align: center;">
                        <a href="{dashboard_url}" style="
                            background-color: #3498db;
                            color: white;
                            padding: 12px 30px;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                            display: inline-block;
                        ">
                            Go to Dashboard
                        </a>
                    </div>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                        This is an automated email. Please do not reply to this message.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_content = f"""
        Welcome, {user_name}!
        
        You've successfully joined {settings.APP_NAME}. 
        We're excited to help you learn coding and AI skills for free.
        
        Get Started in 3 Steps:
        1. Browse our free courses on Python, AI, and more
        2. Enroll in a course that interests you
        3. Start learning with interactive lessons and AI support
        
        Visit your dashboard: {dashboard_url}
        """
        
        return subject, html_content, text_content


class LessonCompletedEmailTemplate(EmailTemplate):
    """Email sent when user completes a lesson."""
    
    def render(
        self,
        user_name: str,
        course_title: str,
        lesson_title: str,
        progress_percentage: float,
        next_lesson_title: Optional[str] = None,
        course_url: str = "",
        **context
    ) -> tuple[str, str, str]:
        subject = f"Great work! You completed '{lesson_title}' 🎉"
        
        next_lesson_html = f"""
        <h3 style="color: #3498db;">Next Up:</h3>
        <p style="color: #555; font-size: 14px;">
            <strong>{next_lesson_title}</strong>
        </p>
        """ if next_lesson_title else ""
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                    <h1 style="color: #27ae60;">Lesson Completed! 🎉</h1>
                    
                    <p style="color: #555; font-size: 16px; line-height: 1.6;">
                        Excellent work, {user_name}! You've completed:
                    </p>
                    
                    <div style="background-color: #ecf0f1; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0;">
                        <p style="color: #555; margin: 5px 0;"><strong>Course:</strong> {course_title}</p>
                        <p style="color: #555; margin: 5px 0;"><strong>Lesson:</strong> {lesson_title}</p>
                        <p style="color: #555; margin: 5px 0;"><strong>Progress:</strong> {progress_percentage:.0f}% complete</p>
                    </div>
                    
                    {next_lesson_html}
                    
                    <div style="margin-top: 30px; text-align: center;">
                        <a href="{course_url}" style="
                            background-color: #3498db;
                            color: white;
                            padding: 12px 30px;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                            display: inline-block;
                        ">
                            Continue Learning
                        </a>
                    </div>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                        Keep up the great work! Every lesson brings you closer to mastery.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_content = f"""
        Lesson Completed! 🎉
        
        Excellent work, {user_name}! You've completed:
        
        Course: {course_title}
        Lesson: {lesson_title}
        Progress: {progress_percentage:.0f}% complete
        
        {f"Next Up: {next_lesson_title}" if next_lesson_title else ""}
        
        Keep up the great work!
        """
        
        return subject, html_content, text_content


class StreakMilestoneEmailTemplate(EmailTemplate):
    """Email for streak milestones."""
    
    def render(
        self,
        user_name: str,
        streak_count: int,
        dashboard_url: str = "",
        **context
    ) -> tuple[str, str, str]:
        fire_emoji = "🔥" * (min(streak_count // 7, 5))  # More fire for longer streaks
        subject = f"You're on a {streak_count}-day streak! {fire_emoji}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                    <h1 style="color: #e74c3c;">You're on Fire! {fire_emoji}</h1>
                    
                    <div style="font-size: 48px; text-align: center; margin: 20px 0;">
                        {streak_count} 🔥
                    </div>
                    
                    <p style="color: #555; font-size: 16px; line-height: 1.6; text-align: center;">
                        <strong>{user_name}</strong>, you've been learning every day for <strong>{streak_count} consecutive days</strong>!
                    </p>
                    
                    <p style="color: #555; font-size: 14px; text-align: center; margin-top: 20px;">
                        This kind of consistency builds real skills. Keep it up!
                    </p>
                    
                    <div style="margin-top: 30px; text-align: center;">
                        <a href="{dashboard_url}" style="
                            background-color: #e74c3c;
                            color: white;
                            padding: 12px 30px;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                            display: inline-block;
                        ">
                            Continue Your Streak
                        </a>
                    </div>
                </div>
            </body>
        </html>
        """
        
        text_content = f"""
        You're on Fire! {fire_emoji}
        
        {user_name}, you've been learning every day for {streak_count} consecutive days!
        
        This kind of consistency builds real skills. Keep it up!
        """
        
        return subject, html_content, text_content


class CourseCompletedEmailTemplate(EmailTemplate):
    """Email for course completion."""
    
    def render(
        self,
        user_name: str,
        course_title: str,
        course_url: str = "",
        **context
    ) -> tuple[str, str, str]:
        subject = f"Congratulations! You completed '{course_title}' 🏆"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                    <h1 style="color: #27ae60;">Course Complete! 🏆</h1>
                    
                    <p style="color: #555; font-size: 16px; line-height: 1.6;">
                        Congratulations, {user_name}! You've successfully completed:
                    </p>
                    
                    <div style="background-color: #d5f4e6; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center;">
                        <h2 style="color: #27ae60; margin: 0;">{course_title}</h2>
                    </div>
                    
                    <p style="color: #555; font-size: 14px; line-height: 1.6;">
                        You've demonstrated commitment and discipline by completing this entire course. 
                        This is a major milestone in your learning journey!
                    </p>
                    
                    <h3 style="color: #3498db; margin-top: 30px;">What's Next?</h3>
                    <ul style="color: #555; font-size: 14px; line-height: 1.8;">
                        <li>Download your course completion certificate</li>
                        <li>Build a project using what you've learned</li>
                        <li>Share your achievement with peers</li>
                        <li>Explore our other courses</li>
                    </ul>
                    
                    <div style="margin-top: 30px; text-align: center;">
                        <a href="{course_url}" style="
                            background-color: #27ae60;
                            color: white;
                            padding: 12px 30px;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                            display: inline-block;
                        ">
                            View Your Certificate
                        </a>
                    </div>
                </div>
            </body>
        </html>
        """
        
        text_content = f"""
        Course Complete! 🏆
        
        Congratulations, {user_name}! You've successfully completed:
        
        {course_title}
        
        You've demonstrated commitment and discipline. This is a major milestone!
        
        What's Next?
        - Download your course completion certificate
        - Build a project using what you've learned
        - Share your achievement with peers
        - Explore our other courses
        """
        
        return subject, html_content, text_content


# ============================================================================
# EMAIL SERVICE
# ============================================================================

class EmailService:
    """Service for sending emails via SendGrid."""
    
    def __init__(self):
        """Initialize SendGrid client."""
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.RESEND_FROM_EMAIL
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """
        Send email via SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback
            reply_to: Reply-to email address
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.api_key:
            logger.warning(f"Email service not configured. Skipping email to {to_email}")
            return False
        
        try:
            payload = {"from": self.from_email, "to": [to_email], "subject": subject, "html": html_content, "text": text_content or ""}
            if reply_to: payload["reply_to"] = reply_to
            response = httpx.post("https://api.resend.com/emails", headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, json=payload, timeout=settings.EXTERNAL_API_TIMEOUT)
            response.raise_for_status()
            logger.info("Email sent successfully", extra={"provider": "resend", "recipient": to_email, "provider_id": response.json().get("id")})
            return True
        
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    def send_welcome_email(self, user_email: str, user_name: str, dashboard_url: str) -> bool:
        """Send welcome email to new user."""
        template = WelcomeEmailTemplate()
        subject, html, text = template.render(user_name=user_name, dashboard_url=dashboard_url)
        return self.send_email(user_email, subject, html, text)
    
    def send_lesson_completed_email(
        self,
        user_email: str,
        user_name: str,
        course_title: str,
        lesson_title: str,
        progress_percentage: float,
        next_lesson_title: Optional[str] = None,
        course_url: str = "",
    ) -> bool:
        """Send lesson completion email."""
        template = LessonCompletedEmailTemplate()
        subject, html, text = template.render(
            user_name=user_name,
            course_title=course_title,
            lesson_title=lesson_title,
            progress_percentage=progress_percentage,
            next_lesson_title=next_lesson_title,
            course_url=course_url,
        )
        return self.send_email(user_email, subject, html, text)
    
    def send_streak_milestone_email(
        self,
        user_email: str,
        user_name: str,
        streak_count: int,
        dashboard_url: str = "",
    ) -> bool:
        """Send streak milestone email."""
        template = StreakMilestoneEmailTemplate()
        subject, html, text = template.render(
            user_name=user_name,
            streak_count=streak_count,
            dashboard_url=dashboard_url,
        )
        return self.send_email(user_email, subject, html, text)
    
    def send_course_completed_email(
        self,
        user_email: str,
        user_name: str,
        course_title: str,
        course_url: str = "",
    ) -> bool:
        """Send course completion email."""
        template = CourseCompletedEmailTemplate()
        subject, html, text = template.render(
            user_name=user_name,
            course_title=course_title,
            course_url=course_url,
        )
        return self.send_email(user_email, subject, html, text)


# === SINGLETON INSTANCE ===
email_service = EmailService()
