from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Job, JobResult, Server, User
from app.deps import get_current_user, get_db
from app.schemas import JobCreate, JobOut, JobResultOut
from app.services.audit import create_audit


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobOut)
def create_job(payload: JobCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == payload.server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    status = "PENDING_APPROVAL" if payload.requires_approval else "APPROVED"
    job = Job(
        server_id=payload.server_id,
        job_type=payload.job_type,
        status=status,
        scheduled_at=payload.scheduled_at,
        requires_approval=payload.requires_approval,
        created_by=user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    create_audit(db, "user", user.id, "job_created", "job", job.id, f"{job.job_type} for server {server.hostname}")
    return job


@router.get("", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Job).order_by(Job.created_at.desc()).all()


@router.get("/{job_id}/results", response_model=list[JobResultOut])
def list_job_results(job_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(JobResult).filter(JobResult.job_id == job_id).order_by(JobResult.id.desc()).all()
