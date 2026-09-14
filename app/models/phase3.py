"""Phase 3 live sessions and constrained code exercises."""
from datetime import datetime
import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class LiveSession(Base):
    __tablename__="live_sessions"
    id=Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    course_id=Column(UUID(as_uuid=True),ForeignKey("courses.id",ondelete="CASCADE"),nullable=False,index=True)
    instructor_id=Column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    title=Column(String(255),nullable=False); description=Column(Text,nullable=True)
    external_url=Column(String(1000),nullable=False); recording_url=Column(String(1000),nullable=True)
    starts_at=Column(DateTime,nullable=False,index=True); ends_at=Column(DateTime,nullable=True)
    timezone=Column(String(64),nullable=False,default="UTC"); capacity=Column(Integer,nullable=True)
    status=Column(String(32),nullable=False,default="scheduled",index=True); created_at=Column(DateTime,nullable=False,default=datetime.utcnow)
class LiveSessionAttendance(Base):
    __tablename__="live_session_attendance"
    id=Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    session_id=Column(UUID(as_uuid=True),ForeignKey("live_sessions.id",ondelete="CASCADE"),nullable=False)
    user_id=Column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    joined_at=Column(DateTime,nullable=False,default=datetime.utcnow); left_at=Column(DateTime,nullable=True)
    __table_args__=(Index("uq_live_session_attendee","session_id","user_id",unique=True),)
class CodeExercise(Base):
    __tablename__="code_exercises"
    id=Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); lesson_id=Column(UUID(as_uuid=True),ForeignKey("lessons.id",ondelete="CASCADE"),nullable=False,index=True)
    title=Column(String(255),nullable=False); prompt=Column(Text,nullable=False); runtime=Column(String(20),nullable=False,default="javascript")
    starter_code=Column(Text,nullable=True); expected_output=Column(Text,nullable=True); is_published=Column(Boolean,nullable=False,default=False)
class CodeSubmission(Base):
    __tablename__="code_submissions"
    id=Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); exercise_id=Column(UUID(as_uuid=True),ForeignKey("code_exercises.id",ondelete="CASCADE"),nullable=False,index=True)
    user_id=Column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True); source_code=Column(Text,nullable=False)
    status=Column(String(32),nullable=False); output=Column(Text,nullable=True); score=Column(Integer,nullable=True); created_at=Column(DateTime,nullable=False,default=datetime.utcnow)
