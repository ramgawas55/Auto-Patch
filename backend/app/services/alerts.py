from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Server


offline_alerted: set[int] = set()


def send_telegram(message: str):
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {"chat_id": settings.telegram_chat_id, "text": message}
    try:
        httpx.post(url, data=payload, timeout=10)
    except Exception:
        return


def check_offline_servers(db: Session):
    now = datetime.now(timezone.utc)
    offline_before = now - timedelta(minutes=10)
    servers = db.query(Server).all()
    for server in servers:
        if server.last_seen and server.last_seen < offline_before:
            if server.id not in offline_alerted:
                send_telegram(f"Server offline: {server.hostname} ({server.ip})")
                offline_alerted.add(server.id)
        else:
            if server.id in offline_alerted:
                offline_alerted.remove(server.id)
