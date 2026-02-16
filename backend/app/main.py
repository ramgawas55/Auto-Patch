import threading
import time
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.db.models import User
from app.routers import agent, approvals, audit, auth, jobs, servers, users
from app.services.jobs import queue_due_jobs
from app.services.alerts import check_offline_servers


app = FastAPI(title=settings.app_name)

allowed_origins = ["http://localhost:3000"]
if settings.frontend_origin:
    allowed_origins.append(settings.frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(servers.router, prefix=settings.api_prefix)
app.include_router(jobs.router, prefix=settings.api_prefix)
app.include_router(approvals.router, prefix=settings.api_prefix)
app.include_router(audit.router, prefix=settings.api_prefix)
app.include_router(agent.router, prefix=settings.api_prefix)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


def scheduler_loop():
    while True:
        db = SessionLocal()
        try:
            queue_due_jobs(db)
            check_offline_servers(db)
        finally:
            db.close()
        time.sleep(30)


@app.on_event("startup")
def seed_admin_and_scheduler():
    db = SessionLocal()
    try:
        if settings.admin_email and settings.admin_password:
            existing = db.query(User).filter(User.email == settings.admin_email).first()
            if not existing:
                user = User(
                    email=settings.admin_email,
                    password_hash=hash_password(settings.admin_password),
                    role="admin",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(user)
                db.commit()
    finally:
        db.close()
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()
