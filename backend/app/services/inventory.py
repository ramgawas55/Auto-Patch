from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Inventory, Update, Server
from app.schemas import InventoryIn


def store_inventory(db: Session, server: Server, inventory_in: InventoryIn) -> Inventory:
    inventory = Inventory(
        server_id=server.id,
        collected_at=datetime.now(timezone.utc),
        hostname=inventory_in.hostname,
        ip=inventory_in.ip,
        os_name=inventory_in.os_name,
        os_version=inventory_in.os_version,
        kernel_version=inventory_in.kernel_version,
        package_manager=inventory_in.package_manager,
        last_update_time=inventory_in.last_update_time,
        reboot_required=inventory_in.reboot_required,
        security_updates_count=len(inventory_in.security_updates),
        updates_count=len(inventory_in.updates),
    )
    db.add(inventory)
    db.flush()
    for update in inventory_in.updates:
        db.add(
            Update(
                inventory_id=inventory.id,
                name=update.name,
                current_version=update.current_version,
                candidate_version=update.candidate_version,
                is_security=update.is_security,
            )
        )
    for update in inventory_in.security_updates:
        db.add(
            Update(
                inventory_id=inventory.id,
                name=update.name,
                current_version=update.current_version,
                candidate_version=update.candidate_version,
                is_security=True,
            )
        )
    server.hostname = inventory_in.hostname
    server.ip = inventory_in.ip
    server.os_name = inventory_in.os_name
    server.os_version = inventory_in.os_version
    server.kernel_version = inventory_in.kernel_version
    server.package_manager = inventory_in.package_manager
    server.last_update_time = inventory_in.last_update_time
    server.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(inventory)
    return inventory
