import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Job, JobResult, Server
from app.deps import get_db
from app.schemas import AgentHeartbeat, AgentJobResultIn
from app.services.audit import create_audit
from app.services.inventory import store_inventory
from app.services.jobs import resolve_job_status
from app.services.alerts import send_telegram


router = APIRouter(prefix="/agent", tags=["agent"])

rate_state: dict[str, datetime] = {}


def enforce_rate_limit(token: str):
    if not settings.agent_rate_limit_seconds:
        return
    now = datetime.now(timezone.utc)
    last = rate_state.get(token)
    if last and (now - last).total_seconds() < settings.agent_rate_limit_seconds:
        raise HTTPException(status_code=429, detail="Rate limit")
    rate_state[token] = now


def get_server_by_token(db: Session, token: str) -> Server:
    server = db.query(Server).filter(Server.agent_token == token).first()
    if not server:
        raise HTTPException(status_code=401, detail="Invalid agent token")
    return server


@router.post("/register")
async def register_agent(request: Request, db: Session = Depends(get_db)):
    bootstrap = request.headers.get("X-BOOTSTRAP-TOKEN")
    if not settings.agent_bootstrap_token or bootstrap != settings.agent_bootstrap_token:
        raise HTTPException(status_code=401, detail="Invalid bootstrap token")
    body = await await_json(request)
    hostname = body.get("hostname")
    ip = body.get("ip")
    os_name = body.get("os_name")
    os_version = body.get("os_version")
    kernel_version = body.get("kernel_version")
    package_manager = body.get("package_manager")
    if not hostname or not ip:
        raise HTTPException(status_code=400, detail="Missing host identity")
    existing = db.query(Server).filter(Server.hostname == hostname, Server.ip == ip).first()
    token = secrets.token_hex(24)
    if existing:
        existing.agent_token = token
        existing.os_name = os_name or existing.os_name
        existing.os_version = os_version or existing.os_version
        existing.kernel_version = kernel_version or existing.kernel_version
        existing.package_manager = package_manager or existing.package_manager
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        create_audit(db, "agent", existing.id, "agent_token_rotated", "server", existing.id, hostname)
        return {"agent_token": token, "server_id": existing.id}
    server = Server(
        hostname=hostname,
        ip=ip,
        os_name=os_name or "unknown",
        os_version=os_version or "unknown",
        kernel_version=kernel_version or "unknown",
        package_manager=package_manager or "unknown",
        agent_token=token,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    create_audit(db, "agent", server.id, "agent_registered", "server", server.id, hostname)
    return {"agent_token": token, "server_id": server.id}


@router.post("/rotate-token")
def rotate_agent_token(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("X-AGENT-TOKEN")
    if not token:
        raise HTTPException(status_code=401, detail="Missing agent token")
    enforce_rate_limit(token)
    server = get_server_by_token(db, token)
    new_token = secrets.token_hex(24)
    server.agent_token = new_token
    server.updated_at = datetime.now(timezone.utc)
    db.commit()
    create_audit(db, "agent", server.id, "agent_token_rotated", "server", server.id, server.hostname)
    return {"agent_token": new_token}


@router.post("/heartbeat")
def heartbeat(payload: AgentHeartbeat, request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("X-AGENT-TOKEN")
    if not token:
        raise HTTPException(status_code=401, detail="Missing agent token")
    enforce_rate_limit(token)
    server = get_server_by_token(db, token)
    server.last_seen = datetime.now(timezone.utc)
    db.commit()
    store_inventory(db, server, payload.inventory)
    if len(payload.inventory.security_updates) > 0:
        send_telegram(f"Security updates available on {server.hostname} ({server.ip})")
    create_audit(db, "agent", server.id, "heartbeat", "server", server.id, server.hostname)
    return {"status": "ok"}


@router.get("/jobs/poll")
def poll_job(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("X-AGENT-TOKEN")
    if not token:
        raise HTTPException(status_code=401, detail="Missing agent token")
    enforce_rate_limit(token)
    server = get_server_by_token(db, token)
    job = (
        db.query(Job)
        .filter(Job.server_id == server.id, Job.status == "QUEUED")
        .order_by(Job.created_at.asc())
        .first()
    )
    if not job:
        return {"job": None}
    job.status = "RUNNING"
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    create_audit(db, "agent", server.id, "job_started", "job", job.id, job.job_type)
    return {"job": {"id": job.id, "job_type": job.job_type}}


@router.post("/jobs/{job_id}/result")
def submit_job_result(job_id: int, payload: AgentJobResultIn, request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("X-AGENT-TOKEN")
    if not token:
        raise HTTPException(status_code=401, detail="Missing agent token")
    enforce_rate_limit(token)
    server = get_server_by_token(db, token)
    job = db.query(Job).filter(Job.id == job_id, Job.server_id == server.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    status = resolve_job_status(payload.exit_code, payload.status)
    result = JobResult(
        job_id=job.id,
        started_at=payload.started_at,
        finished_at=payload.finished_at,
        exit_code=payload.exit_code,
        stdout=payload.stdout,
        stderr=payload.stderr,
        status=status,
    )
    db.add(result)
    job.status = status
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    store_inventory(db, server, payload.inventory)
    if status == "FAILED":
        send_telegram(f"Patch job failed on {server.hostname} ({server.ip})")
    create_audit(db, "agent", server.id, "job_result", "job", job.id, status)
    return {"status": status}


async def await_json(request: Request) -> dict:
    try:
        return await request.json()
    except Exception:
        return {}
