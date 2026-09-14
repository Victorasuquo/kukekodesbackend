from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.dependencies import get_student_user, get_instructor_user
from app.models.phase3 import LiveSession, LiveSessionAttendance

router=APIRouter(prefix="/api/v1/live-sessions",tags=["Live sessions"])
class SessionCreate(BaseModel):
    course_id:str; title:str=Field(...,min_length=3); description:str|None=None; external_url:HttpUrl; starts_at:datetime; ends_at:datetime|None=None; timezone:str="UTC"; capacity:int|None=Field(None,gt=0)
def out(s):
    active=s.status=="live"
    return {"id":str(s.id),"course_id":str(s.course_id),"course":str(s.course_id),"title":s.title,"description":s.description,"external_url":s.external_url,"youtube_live_url":s.external_url,"recording_url":s.recording_url,"starts_at":s.starts_at,"ends_at":s.ends_at,"scheduled_start":s.starts_at,"scheduled_end":s.ends_at or s.starts_at,"timezone":s.timezone,"capacity":s.capacity,"max_participants":s.capacity,"status":s.status,"is_active":active}
@router.post("",status_code=201)
async def create(payload:SessionCreate,current_user:Dict[str,Any]=Depends(get_instructor_user),db:Session=Depends(get_db)):
    values=payload.model_dump(); values["external_url"]=str(payload.external_url)
    s=LiveSession(**values,instructor_id=current_user["sub"]); db.add(s); db.commit(); db.refresh(s); return out(s)
@router.get("")
async def list_sessions(course_id:str|None=None,current_user:Dict[str,Any]=Depends(get_student_user),db:Session=Depends(get_db)):
    q=db.query(LiveSession).filter(LiveSession.status!="cancelled");
    if course_id:q=q.filter(LiveSession.course_id==course_id)
    return [out(s) for s in q.order_by(LiveSession.starts_at).all()]
@router.post("/{session_id}/join")
async def join(session_id:str,current_user:Dict[str,Any]=Depends(get_student_user),db:Session=Depends(get_db)):
    s=db.query(LiveSession).filter(LiveSession.id==session_id).first()
    if not s: raise HTTPException(404,"Live session not found")
    a=db.query(LiveSessionAttendance).filter_by(session_id=s.id,user_id=current_user["sub"]).first()
    if not a: db.add(LiveSessionAttendance(session_id=s.id,user_id=current_user["sub"])); db.commit()
    return {"join_url":s.external_url,"session":out(s)}
@router.post("/{session_id}/attendance")
async def attendance(session_id:str,current_user:Dict[str,Any]=Depends(get_student_user),db:Session=Depends(get_db)):
    a=db.query(LiveSessionAttendance).filter_by(session_id=session_id,user_id=current_user["sub"]).first()
    if not a: raise HTTPException(404,"Join the session before marking attendance")
    a.left_at=datetime.utcnow(); db.commit(); return {"status":"attended"}
@router.post("/{session_id}/recording")
async def recording(session_id:str, recording_url:HttpUrl, current_user:Dict[str,Any]=Depends(get_instructor_user),db:Session=Depends(get_db)):
    s=db.query(LiveSession).filter(LiveSession.id==session_id,LiveSession.instructor_id==current_user["sub"]).first()
    if not s: raise HTTPException(404,"Live session not found")
    s.recording_url=str(recording_url); s.status="completed"; db.commit(); return out(s)
