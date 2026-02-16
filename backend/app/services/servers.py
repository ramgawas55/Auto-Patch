from datetime import datetime, timedelta, timezone


def compute_server_status(last_seen: datetime | None, updates_count: int, security_updates_count: int, reboot_required: bool) -> str:
    if last_seen is None:
        return "offline"
    if datetime.now(timezone.utc) - last_seen > timedelta(minutes=10):
        return "offline"
    if security_updates_count > 0:
        return "security"
    if updates_count > 0:
        return "updates"
    if reboot_required:
        return "reboot"
    return "up_to_date"
