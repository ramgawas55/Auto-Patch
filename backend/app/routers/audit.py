from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import AuditLog, User
from app.deps import get_current_user, get_db
from app.schemas import AuditLogOut


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(500).all()
