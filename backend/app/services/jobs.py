from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Job


def queue_due_jobs(db: Session, now: datetime | None = None) -> int:
    if now is None:
        now = datetime.now(timezone.utc)
    due_jobs = (
        db.query(Job)
        .filter(Job.status == "APPROVED")
        .filter((Job.scheduled_at == None) | (Job.scheduled_at <= now))
        .all()
    )
    for job in due_jobs:
        job.status = "QUEUED"
        job.updated_at = now
    db.commit()
    return len(due_jobs)


def resolve_job_status(exit_code: int, status: str | None) -> str:
    if status in {"COMPLETED", "FAILED"}:
        return status
    return "COMPLETED" if exit_code == 0 else "FAILED"
