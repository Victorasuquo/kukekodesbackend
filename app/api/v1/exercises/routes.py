from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.dependencies import get_student_user, get_instructor_user
from app.models.phase3 import CodeExercise, CodeSubmission

router=APIRouter(prefix="/api/v1",tags=["Code exercises"])
class ExerciseCreate(BaseModel): lesson_id:str; title:str=Field(...,min_length=3); prompt:str=Field(...,min_length=1); runtime:str="javascript"; starter_code:str|None=None; expected_output:str|None=None; is_published:bool=False
class SubmissionCreate(BaseModel): exercise_id:str|None=None; lesson_id:str|None=None; source_code:str=Field(...,max_length=20000); runtime:str|None=None
def exout(e): return {"id":str(e.id),"lesson_id":str(e.lesson_id),"title":e.title,"prompt":e.prompt,"runtime":e.runtime,"starter_code":e.starter_code,"is_published":e.is_published}
@router.post("/exercises",status_code=201)
async def create(p:ExerciseCreate,current_user:Dict[str,Any]=Depends(get_instructor_user),db:Session=Depends(get_db)):
    if p.runtime not in {"javascript"}: raise HTTPException(422,"Unsupported runtime; only javascript is currently available")
    e=CodeExercise(**p.model_dump()); db.add(e); db.commit(); db.refresh(e); return exout(e)
@router.get("/exercises/{exercise_id}")
async def get(exercise_id:str,current_user:Dict[str,Any]=Depends(get_student_user),db:Session=Depends(get_db)):
    e=db.query(CodeExercise).filter(CodeExercise.id==exercise_id,CodeExercise.is_published.is_(True)).first()
    if not e: raise HTTPException(404,"Exercise not found")
    return exout(e)
@router.post("/code/submissions",status_code=201)
async def submit_legacy(p:SubmissionCreate, current_user:Dict[str,Any]=Depends(get_student_user),db:Session=Depends(get_db)):
    exercise_id=p.exercise_id
    if not exercise_id and p.lesson_id:
        exercise=db.query(CodeExercise).filter(CodeExercise.lesson_id==p.lesson_id,CodeExercise.is_published.is_(True)).first(); exercise_id=str(exercise.id) if exercise else None
    if not exercise_id: raise HTTPException(422,"exercise_id or lesson_id is required")
    result=await submit(exercise_id,p,current_user,db); result["submission_id"]=result["id"]; return result
@router.post("/exercises/{exercise_id}/submissions",status_code=201)
async def submit(exercise_id:str,p:SubmissionCreate,current_user:Dict[str,Any]=Depends(get_student_user),db:Session=Depends(get_db)):
    e=db.query(CodeExercise).filter(CodeExercise.id==exercise_id,CodeExercise.is_published.is_(True)).first()
    if not e: raise HTTPException(404,"Exercise not found")
    if e.runtime!="javascript": raise HTTPException(422,"Unsupported runtime")
    # Validate syntax only; execution happens in the frontend Web Worker sandbox.
    if any(token in p.source_code for token in ("eval(","Function(","import ","require(","fetch(","XMLHttpRequest")): status="rejected"; output="Unsafe JavaScript construct"
    else:
        pairs={"(":")","{":"}","[":"]"}; stack=[]
        for char in p.source_code:
            if char in pairs: stack.append(pairs[char])
            elif char in ")} ]".replace(" ","") and (not stack or stack.pop()!=char): stack=["invalid"]; break
        status="accepted" if not stack else "rejected"; output="Submission accepted for sandbox execution" if status=="accepted" else "Unbalanced JavaScript delimiters"
    s=CodeSubmission(exercise_id=e.id,user_id=current_user["sub"],source_code=p.source_code,status=status,output=output); db.add(s); db.commit(); db.refresh(s)
    return {"id":str(s.id),"status":status,"output":output,"score":s.score,"created_at":s.created_at}
@router.get("/code/submissions/{submission_id}")
async def get_submission(submission_id:str,current_user:Dict[str,Any]=Depends(get_student_user),db:Session=Depends(get_db)):
    s=db.query(CodeSubmission).filter(CodeSubmission.id==submission_id,CodeSubmission.user_id==current_user["sub"]).first()
    if not s: raise HTTPException(404,"Submission not found")
    return {"id":str(s.id),"status":s.status,"output":s.output,"score":s.score,"created_at":s.created_at}
@router.get("/code/submissions")
async def list_submissions(lesson_id:str|None=None,current_user:Dict[str,Any]=Depends(get_student_user),db:Session=Depends(get_db)):
    q=db.query(CodeSubmission).filter(CodeSubmission.user_id==current_user["sub"])
    if lesson_id: q=q.join(CodeExercise,CodeSubmission.exercise_id==CodeExercise.id).filter(CodeExercise.lesson_id==lesson_id)
    return [{"submission_id":str(s.id),"id":str(s.id),"status":s.status,"output":s.output,"score":s.score,"created_at":s.created_at} for s in q.order_by(CodeSubmission.created_at.desc()).limit(50).all()]
