from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.db.models import Inventory, Job, Server, Update
import secrets
from datetime import datetime, timezone

from app.deps import get_current_admin, get_current_user, get_db
from app.services.audit import create_audit
from app.schemas import InventoryOut, JobOut, ServerOut, UpdateOut
from app.services.servers import compute_server_status


router = APIRouter(prefix="/servers", tags=["servers"])


@router.get("", response_model=list[ServerOut])
def list_servers(db: Session = Depends(get_db), _: str = Depends(get_current_user)):
    latest_subq = (
        db.query(Inventory.server_id, func.max(Inventory.collected_at).label("max_time"))
        .group_by(Inventory.server_id)
        .subquery()
    )
    latest_inventory = (
        db.query(Inventory)
        .join(latest_subq, (Inventory.server_id == latest_subq.c.server_id) & (Inventory.collected_at == latest_subq.c.max_time))
        .all()
    )
    inventory_map = {inv.server_id: inv for inv in latest_inventory}
    servers = db.query(Server).all()
    results = []
    for server in servers:
        inv = inventory_map.get(server.id)
        updates_count = inv.updates_count if inv else 0
        security_count = inv.security_updates_count if inv else 0
        reboot_required = inv.reboot_required if inv else False
        status = compute_server_status(server.last_seen, updates_count, security_count, reboot_required)
        results.append(
            ServerOut(
                id=server.id,
                hostname=server.hostname,
                ip=server.ip,
                os_name=server.os_name,
                os_version=server.os_version,
                kernel_version=server.kernel_version,
                package_manager=server.package_manager,
                last_update_time=server.last_update_time,
                last_seen=server.last_seen,
                status=status,
            )
        )
    return results


@router.get("/{server_id}/inventory", response_model=InventoryOut)
def get_server_inventory(server_id: int, db: Session = Depends(get_db), _: str = Depends(get_current_user)):
    inventory = (
        db.query(Inventory)
        .filter(Inventory.server_id == server_id)
        .order_by(Inventory.collected_at.desc())
        .first()
    )
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    updates = db.query(Update).filter(Update.inventory_id == inventory.id).all()
    inventory.updates = updates
    return inventory


@router.get("/{server_id}/jobs", response_model=list[JobOut])
def list_server_jobs(server_id: int, db: Session = Depends(get_db), _: str = Depends(get_current_user)):
    return db.query(Job).filter(Job.server_id == server_id).order_by(Job.created_at.desc()).all()


@router.get("/{server_id}/updates", response_model=list[UpdateOut])
def list_server_updates(server_id: int, db: Session = Depends(get_db), _: str = Depends(get_current_user)):
    inventory = (
        db.query(Inventory)
        .filter(Inventory.server_id == server_id)
        .order_by(Inventory.collected_at.desc())
        .first()
    )
    if not inventory:
        return []
    return db.query(Update).filter(Update.inventory_id == inventory.id).all()


@router.post("/{server_id}/rotate-token")
def rotate_agent_token(server_id: int, db: Session = Depends(get_db), user=Depends(get_current_admin)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    server.agent_token = secrets.token_hex(24)
    server.updated_at = datetime.now(timezone.utc)
    db.commit()
    create_audit(db, "user", user.id, "agent_token_rotated", "server", server.id, server.hostname)
    return {"agent_token": server.agent_token}
