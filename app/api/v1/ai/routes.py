import time
from typing import Any, Dict
import httpx
from fastapi import APIRouter, Depends
from app.api.v1.ai.schemas import CoachRequest, CoachResponse
from app.config import settings
from app.dependencies import get_student_user
from app.db.postgres import get_db
from app.db.mongodb import get_mongodb, insert_ai_interaction
from app.models.course import Lesson
from sqlalchemy.orm import Session

router=APIRouter(prefix="/api/v1/ai",tags=["AI coach"])
_usage:dict[str,list[float]]={}
@router.post("/coach",response_model=CoachResponse)
async def coach(payload:CoachRequest,current_user:Dict[str,Any]=Depends(get_student_user),db:Session=Depends(get_db)):
    uid=str(current_user["sub"]); now=time.time(); recent=[t for t in _usage.get(uid,[]) if now-t<86400]
    if len(recent)>=50: return CoachResponse(answer="You have reached today's AI coach limit. Continue with the lesson transcript and try again tomorrow.",degraded=True,remaining_quota=0)
    recent.append(now); _usage[uid]=recent
    if not settings.GEMINI_API_KEY: return CoachResponse(answer="AI coach is temporarily unavailable. Please use the lesson transcript or try again later.",degraded=True,remaining_quota=50-len(recent))
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    question=payload.prompt or payload.message or ""
    context=payload.context
    if not context and payload.lesson_id:
        try:
            lesson=db.query(Lesson).filter(Lesson.id==payload.lesson_id).first()
            context=(getattr(lesson,"transcript",None) or getattr(lesson,"description",None)) if lesson else None
        except Exception: context=None
    context=(context or "No course context was provided.")[:12000]
    history=[]
    try:
        history=list(get_mongodb().ai_interactions.find({"user_id":uid,"lesson_id":payload.lesson_id}).sort("timestamp",-1).limit(6)) if payload.lesson_id else []
    except Exception: history=[]
    turns=[]
    for item in reversed(history): turns.extend([f"Learner: {item.get('question','')}",f"Tutor: {item.get('response','')}"])
    memory="\n".join(turns)
    body={"contents":[{"parts":[{"text":f"You are a careful course tutor. Answer only using the learner's course context below. If it does not contain the answer, say so.\n\nCourse context:\n{context}\n\nRecent conversation:\n{memory}\n\nQuestion: {question}"}]}],"generationConfig":{"maxOutputTokens":800}}
    try:
        async with httpx.AsyncClient(timeout=settings.EXTERNAL_API_TIMEOUT) as client:
            response=await client.post(url,json=body); response.raise_for_status(); data=response.json()
        answer=data["candidates"][0]["content"]["parts"][0]["text"]
        try: insert_ai_interaction(uid,payload.lesson_id or "",question,answer,metadata={"course_id":payload.course_id})
        except Exception: pass
        return CoachResponse(answer=answer,remaining_quota=50-len(recent))
    except Exception:
        return CoachResponse(answer="AI coach is temporarily unavailable. Please use the lesson transcript or try again later.",degraded=True,remaining_quota=50-len(recent))
