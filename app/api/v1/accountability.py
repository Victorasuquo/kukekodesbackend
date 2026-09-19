"""Learner accountability matching and progress APIs."""
import secrets
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.dependencies import get_db
from app.security import get_current_user
from app.models.accountability import AccountabilityCluster, AccountabilityClusterMembership, AccountabilityMatchQueue, ClusterStatus, QueueStatus
from app.models.user import User

router = APIRouter(prefix="/api/v1/accountability", tags=["Accountability"])
ADJECTIVES = ("Bright", "Curious", "Bold", "Brave", "Focused", "Rising", "Swift", "Clever")
NOUNS = ("Sparks", "Voyagers", "Builders", "Pathfinders", "Minds", "Pioneers", "Coders", "Trailblazers")
class ReportRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)

def uid(current_user: dict) -> UUID: return UUID(str(current_user["sub"]))
def unique_name(db: Session) -> str:
    for _ in range(100):
        name = f"{secrets.choice(ADJECTIVES)} {secrets.choice(NOUNS)} {secrets.randbelow(900)+100}"
        if not db.query(AccountabilityCluster).filter_by(name=name).first(): return name
    raise HTTPException(503, "Unable to generate a unique cluster name")

def active_membership(db: Session, user_id: UUID):
    return db.query(AccountabilityClusterMembership).filter(AccountabilityClusterMembership.user_id == user_id, AccountabilityClusterMembership.left_at.is_(None)).first()

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

@router.post("/cluster/report", status_code=201)
def report_cluster(request: ReportRequest, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    if not active_membership(db,uid(current_user)): raise HTTPException(403,"Cluster membership required")
    from app.models.outbox import OutboxEvent
    db.add(OutboxEvent(event_type="accountability.moderation_report",payload={"reporter_id":str(uid(current_user)),"reason":request.reason},idempotency_key=f"cluster-report:{uid(current_user)}:{secrets.token_hex(8)}")); db.commit(); return {"status":"reported"}
