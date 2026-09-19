"""Learner accountability matching and progress APIs."""
import secrets
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.dependencies import get_db
from app.security import get_current_user, decode_token
from app.db.mongodb import get_mongodb
from bson import ObjectId
from app.models.accountability import AccountabilityCluster, AccountabilityClusterMembership, AccountabilityMatchQueue, ClusterStatus, QueueStatus
from app.models.user import User
from app.models.enrollment import UserProgress
from app.models.progress import Streak
from app.models.community import CommunityReport, CommunityBlock

router = APIRouter(prefix="/api/v1/accountability", tags=["Accountability"])
ADJECTIVES = ("Bright", "Curious", "Bold", "Brave", "Focused", "Rising", "Swift", "Clever")
NOUNS = ("Sparks", "Voyagers", "Builders", "Pathfinders", "Minds", "Pioneers", "Coders", "Trailblazers")
class ReportRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)
class MessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)

def uid(current_user: dict) -> UUID: return UUID(str(current_user["sub"]))
def unique_name(db: Session) -> str:
    for _ in range(100):
        name = f"{secrets.choice(ADJECTIVES)} {secrets.choice(NOUNS)} {secrets.randbelow(900)+100}"
        if not db.query(AccountabilityCluster).filter_by(name=name).first(): return name
    raise HTTPException(503, "Unable to generate a unique cluster name")

def active_membership(db: Session, user_id: UUID):
    return db.query(AccountabilityClusterMembership).filter(AccountabilityClusterMembership.user_id == user_id, AccountabilityClusterMembership.left_at.is_(None)).first()
def require_cluster(db: Session, user_id: UUID):
    membership=active_membership(db,user_id)
    if not membership: raise HTTPException(403,"Active accountability membership required")
    return membership

@router.get("/status")
def status_view(current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    user_id=uid(current_user); membership=active_membership(db,user_id); queue=db.query(AccountabilityMatchQueue).filter_by(user_id=user_id).first()
    if membership:
        cluster=db.query(AccountabilityCluster).get(membership.cluster_id)
        return {"status":"active","cluster":{"id":str(cluster.id),"name":cluster.name,"capacity":cluster.capacity,"created_at":cluster.created_at.isoformat()}}
    return {"status": queue.status.value if queue else "not_queued", "queued_at": queue.queued_at.isoformat() if queue else None, "message":"Groups form at 15 learners or after 7 days with at least 3."}

@router.post("/queue", status_code=201)
def join_queue(current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    user_id=uid(current_user)
    if active_membership(db,user_id): return status_view(current_user,db)
    queue=db.query(AccountabilityMatchQueue).filter_by(user_id=user_id).first()
    if not queue: queue=AccountabilityMatchQueue(user_id=user_id); db.add(queue)
    queue.status=QueueStatus.WAITING; queue.queued_at=datetime.utcnow(); db.commit()
    return status_view(current_user,db)

@router.post("/leave")
def leave_queue(current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    user_id=uid(current_user); membership=active_membership(db,user_id)
    if membership: membership.left_at=datetime.utcnow()
    queue=db.query(AccountabilityMatchQueue).filter_by(user_id=user_id).first()
    if queue: queue.status=QueueStatus.LEFT
    db.commit(); return {"status":"left"}

@router.get("/cluster")
def cluster_view(current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    membership=active_membership(db,uid(current_user))
    if not membership: raise HTTPException(404,"Learner is not in a cluster")
    cluster=db.query(AccountabilityCluster).get(membership.cluster_id)
    members=db.query(AccountabilityClusterMembership,User).join(User,User.id==AccountabilityClusterMembership.user_id).filter(AccountabilityClusterMembership.cluster_id==cluster.id,AccountabilityClusterMembership.left_at.is_(None)).all()
    return {"id":str(cluster.id),"name":cluster.name,"capacity":cluster.capacity,"members":[{"id":str(u.id),"display_name":f"{u.first_name} {u.last_name[:1]}."} for _,u in members]}

@router.get("/cluster/progress")
def cluster_progress(current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    membership=require_cluster(db,uid(current_user)); rows=db.query(AccountabilityClusterMembership,User,Streak).join(User,User.id==AccountabilityClusterMembership.user_id).outerjoin(Streak,Streak.user_id==User.id).filter(AccountabilityClusterMembership.cluster_id==membership.cluster_id,AccountabilityClusterMembership.left_at.is_(None)).all()
    return {"data":[{"display_name":f"{u.first_name} {u.last_name[:1]}.","completed_lessons":db.query(UserProgress).filter(UserProgress.user_id==u.id,UserProgress.is_completed.is_(True)).count(),"current_streak":s.current_streak_count if s else 0,"last_active_date":s.last_activity_date.date().isoformat() if s and s.last_activity_date else None} for _,u,s in rows]}

@router.get("/chat/unread-count")
def unread_count(current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    membership=require_cluster(db,uid(current_user)); count=get_mongodb().accountability_messages.count_documents({"cluster_id":str(membership.cluster_id),"user_id":{"$ne":str(uid(current_user))},"deleted":False})
    return {"count":count}

@router.post("/chat/messages/{message_id}/report", status_code=201)
def report_message(message_id: str, request: ReportRequest, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    require_cluster(db,uid(current_user)); report=CommunityReport(reporter_id=uid(current_user),content_id=f"accountability:{message_id}",reason=request.reason); db.add(report); db.commit(); return {"status":"reported","id":str(report.id)}

@router.post("/chat/users/{user_id}/block", status_code=201)
def block_chat_user(user_id: str, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    require_cluster(db,uid(current_user));
    if str(uid(current_user)) == user_id: raise HTTPException(400,"Cannot block yourself")
    db.add(CommunityBlock(blocker_id=uid(current_user),blocked_user_id=user_id));
    try: db.commit()
    except Exception: db.rollback()
    return {"status":"blocked"}

@router.get("/chat/messages")
def chat_messages(limit: int=50, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    membership=require_cluster(db,uid(current_user)); limit=min(max(limit,1),100); docs=get_mongodb().accountability_messages.find({"cluster_id":str(membership.cluster_id),"deleted":False}).sort("created_at",-1).limit(limit)
    return {"data":[{"id":str(d["_id"]),"user_id":d["user_id"],"content":d["content"],"created_at":d["created_at"]} for d in reversed(list(docs))]}

@router.post("/chat/messages", status_code=201)
def send_chat_message(request: MessageRequest, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    membership=require_cluster(db,uid(current_user)); now=datetime.utcnow(); doc={"cluster_id":str(membership.cluster_id),"user_id":str(uid(current_user)),"content":request.content.strip(),"deleted":False,"created_at":now}; result=get_mongodb().accountability_messages.insert_one(doc); return {"id":str(result.inserted_id),"user_id":doc["user_id"],"content":doc["content"],"created_at":now}

@router.websocket("/chat/ws")
async def chat_socket(websocket: WebSocket, token: str, db: Session=Depends(get_db)):
    try:
        payload=decode_token(token); user_id=UUID(str(payload.get("sub"))); membership=require_cluster(db,user_id)
    except Exception:
        await websocket.close(code=1008); return
    await websocket.accept(); collection=get_mongodb().accountability_messages
    try:
        while True:
            content=(await websocket.receive_text()).strip()
            if not content or len(content)>2000: continue
            now=datetime.utcnow(); doc={"cluster_id":str(membership.cluster_id),"user_id":str(user_id),"content":content,"deleted":False,"created_at":now}; result=collection.insert_one(doc)
            await websocket.send_json({"id":str(result.inserted_id),"user_id":str(user_id),"content":content,"created_at":now.isoformat()})
    except WebSocketDisconnect: return

@router.post("/cluster/report", status_code=201)
def report_cluster(request: ReportRequest, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    if not active_membership(db,uid(current_user)): raise HTTPException(403,"Cluster membership required")
    from app.models.outbox import OutboxEvent
    db.add(OutboxEvent(event_type="accountability.moderation_report",payload={"reporter_id":str(uid(current_user)),"reason":request.reason},idempotency_key=f"cluster-report:{uid(current_user)}:{secrets.token_hex(8)}")); db.commit(); return {"status":"reported"}
