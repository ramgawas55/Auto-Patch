from sqlalchemy.orm import Session

from app.db.models import AuditLog


def create_audit(
    db: Session,
    actor_type: str,
    actor_id: int | None,
    action: str,
    target_type: str | None = None,
    target_id: int | None = None,
    message: str | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        message=message,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
