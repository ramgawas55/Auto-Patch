from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Job
from app.services.jobs import queue_due_jobs
from app.services.servers import compute_server_status


def setup_db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_queue_due_jobs():
    db = setup_db()
    now = datetime.now(timezone.utc)
    job_due = Job(server_id=1, job_type="SCAN_NOW", status="APPROVED", scheduled_at=now - timedelta(minutes=1), requires_approval=False, created_at=now, updated_at=now)
    job_future = Job(server_id=1, job_type="SCAN_NOW", status="APPROVED", scheduled_at=now + timedelta(minutes=10), requires_approval=False, created_at=now, updated_at=now)
    db.add(job_due)
    db.add(job_future)
    db.commit()
    queued = queue_due_jobs(db, now=now)
    assert queued == 1
    db.refresh(job_due)
    db.refresh(job_future)
    assert job_due.status == "QUEUED"
    assert job_future.status == "APPROVED"


def test_offline_detection():
    now = datetime.now(timezone.utc)
    status = compute_server_status(now - timedelta(minutes=11), 0, 0, False)
    assert status == "offline"
    status = compute_server_status(now, 1, 0, False)
    assert status == "updates"
    status = compute_server_status(now, 0, 2, False)
    assert status == "security"
    status = compute_server_status(now, 0, 0, True)
    assert status == "reboot"
    status = compute_server_status(now, 0, 0, False)
    assert status == "up_to_date"
