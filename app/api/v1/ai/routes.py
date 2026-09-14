import time
from typing import Any, Dict
import httpx
from fastapi import APIRouter, Depends
from app.api.v1.ai.schemas import CoachRequest, CoachResponse
from app.config import settings
from app.dependencies import get_student_user

router=APIRouter(prefix="/api/v1/ai",tags=["AI coach"])
_usage:dict[str,list[float]]={}
@router.post("/coach",response_model=CoachResponse)
async def coach(payload:CoachRequest,current_user:Dict[str,Any]=Depends(get_student_user)):
    uid=str(current_user["sub"]); now=time.time(); recent=[t for t in _usage.get(uid,[]) if now-t<86400]
    if len(recent)>=50: return CoachResponse(answer="You have reached today's AI coach limit. Continue with the lesson transcript and try again tomorrow.",degraded=True,remaining_quota=0)
    recent.append(now); _usage[uid]=recent
    if not settings.GEMINI_API_KEY: return CoachResponse(answer="AI coach is temporarily unavailable. Please use the lesson transcript or try again later.",degraded=True,remaining_quota=50-len(recent))
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    question=payload.prompt or payload.message or ""
    body={"contents":[{"parts":[{"text":f"You are a careful course tutor. Answer only using the learner's course context.\n\nQuestion: {question}"}]}],"generationConfig":{"maxOutputTokens":800}}
    try:
        async with httpx.AsyncClient(timeout=settings.EXTERNAL_API_TIMEOUT) as client:
            response=await client.post(url,json=body); response.raise_for_status(); data=response.json()
        answer=data["candidates"][0]["content"]["parts"][0]["text"]
        return CoachResponse(answer=answer,remaining_quota=50-len(recent))
    except Exception:
        return CoachResponse(answer="AI coach is temporarily unavailable. Please use the lesson transcript or try again later.",degraded=True,remaining_quota=50-len(recent))
