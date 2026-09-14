"""Moderated forum endpoints. Documents live in MongoDB; reports live in PostgreSQL."""
from datetime import datetime
from math import ceil
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.v1.community.schemas import *
from app.db.mongodb import get_mongodb
from app.db.postgres import get_db
from app.dependencies import get_student_user, get_admin_user
from app.models.community import CommunityReport, CommunityBlock
from bson import ObjectId

router = APIRouter(prefix="/api/v1/community", tags=["Community"])
def _mongo():
    try: return get_mongodb()
    except Exception as exc: raise HTTPException(503, "Community service is temporarily unavailable") from exc
def _doc(d):
    content=d.get("content") or d.get("body", "")
    return {"id": str(d.get("_id")), "title": d.get("title", ""), "body": content, "content": content, "user_id": str(d.get("user_id", "")), "course_id": d.get("course_id"), "organization_id": d.get("organization_id"), "moderation_status": d.get("moderation_status", "visible"), "created_at": d.get("created_at", datetime.utcnow()), "reply_count": d.get("reply_count", 0), "replies_count": d.get("reply_count", 0)}
@router.get("/threads", response_model=ThreadPage)
async def list_threads(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), course_id: str|None=None, organization_id: str|None=None, current_user: Dict[str,Any]=Depends(get_student_user)):
    db = _mongo(); q={"moderation_status":{"$ne":"deleted"}}
    if course_id: q["course_id"]=course_id
    if organization_id: q["organization_id"]=organization_id
    total=db.forum_threads.count_documents(q); docs=db.forum_threads.find(q).sort("created_at",-1).skip((page-1)*page_size).limit(page_size)
    return {"data":[_doc(d) for d in docs],"meta":{"page":page,"page_size":page_size,"total":total,"total_pages":ceil(total/page_size) if total else 0}}
@router.post("/threads", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(payload: ThreadCreate, current_user: Dict[str,Any]=Depends(get_student_user)):
    now=datetime.utcnow(); values=payload.model_dump(); values["content"]=values.get("content") or values.get("body") or ""; values.pop("body",None); d={**values,"user_id":current_user["sub"],"moderation_status":"visible","created_at":now,"reply_count":0}
    result=_mongo().forum_threads.insert_one(d); d["_id"]=result.inserted_id; return _doc(d)
@router.post("/threads/{thread_id}/replies", status_code=201)
async def reply(thread_id: str, payload: ReplyCreate, current_user: Dict[str,Any]=Depends(get_student_user)):
    try: oid=ObjectId(thread_id)
    except Exception: raise HTTPException(404,"Thread not found")
    db=_mongo(); thread=db.forum_threads.find_one({"_id":oid,"moderation_status":{"$ne":"deleted"}})
    if not thread: raise HTTPException(404,"Thread not found")
    content=payload.content or payload.body or ""; d={"thread_id":thread_id,"user_id":current_user["sub"],"content":content,"moderation_status":"visible","created_at":datetime.utcnow()}; r=db.forum_replies.insert_one(d); db.forum_threads.update_one({"_id":oid},{"$inc":{"reply_count":1}}); return {"id":str(r.inserted_id),"thread_id":thread_id,"content":content,"user_id":str(current_user["sub"]),"created_at":d["created_at"],"moderation_status":"visible"}
@router.get("/threads/{thread_id}/replies", response_model=ReplyPage)
async def list_replies(thread_id: str, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), current_user: Dict[str,Any]=Depends(get_student_user)):
    db=_mongo(); q={"thread_id":thread_id,"moderation_status":{"$ne":"deleted"}}; total=db.forum_replies.count_documents(q); docs=db.forum_replies.find(q).sort("created_at",1).skip((page-1)*page_size).limit(page_size)
    data=[{"id":str(d.get("_id")),"thread_id":thread_id,"content":d.get("content") or d.get("body", ""),"user_id":str(d.get("user_id", "")),"created_at":d.get("created_at",datetime.utcnow()),"moderation_status":d.get("moderation_status","visible")} for d in docs]
    return {"data":data,"meta":{"page":page,"page_size":page_size,"total":total,"total_pages":ceil(total/page_size) if total else 0}}
@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(thread_id: str, current_user: Dict[str,Any]=Depends(get_student_user)):
    try: oid=ObjectId(thread_id)
    except Exception: raise HTTPException(404,"Thread not found")
    d=_mongo().forum_threads.find_one({"_id":oid,"moderation_status":{"$ne":"deleted"}})
    if not d: raise HTTPException(404,"Thread not found")
    return _doc(d)
@router.post("/threads/{thread_id}/report", status_code=201)
async def report(thread_id: str, payload: ReportCreate, current_user: Dict[str,Any]=Depends(get_student_user), db: Session=Depends(get_db)):
    report=CommunityReport(reporter_id=current_user["sub"],content_id=thread_id,reason=payload.reason); db.add(report); db.commit(); return {"id":str(report.id),"status":report.status}
@router.post("/reports", status_code=201)
async def create_report(payload: ReportCreate, content_id: str|None = None, current_user: Dict[str,Any]=Depends(get_student_user), db: Session=Depends(get_db)):
    target=content_id or payload.content_id
    if not target: raise HTTPException(422,"content_id is required")
    report=CommunityReport(reporter_id=current_user["sub"],content_id=target,reason=payload.reason); db.add(report); db.commit(); return {"id":str(report.id),"status":report.status}
@router.post("/users/{user_id}/block", status_code=201)
async def block_user(user_id: str, current_user: Dict[str,Any]=Depends(get_student_user), db: Session=Depends(get_db)):
    if str(user_id)==str(current_user["sub"]): raise HTTPException(400,"Cannot block yourself")
    block=CommunityBlock(blocker_id=current_user["sub"],blocked_user_id=user_id); db.add(block)
    try: db.commit()
    except Exception: db.rollback(); return {"status":"already_blocked"}
    return {"status":"blocked"}
@router.post("/blocks", status_code=201)
async def create_block(payload: BlockCreate, current_user: Dict[str,Any]=Depends(get_student_user), db: Session=Depends(get_db)):
    return await block_user(payload.user_id, current_user, db)
@router.get("/moderation/reports")
async def reports(current_user: Dict[str,Any]=Depends(get_admin_user), db: Session=Depends(get_db)):
    return [{"id":str(r.id),"content_id":r.content_id,"reason":r.reason,"status":r.status,"created_at":r.created_at} for r in db.query(CommunityReport).order_by(CommunityReport.created_at.desc()).limit(100)]
@router.patch("/moderation/reports/{report_id}")
async def resolve_report(report_id: str, status_value: str = Query(..., alias="status"), current_user: Dict[str,Any]=Depends(get_admin_user), db: Session=Depends(get_db)):
    if status_value not in {"open","reviewing","resolved","dismissed"}: raise HTTPException(422,"Invalid moderation status")
    report=db.query(CommunityReport).filter(CommunityReport.id==report_id).first()
    if not report: raise HTTPException(404,"Report not found")
    report.status=status_value; db.commit(); return {"id":str(report.id),"status":report.status}
