
from datetime import datetime, date

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Float,
    Text,
    Index,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from database.database import Base


class PortalUser(Base):
    """Portal login credentials stored in the database (bcrypt hash).

    role: employee | tower_head | assignee | admin
    """
    __tablename__ = "portal_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, default="")
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="employee", index=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PortalSession(Base):
    """Server-side session record. Token validity = row exists + not expired.

    Logout deletes the row; each login inserts a fresh token (jti), so a new
    token is always prompted/issued per login and old ones die with logout.
    """
    __tablename__ = "portal_sessions"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(64), unique=True, nullable=False, index=True)
    portal_user_id = Column(Integer, ForeignKey("portal_users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("PortalUser")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    vendor = Column(String(255))
    category = Column(String(100))
    owner = Column(String(255))
    environment = Column(String(100))
    status = Column(String(50), default="Active")
    last_sync = Column(DateTime)

    licenses = relationship(
        "License",
        back_populates="application",
        cascade="all, delete-orphan",
    )


class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("applications.id"),
        nullable=False,
    )

    product = Column(String(255))
    license_type = Column(String(100))

    purchased_qty = Column(Integer)
    assigned_qty = Column(Integer)
    available_qty = Column(Integer)
    used_qty = Column(Integer)

    cost = Column(Float)
    currency = Column(String(20))
    billing_cycle = Column(String(50))
    renewal_date = Column(Date)

    data_source = Column(String(255))
    last_updated = Column(DateTime, default=datetime.utcnow)

    application = relationship(
        "Application",
        back_populates="licenses",
    )


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    active = Column(Boolean, nullable=False, default=True)

    users = relationship(
        "User",
        back_populates="department",
    )
    approver_mapping = relationship(
        "DepartmentApprover",
        back_populates="department",
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("applications.id"),
        nullable=True,
    )

    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=True,
        index=True,
    )

    external_user_id = Column(String(255))
    name = Column(String(255))
    email = Column(String(255))
    status = Column(String(50))
    role = Column(String(100))
    job_title = Column(String(255))
    last_activity = Column(DateTime)

    department = relationship(
        "Department",
        back_populates="users",
    )
    submitted_license_requests = relationship(
        "LicenseRequest",
        foreign_keys="LicenseRequest.user_id",
        back_populates="employee",
    )
    department_approver_mappings = relationship(
        "DepartmentApprover",
        back_populates="employee",
        foreign_keys="DepartmentApprover.employee_id",
    )


class DepartmentApprover(Base):
    __tablename__ = "department_approvers"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )
    employee_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    approver_name = Column(String(255), nullable=False)
    approver_email = Column(String(255))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    department = relationship("Department", back_populates="approver_mapping")
    employee = relationship(
        "User",
        back_populates="department_approver_mappings",
        foreign_keys=[employee_id],
    )
    approvals = relationship("LicenseApproval", back_populates="approver")


class LicenseRequest(Base):
    __tablename__ = "license_requests"
    __table_args__ = (
        Index("uq_license_requests_request_number", "request_number", unique=True),
        Index(
            "uq_license_requests_employee_idempotency",
            "employee_id",
            "idempotency_key",
            unique=True,
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column("request_number", String(64), nullable=False)
    idempotency_key = Column(String(64))
    user_id = Column("employee_id", Integer, ForeignKey("users.id"), nullable=False, index=True)
    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False, index=True)
    approver_id = Column(
        Integer,
        ForeignKey("department_approvers.id"),
        nullable=True,
        index=True,
    )
    business_justification = Column(Text, nullable=False)
    urgency = Column(String(64), nullable=False, default="Standard")
    status = Column(String(30), default="Pending Approval", index=True)
    requested_at = Column("submission_timestamp", DateTime, default=datetime.utcnow)
    provisioning_status = Column(String(50))
    failure_details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    requested_duration = Column(String(50))
    requester_identity = Column(String(255))

    employee = relationship("User", foreign_keys=[user_id], back_populates="submitted_license_requests")
    department = relationship("Department")
    license = relationship("License")
    approver = relationship("DepartmentApprover", foreign_keys=[approver_id])
    approvals = relationship(
        "LicenseApproval",
        back_populates="request",
        order_by="LicenseApproval.created_at",
    )


class LicenseApproval(Base):
    __tablename__ = "license_approvals"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(
        Integer,
        ForeignKey("license_requests.id"),
        nullable=False,
        index=True,
    )
    approver_id = Column(
        Integer,
        ForeignKey("department_approvers.id"),
        nullable=True,
        index=True,
    )
    stage = Column(String(64), nullable=False, default="tower_head", index=True)
    approver_email = Column(String(255), nullable=True, index=True)
    status = Column("decision", String(20), nullable=False, default="Pending", index=True)
    comments = Column(Text)
    decision_at = Column("decision_timestamp", DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    request = relationship("LicenseRequest", back_populates="approvals")
    approver = relationship("DepartmentApprover", back_populates="approvals")

    STAGE_LABELS = {
        "tower_head": "Tower Head Approval",
        "assignee": "Assignee Approval",
        "final": "Final Approval",
    }


class LicenseAssignment(Base):
    __tablename__ = "license_assignments"

    id = Column(Integer, primary_key=True, index=True)

    license_id = Column(
        Integer,
        ForeignKey("licenses.id"),
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
    )

    assigned_date = Column(DateTime)
    status = Column(String(50))


class LicenseAssignedUser(Base):
    __tablename__ = "license_assigned_users"

    __table_args__ = (
        UniqueConstraint(
            "license_id",
            "user_id",
            name="uq_license_assigned_users_license_user",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("applications.id"),
        nullable=False,
        index=True,
    )

    license_id = Column(
        Integer,
        ForeignKey("licenses.id"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    sku_id = Column(String(255))
    display_name = Column(String(255))
    email = Column(String(255))

    # Keep this as a text snapshot for existing license assignment data.
    department = Column(String(255))

    external_user_id = Column(String(255))
    status = Column(String(50), default="assigned")
    assigned_at = Column(DateTime, default=datetime.utcnow)
    last_synced_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    application = relationship("Application")
    license = relationship("License")
    user = relationship("User")


class Microsoft365Data(Base):
    __tablename__ = "microsoft365_data"

    __table_args__ = (
        UniqueConstraint(
            "application_id",
            "sku_id",
            name="uq_microsoft365_data_application_sku",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("applications.id"),
        nullable=False,
        index=True,
    )

    sku_id = Column(String(255), nullable=False)
    product = Column(String(255))
    sku_part_number = Column(String(255))
    license_type = Column(String(255))
    purchased_quantity = Column(Integer)
    assigned_quantity = Column(Integer)
    available_quantity = Column(Integer)
    consumed_quantity = Column(Integer)

    synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    application = relationship("Application")


class SlackData(Base):
    __tablename__ = "slack_data"

    __table_args__ = (
        UniqueConstraint(
            "application_id",
            "plan",
            "license_type",
            name="uq_slack_data_application_plan_type",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("applications.id"),
        nullable=False,
        index=True,
    )

    plan = Column(String(255))
    license_type = Column(String(255))
    purchased_quantity = Column(Integer)
    entitled_quantity = Column(Integer)
    assigned_quantity = Column(Integer)
    available_quantity = Column(Integer)
    active_users = Column(Integer)
    inactive_users = Column(Integer)
    renewal_date = Column(Date)
    cost = Column(Float)
    currency = Column(String(20))
    billing_cycle = Column(String(50))
    data_source = Column(String(255))

    synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    application = relationship("Application")


class Usage(Base):
    __tablename__ = "usage"

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("applications.id"),
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
    )

    last_activity = Column(DateTime)
    usage_status = Column(String(50))
    usage_count = Column(Integer)

    last_updated = Column(
        DateTime,
        default=datetime.utcnow,
    )


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("applications.id"),
    )

    contract_id = Column(String(255))
    vendor = Column(String(255))
    purchased_qty = Column(Integer)
    cost = Column(Float)
    currency = Column(String(20))
    renewal_date = Column(Date)
    source_document = Column(Text)


class SyncLog(Base):
    __tablename__ = "sync_log"

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("applications.id"),
    )

    sync_time = Column(
        DateTime,
        default=datetime.utcnow,
    )

    status = Column(String(50))
    records_processed = Column(Integer)
    error_message = Column(Text)
