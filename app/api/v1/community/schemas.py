from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ThreadCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    body: Optional[str] = Field(None, min_length=1, max_length=10000)
    content: Optional[str] = None
    course_id: Optional[str] = None
    organization_id: Optional[str] = None
class ReplyCreate(BaseModel):
    body: Optional[str] = Field(None, min_length=1, max_length=10000)
    content: Optional[str] = None
class ReportCreate(BaseModel):
    content_id: Optional[str] = None
    reason: str = Field(..., min_length=3, max_length=500)
class BlockCreate(BaseModel):
    user_id: str
    thread_id: Optional[str] = None
    reply_id: Optional[str] = None
class ThreadResponse(BaseModel):
    id: str
    title: str
    body: str
    user_id: str
    course_id: Optional[str] = None
    organization_id: Optional[str] = None
    moderation_status: str
    created_at: datetime
    reply_count: int = 0
    replies_count: int = 0
class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
class ThreadPage(BaseModel):
    data: List[ThreadResponse]
    meta: PageMeta

class ReplyResponse(BaseModel):
    id: str
    thread_id: str
    content: str
    user_id: str
    created_at: datetime
    moderation_status: str = "visible"

class ReplyPage(BaseModel):
    data: List[ReplyResponse]
    meta: PageMeta
