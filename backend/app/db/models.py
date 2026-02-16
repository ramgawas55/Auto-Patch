from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="operator")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True)
    hostname = Column(String(255), nullable=False)
    ip = Column(String(64), nullable=False)
    os_name = Column(String(128), nullable=False)
    os_version = Column(String(128), nullable=False)
    kernel_version = Column(String(128), nullable=False)
    package_manager = Column(String(32), nullable=False)
    last_update_time = Column(DateTime(timezone=True), nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    agent_token = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    inventories = relationship("Inventory", back_populates="server")
    jobs = relationship("Job", back_populates="server")


class Inventory(Base):
    __tablename__ = "inventories"

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    collected_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    hostname = Column(String(255), nullable=False)
    ip = Column(String(64), nullable=False)
    os_name = Column(String(128), nullable=False)
    os_version = Column(String(128), nullable=False)
    kernel_version = Column(String(128), nullable=False)
    package_manager = Column(String(32), nullable=False)
    last_update_time = Column(DateTime(timezone=True), nullable=True)
    reboot_required = Column(Boolean, default=False, nullable=False)
    security_updates_count = Column(Integer, default=0, nullable=False)
    updates_count = Column(Integer, default=0, nullable=False)

    server = relationship("Server", back_populates="inventories")
    updates = relationship("Update", back_populates="inventory", cascade="all, delete-orphan")


class Update(Base):
    __tablename__ = "updates"

    id = Column(Integer, primary_key=True)
    inventory_id = Column(Integer, ForeignKey("inventories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    current_version = Column(String(128), nullable=True)
    candidate_version = Column(String(128), nullable=True)
    is_security = Column(Boolean, default=False, nullable=False)

    inventory = relationship("Inventory", back_populates="updates")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    job_type = Column(String(64), nullable=False)
    status = Column(String(64), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    requires_approval = Column(Boolean, default=False, nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_reason = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    server = relationship("Server", back_populates="jobs")
    results = relationship("JobResult", back_populates="job", cascade="all, delete-orphan")


class JobResult(Base):
    __tablename__ = "job_results"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    status = Column(String(64), nullable=False)

    job = relationship("Job", back_populates="results")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    actor_type = Column(String(32), nullable=False)
    actor_id = Column(Integer, nullable=True)
    action = Column(String(128), nullable=False)
    target_type = Column(String(64), nullable=True)
    target_id = Column(Integer, nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
