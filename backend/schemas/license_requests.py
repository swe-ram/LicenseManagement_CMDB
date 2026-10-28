from datetime import datetime

from typing import Literal

from pydantic import BaseModel, Field


class LicenseRequestCreate(BaseModel):
    user_id: int = Field(gt=0)
    idempotency_key: str = Field(min_length=16, max_length=64)
    department: str = Field(min_length=1, max_length=255)
    application_name: str = Field(min_length=1, max_length=255)
    license_id: int = Field(gt=0)
    business_justification: str = Field(min_length=1, max_length=10000)
    urgency: Literal["Standard", "Urgent", "Immediate Project Blocker"] = "Standard"


class ApprovalDecision(BaseModel):
    decision: Literal["Approved", "Rejected"]
    comments: str | None = Field(default=None, max_length=5000)


class DepartmentApproverAssignment(BaseModel):
    department_id: int = Field(gt=0)
    approver_user_id: int = Field(gt=0)


class ApprovalRead(BaseModel):
    id: int
    approver_name: str
    decision: str
    stage: str
    decision_at: datetime | None
    comments: str | None
    created_at: datetime | None


class LicenseRequestRead(BaseModel):
    id: int
    request_id: str
    user_id: int
    employee_name: str
    employee_email: str | None
    department: str
    application: str
    license_id: int
    license_type: str | None
    license_name: str | None
    business_justification: str
    urgency: str
    requested_at: datetime | None
    status: str
    provisioning_status: str | None = None
    approver_id: int | None
    approver_name: str | None
    requester_identity: str | None = None
    test_mode: bool = False
    can_decide: bool = False


class LicenseRequestDetail(LicenseRequestRead):
    approvals: list[ApprovalRead] = Field(default_factory=list)
