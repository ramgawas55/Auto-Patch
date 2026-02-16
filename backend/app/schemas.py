from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "operator"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ServerBase(BaseModel):
    hostname: str
    ip: str
    os_name: str
    os_version: str
    kernel_version: str
    package_manager: str
    last_update_time: Optional[datetime]


class ServerOut(ServerBase):
    id: int
    last_seen: Optional[datetime]
    status: str

    class Config:
        from_attributes = True


class UpdateOut(BaseModel):
    id: int
    name: str
    current_version: Optional[str]
    candidate_version: Optional[str]
    is_security: bool

    class Config:
        from_attributes = True


class InventoryOut(BaseModel):
    id: int
    collected_at: datetime
    hostname: str
    ip: str
    os_name: str
    os_version: str
    kernel_version: str
    package_manager: str
    last_update_time: Optional[datetime]
    reboot_required: bool
    security_updates_count: int
    updates_count: int
    updates: List[UpdateOut]

    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    server_id: int
    job_type: str
    scheduled_at: Optional[datetime] = None
    requires_approval: bool = True


class JobOut(BaseModel):
    id: int
    server_id: int
    job_type: str
    status: str
    scheduled_at: Optional[datetime]
    requires_approval: bool
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    approval_reason: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobResultOut(BaseModel):
    id: int
    job_id: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    status: str

    class Config:
        from_attributes = True


class AuditLogOut(BaseModel):
    id: int
    actor_type: str
    actor_id: Optional[int]
    action: str
    target_type: Optional[str]
    target_id: Optional[int]
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateIn(BaseModel):
    name: str
    current_version: Optional[str]
    candidate_version: Optional[str]
    is_security: bool


class InventoryIn(BaseModel):
    hostname: str
    ip: str
    os_name: str
    os_version: str
    kernel_version: str
    package_manager: str
    last_update_time: Optional[datetime]
    reboot_required: bool
    updates: List[UpdateIn]
    security_updates: List[UpdateIn]


class AgentHeartbeat(BaseModel):
    inventory: InventoryIn


class AgentJobResultIn(BaseModel):
    job_id: int
    started_at: datetime
    finished_at: datetime
    exit_code: int
    stdout: str
    stderr: str
    status: str
    inventory: InventoryIn


class ApprovalAction(BaseModel):
    reason: Optional[str] = None
