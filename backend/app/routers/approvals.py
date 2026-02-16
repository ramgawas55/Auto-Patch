from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Job, User
from app.deps import get_current_user, get_db
from app.schemas import ApprovalAction, JobOut
from app.services.audit import create_audit


router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=list[JobOut])
def list_pending_approvals(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Job).filter(Job.status == "PENDING_APPROVAL").order_by(Job.created_at.desc()).all()


@router.post("/{job_id}/approve", response_model=JobOut)
def approve_job(job_id: int, payload: ApprovalAction, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "APPROVED"
    job.approved_by = user.id
    job.approved_at = datetime.now(timezone.utc)
    job.approval_reason = payload.reason
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    create_audit(db, "user", user.id, "job_approved", "job", job.id, payload.reason)
    return job


@router.post("/{job_id}/deny", response_model=JobOut)
def deny_job(job_id: int, payload: ApprovalAction, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "DENIED"
    job.approved_by = user.id
    job.approved_at = datetime.now(timezone.utc)
    job.approval_reason = payload.reason
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    create_audit(db, "user", user.id, "job_denied", "job", job.id, payload.reason)
    return job
