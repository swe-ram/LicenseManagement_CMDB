from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from auth.session import (
    AuthenticatedPrincipal,
    get_current_principal,
    is_loopback_request,
    local_license_request_test_mode_enabled,
    require_role,
)
from database.database import get_db
from database.models import (
    Application,
    Department,
    DepartmentApprover,
    License,
    LicenseApproval,
    LicenseRequest,
    User,
)
from schemas.license_requests import (
    ApprovalDecision,
    ApprovalRead,
    DepartmentApproverAssignment,
    LicenseRequestCreate,
    LicenseRequestDetail,
    LicenseRequestRead,
)


router = APIRouter(prefix="/api/v1/license-requests", tags=["License Requests"])
legacy_router = APIRouter(tags=["License Requests"])

REQUESTER_ROLE = "License.Requester"
APPROVER_ROLE = "License.Approver"
ADMIN_ROLE = "License.Admin"

TOWER_HEAD_EMAIL = "akshayap@clouddestinations.com"
ASSIGNEE_EMAIL = "swethar@clouddestinations.com"

STAGE_ORDER = ["tower_head", "assignee", "final"]
STAGE_LABELS = {
    "tower_head": "Tower Head Approval",
    "assignee": "Assignee Approval",
    "final": "Final Approval",
}


def _portal_email(principal: AuthenticatedPrincipal) -> str:
    return (principal.claims.get("preferred_username") or "").strip().lower()


def _portal_role(principal: AuthenticatedPrincipal) -> str:
    return (principal.claims.get("portal_role") or "").strip().lower()


def _current_stage(request: LicenseRequest) -> str | None:
    for approval in sorted(request.approvals, key=lambda a: (STAGE_ORDER.index(a.stage) if a.stage in STAGE_ORDER else 99, a.id)):
        if approval.status == "Pending":
            return approval.stage
    return None


def _stage_approver_email(db: Session, request: LicenseRequest, stage: str) -> str:
    if stage == "tower_head":
        if request.approver and request.approver.approver_email:
            return request.approver.approver_email.strip().lower()
        return TOWER_HEAD_EMAIL
    if stage == "assignee":
        return ASSIGNEE_EMAIL
    return ""


def _can_decide_stage(principal: AuthenticatedPrincipal, stage: str | None) -> bool:
    if stage is None:
        return False
    email = _portal_email(principal)
    role = _portal_role(principal)
    if role == "admin":
        return stage == "final"
    if stage == "tower_head":
        return email == TOWER_HEAD_EMAIL
    if stage == "assignee":
        return email == ASSIGNEE_EMAIL
    return False


def _is_local_test_session(
    principal: AuthenticatedPrincipal,
    http_request: Request,
) -> bool:
    return (
        principal.claims.get("account_type") == "shared"
        and bool(principal.claims.get("license_request_test_mode"))
        and local_license_request_test_mode_enabled()
        and is_loopback_request(http_request)
    )


def _identity_user_ids(
    db: Session,
    principal: AuthenticatedPrincipal,
    http_request: Request | None = None,
) -> set[int]:
    if principal.claims.get("account_type") == "shared":
        # Shared admin account: in local test mode it may act on behalf of the
        # selected employee / approver chosen in the Requests UI. Outside local
        # test mode it must not impersonate anyone.
        if (
            http_request is not None
            and _is_local_test_session(principal, http_request)
        ):
            return set()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The shared account cannot act as an individual employee or approver.",
        )

    if principal.claims.get("account_type") == "portal":
        # Portal users authenticate by email (portal_users table), not by
        # Entra object_id. In local loopback dev they act via the Requests UI;
        # identity mapping for requester checks resolves from the payload. If no
        # matching User exists, fall through to _identity_user_ids with an empty
        # user_set rather than opening a 403 "not mapped".
        if (
            http_request is not None
            and _is_local_test_session(principal, http_request)
        ):
            return set()
        email = (principal.claims.get("preferred_username") or "").strip().lower()
        if email:
            users = (
                db.query(User)
                .filter(User.email.ilike(email))
                .order_by(User.id)
                .all()
            )
            if users:
                return {
                    user.id for user in users
                    if (user.status or "active").strip().lower() not in {"inactive", "disabled"}
                }
        # No matching User: last resort — retry by Entra object_id below, then
        # an actionable 403 naming the unmapped account.
        users = (
            db.query(User)
            .filter(User.external_user_id == principal.object_id)
            .order_by(User.id)
            .all()
        )
    active_users = [
        user
        for user in users
        if (user.status or "active").strip().lower() not in {"inactive", "disabled"}
    ]
    if not active_users:
        account = (
            principal.claims.get("preferred_username")
            or principal.claims.get("upn")
            or ""
        ).strip()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"The logged-in account ({account}) is not mapped to an individual "
                "employee record. Contact an administrator to map the account, or "
                "log in with a mapped account."
            ),
        )
    return {user.id for user in active_users}



def _accessible_request(
    db: Session,
    request_id: str,
    principal: AuthenticatedPrincipal,
    http_request: Request,
) -> tuple[LicenseRequest, set[int]]:
    local_test = _is_local_test_session(principal, http_request)
    # Portal admins carry License.Admin but may have no individual User row
    # (e.g. clouddestinations@gmail.com). Skip identity resolution for them
    # (and for local test sessions) so _identity_user_ids cannot raise a 403
    # before the ADMIN_ROLE short-circuit below grants access.
    if local_test or ADMIN_ROLE in principal.roles:
        user_ids = set()
    else:
        user_ids = _identity_user_ids(db, principal, http_request)
    request = (
        db.query(LicenseRequest)
        .options(
            joinedload(LicenseRequest.employee),
            joinedload(LicenseRequest.department),
            joinedload(LicenseRequest.license).joinedload(License.application),
            joinedload(LicenseRequest.approver).joinedload(DepartmentApprover.employee),
            joinedload(LicenseRequest.approvals).joinedload(LicenseApproval.approver),
        )
        .filter(LicenseRequest.request_id == request_id)
        .first()
    )
    if request is None:
        raise HTTPException(status_code=404, detail="License request not found.")
    if local_test and principal.claims.get("account_type") == "shared":
        return request, set()
    if ADMIN_ROLE in principal.roles:
        return request, user_ids
    email = _portal_email(principal)
    if email and any(
        (a.approver_email or "").strip().lower() == email and a.status == "Pending"
        for a in request.approvals
    ):
        return request, user_ids
    if (
        request.user_id not in user_ids
        and (
            request.approver is None
            or request.approver.employee_id not in user_ids
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this license request.",
        )
    return request, user_ids


def _can_decide(
    request: LicenseRequest,
    principal: AuthenticatedPrincipal,
    user_ids: set[int],
    local_test: bool = False,
) -> bool:
    if request.status != "Pending Approval":
        return False
    if local_test and principal.claims.get("account_type") == "shared":
        # Legacy shared admin acts from the Requests UI.
        return True
    stage = _current_stage(request)
    if stage and _can_decide_stage(principal, stage):
        return True
    return (
        APPROVER_ROLE in principal.roles
        and request.approver is not None
        and request.approver.employee_id in user_ids
    )


def _serialize_request(
    request: LicenseRequest,
    principal: AuthenticatedPrincipal,
    user_ids: set[int],
    local_test: bool,
) -> dict:
    employee = request.employee
    return {
        "id": request.id,
        "request_id": request.request_id,
        "user_id": request.user_id,
        "employee_name": (
            employee.name or employee.email or "Employee"
            if employee
            else "Unknown employee"
        ),
        "employee_email": employee.email if employee else None,
        "department": request.department.name,
        "application": request.license.application.name,
        "license_id": request.license_id,
        "license_type": request.license.license_type,
        "license_name": request.license.product,
        "business_justification": request.business_justification,
        "urgency": request.urgency,
        "requested_at": request.requested_at or request.created_at,
        "status": request.status or "Unknown",
        "provisioning_status": request.provisioning_status,
        "approver_id": request.approver_id,
        "approver_name": (
            (request.approver.approver_name or request.approver.approver_email)
            if request.approver
            else None
        ),
        "requester_identity": request.requester_identity,
        "test_mode": local_test,
        "can_decide": _can_decide(request, principal, user_ids, local_test),
    }


def _serialize_approval(approval: LicenseApproval) -> dict:
    label = STAGE_LABELS.get(getattr(approval, "stage", None) or "", None)
    if label is None:
        try:
            label = approval.stage
        except Exception:
            label = "Tower Head Approval"
    approver = getattr(approval, "approver", None)
    approver_email = getattr(approval, "approver_email", None) or (
        approver.approver_email if approver else None
    )
    return {
        "id": approval.id,
        "approver_name": (
            (approver.approver_name or approver_email or "Approver")
            if approver else (approver_email or "Approver")
        ),
        "decision": approval.status,
        "stage": label,
        "decision_at": approval.decision_at,
        "comments": approval.comments,
        "created_at": approval.created_at,
    }


def _create_request(
    payload: LicenseRequestCreate,
    db: Session,
    principal: AuthenticatedPrincipal,
    http_request: Request,
) -> LicenseRequestDetail:
    local_test = _is_local_test_session(principal, http_request)
    if (
        not local_test
        and REQUESTER_ROLE not in principal.roles
        and ADMIN_ROLE not in principal.roles
    ):
        require_role(principal, REQUESTER_ROLE)
    # Portal admins carry License.Admin but may have no individual User row
    # (e.g. clouddestinations@gmail.com). Skip identity resolution for them
    # (and for local test sessions) so _identity_user_ids cannot raise a 403,
    # and let them submit on behalf of any employee - matching the
    # all-employees visibility granted by get_license_request_options.
    if local_test or ADMIN_ROLE in principal.roles:
        user_ids = set()
    else:
        user_ids = _identity_user_ids(db, principal, http_request)
    if (
        not local_test
        and ADMIN_ROLE not in principal.roles
        and payload.user_id not in user_ids
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A request can only be submitted for the authenticated employee.",
        )

    existing = (
        db.query(LicenseRequest)
        .filter(
            LicenseRequest.user_id == payload.user_id,
            LicenseRequest.idempotency_key == payload.idempotency_key,
        )
        .first()
    )
    if existing is not None:
        existing, user_ids = _accessible_request(
            db, existing.request_id, principal, http_request
        )
        return LicenseRequestDetail(
            **_serialize_request(existing, principal, user_ids, local_test),
            approvals=[_serialize_approval(item) for item in existing.approvals],
        )

    employee = db.query(User).filter(User.id == payload.user_id).first()
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The employee does not exist in the database.",
        )

    department = (
        db.query(Department)
        .filter(Department.name.ilike(payload.department.strip()), Department.active.is_(True))
        .first()
    )
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The selected department does not exist.",
        )
    if employee.department_id is None:
        # Sync data often has no department; adopt the UI-selected one in
        # local test mode so the request flow works end-to-end.
        if local_test:
            employee.department_id = department.id
            db.flush()
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The employee does not have a department mapped in the database.",
            )
    if department.id != employee.department_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The selected department does not match the employee's database department.",
        )

    application = (
        db.query(Application)
        .filter(Application.name.ilike(payload.application_name.strip()))
        .first()
    )
    if application is None:
        raise HTTPException(status_code=422, detail="The selected application does not exist.")

    license_record = (
        db.query(License)
        .filter(
            License.id == payload.license_id,
            License.application_id == application.id,
        )
        .first()
    )
    if license_record is None:
        raise HTTPException(
            status_code=422,
            detail="The selected license does not belong to the selected application.",
        )

    mapping = None
    mapping = (
        db.query(DepartmentApprover)
        .options(joinedload(DepartmentApprover.employee))
        .filter(
            DepartmentApprover.department_id == department.id,
            DepartmentApprover.active.is_(True),
        )
        .order_by(DepartmentApprover.id)
        .all()
    )
    tower_mapping = next(
        (m for m in mapping if (m.approver_email or "").strip().lower() == TOWER_HEAD_EMAIL),
        None,
    )
    chosen = tower_mapping or (mapping[0] if mapping else None)
    if chosen is None:
        # Default tower head: akshayap@clouddestinations.com for every dept.
        tower_user = db.query(User).filter(User.email.ilike(TOWER_HEAD_EMAIL)).order_by(User.id).first()
        if tower_user is None:
            raise HTTPException(status_code=409, detail="Default tower head user is missing from the database.")
        chosen = DepartmentApprover(
            department_id=department.id,
            employee_id=tower_user.id,
            approver_name=tower_user.name or tower_user.email,
            approver_email=tower_user.email,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(chosen)
        db.flush()
    mapping = chosen

    now = datetime.utcnow()
    request = LicenseRequest(
        request_id=f"PENDING-{uuid4().hex}",
        idempotency_key=payload.idempotency_key,
        user_id=employee.id,
        department_id=department.id,
        license_id=license_record.id,
        approver_id=mapping.id if mapping else None,
        business_justification=payload.business_justification.strip(),
        urgency=payload.urgency.strip(),
        status="Pending Approval",
        requested_at=now,
        provisioning_status="Not Started" if local_test else None,
        requester_identity=(
            "shared-development-account" if local_test else None
        ),
        created_at=now,
        updated_at=now,
    )
    db.add(request)
    try:
        db.flush()
        request.request_id = f"LIC-{request.created_at.year}-{request.id:06d}"
        # Three-stage chain: tower head -> assignee (all apps: swethar) -> final (portal admin).
        for stage_name, stage_email, stage_mapping_id in [
            ("tower_head", (mapping.approver_email or TOWER_HEAD_EMAIL), mapping.id),
            ("assignee", ASSIGNEE_EMAIL, None),
            ("final", "", None),
        ]:
            db.add(LicenseApproval(
                request=request,
                approver_id=stage_mapping_id,
                stage=stage_name,
                approver_email=stage_email.strip().lower() if stage_email else None,
                status="Pending",
                created_at=now,
                updated_at=now,
            ))
        db.commit()
        db.refresh(request)
    except IntegrityError as exc:
        db.rollback()
        existing = (
            db.query(LicenseRequest)
            .filter(
                LicenseRequest.user_id == payload.user_id,
                LicenseRequest.idempotency_key == payload.idempotency_key,
            )
            .first()
        )
        if existing is not None:
            existing, user_ids = _accessible_request(
                db, existing.request_id, principal, http_request
            )
            return LicenseRequestDetail(
                **_serialize_request(existing, principal, user_ids, local_test),
                approvals=[_serialize_approval(item) for item in existing.approvals],
            )
        raise HTTPException(
            status_code=409,
            detail="The request could not be saved because of a database uniqueness conflict.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="The license request could not be saved.",
        ) from exc

    db.refresh(request)
    try:
        from services.mail_service import (
            _portal_link,
            build_approval_request_email,
            issue_approval_token,
            send_mail,
        )
        approver_email = mapping.approver_email if mapping else None
        license_label = license_record.product or application.name
        token = issue_approval_token(request.request_id, approver_email or "")
        base = _portal_link()
        api = "http://localhost:8000"
        approve_url = f"{api}/approvals/approve?token={token}"
        decline_url = f"{api}/approvals/decline?token={token}"
        secure_link = f"{base}/approvals/{token}"
        submitted = (request.requested_at or request.created_at)
        subject, html, text = build_approval_request_email(
            approver_name=mapping.approver_name if mapping else "Approver",
            request_id=request.request_id,
            employee_name=employee.name or employee.email or "Employee",
            employee_email=employee.email,
            department=department.name,
            application=application.name,
            license_label=license_label,
            license_type=license_record.license_type or "",
            justification=request.business_justification,
            urgency=request.urgency,
            raised_by=employee.name or employee.email or "Employee",
            raised_by_email=employee.email or "",
            submitted_at=submitted.strftime("%d %b %Y %H:%M UTC") if submitted else "",
            approve_url=approve_url,
            decline_url=decline_url,
            secure_link=secure_link,
        )
        # Approval mail goes to the mapped approver; fall back to requester
        # email so local test flow is still observable in logs/mail.log.
        send_mail(approver_email or employee.email or "", subject, html, text)
    except Exception as exc:  # noqa: BLE001 - mail must never break request save
        print(f"[mail/approval-request-failed] {exc}")
    return LicenseRequestDetail(
        **_serialize_request(request, principal, user_ids, local_test),
        approvals=[_serialize_approval(item) for item in request.approvals],
    )


@router.post("", response_model=LicenseRequestDetail, status_code=status.HTTP_201_CREATED)
def create_license_request(
    payload: LicenseRequestCreate,
    http_request: Request,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> LicenseRequestDetail:
    return _create_request(payload, db, principal, http_request)


@router.get("/options")
def get_license_request_options(
    http_request: Request,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> dict:
    local_test = _is_local_test_session(principal, http_request)
    if (
        not local_test
        and REQUESTER_ROLE not in principal.roles
        and ADMIN_ROLE not in principal.roles
    ):
        require_role(principal, REQUESTER_ROLE)
    if local_test:
        employees = (
            db.query(User)
            .join(Department, User.department_id == Department.id)
            .filter(
                User.department_id.isnot(None),
                Department.active.is_(True),
                (User.status.is_(None))
                | (
                    ~User.status.ilike("inactive")
                    & ~User.status.ilike("disabled")
                ),
            )
            .order_by(User.name, User.id)
            .all()
        )
    elif ADMIN_ROLE in principal.roles:
        # Portal admins may have no individual User row (e.g.
        # clouddestinations@gmail.com) and raise requests on behalf of any
        # employee, so list every department-mapped employee instead of
        # resolving a single identity via _identity_user_ids (which raises 403
        # for an unmapped admin email and left the request dropdown empty).
        employees = (
            db.query(User)
            .join(Department, User.department_id == Department.id)
            .filter(
                User.department_id.isnot(None),
                Department.active.is_(True),
                (User.status.is_(None))
                | (
                    ~User.status.ilike("inactive")
                    & ~User.status.ilike("disabled")
                ),
            )
            .order_by(User.name, User.id)
            .all()
        )
    else:
        user_ids = _identity_user_ids(db, principal, http_request)
        employees = (
            db.query(User)
            .filter(User.id.in_(user_ids), User.department_id.isnot(None))
            .order_by(User.id)
            .all()
        )
    if not employees:
        raise HTTPException(
            status_code=409,
            detail="No active employees with department mappings are available.",
        )

    licenses = (
        db.query(License, Application.name)
        .join(Application, License.application_id == Application.id)
        .order_by(Application.name, License.product)
        .all()
    )
    return {
        "users": [
            {
                "user_id": employee.id,
                "name": employee.name or employee.email or "Employee",
                "email": employee.email,
                "department": employee.department.name,
                "role": employee.role or "Employee",
            }
            for employee in employees
        ],
        "licenses": [
            {
                "license_id": license.id,
                "db_license_id": license.id,
                "license_name": license.product,
                "product": license.product,
                "license_type": license.license_type,
                "application_name": application_name,
                "available_quantity": license.available_qty,
            }
            for license, application_name in licenses
        ],
        "test_mode": local_test,
    }


@legacy_router.post(
    "/licenses/request",
    response_model=LicenseRequestDetail,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_license_request_legacy(
    payload: LicenseRequestCreate,
    http_request: Request,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> LicenseRequestDetail:
    return _create_request(payload, db, principal, http_request)


@router.get("", response_model=list[LicenseRequestRead])
def list_license_requests(
    http_request: Request,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> list[LicenseRequestRead]:
    local_test = _is_local_test_session(principal, http_request)
    # Admins see every request (see the ADMIN_ROLE branch below), and a portal
    # admin may have no individual User row, so skip identity resolution for
    # them (and for local test sessions) to avoid a premature 403.
    if local_test or ADMIN_ROLE in principal.roles:
        user_ids = set()
    else:
        user_ids = _identity_user_ids(db, principal, http_request)
    query = db.query(LicenseRequest)
    if local_test:
        pass
    elif ADMIN_ROLE not in principal.roles:
        if APPROVER_ROLE in principal.roles:
            query = query.filter(
                (LicenseRequest.user_id.in_(user_ids))
                | LicenseRequest.approver.has(
                    DepartmentApprover.employee_id.in_(user_ids)
                )
            )
        elif REQUESTER_ROLE in principal.roles:
            query = query.filter(LicenseRequest.user_id.in_(user_ids))
        else:
            raise HTTPException(status_code=403, detail="No license request viewing role is assigned.")

    requests = (
        query.options(
            joinedload(LicenseRequest.employee),
            joinedload(LicenseRequest.department),
            joinedload(LicenseRequest.license).joinedload(License.application),
            joinedload(LicenseRequest.approver).joinedload(DepartmentApprover.employee),
        )
        .order_by(LicenseRequest.created_at.desc(), LicenseRequest.id.desc())
        .all()
    )
    return [
        LicenseRequestRead(
            **_serialize_request(request, principal, user_ids, local_test)
        )
        for request in requests
    ]


@router.get("/{request_id}/approvals", response_model=list[ApprovalRead])
def get_approval_history(
    request_id: str,
    http_request: Request,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> list[ApprovalRead]:
    request, _ = _accessible_request(db, request_id, principal, http_request)
    return [ApprovalRead(**_serialize_approval(item)) for item in request.approvals]


@router.get("/{request_id}", response_model=LicenseRequestDetail)
def get_license_request(
    request_id: str,
    http_request: Request,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> LicenseRequestDetail:
    request, user_ids = _accessible_request(
        db, request_id, principal, http_request
    )
    return LicenseRequestDetail(
        **_serialize_request(
            request,
            principal,
            user_ids,
            _is_local_test_session(principal, http_request),
        ),
        approvals=[_serialize_approval(item) for item in request.approvals],
    )


@router.post("/{request_id}/decision", response_model=LicenseRequestDetail)
def decide_license_request(
    request_id: str,
    payload: ApprovalDecision,
    http_request: Request,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> LicenseRequestDetail:
    local_test = _is_local_test_session(principal, http_request)
    shared_legacy = local_test and principal.claims.get("account_type") == "shared"
    request, user_ids = _accessible_request(
        db, request_id, principal, http_request
    )
    request = (
        db.query(LicenseRequest)
        .filter(LicenseRequest.id == request.id)
        .with_for_update()
        .populate_existing()
        .first()
    )
    if request is None:
        raise HTTPException(status_code=404, detail="License request not found.")
    # Reload approvals for stage computation
    db.refresh(request, attribute_names=["approvals"])
    stage = _current_stage(request)
    if request.status != "Pending Approval" or stage is None:
        raise HTTPException(status_code=409, detail="This request has already been decided.")
    if not shared_legacy and not _can_decide_stage(principal, stage):
        if stage == "final":
            require_role(principal, ADMIN_ROLE)
        else:
            raise HTTPException(
                status_code=403,
                detail=f"This stage must be approved by {_stage_approver_email(db, request, stage) or 'the admin'}.",
            )

    approval = (
        db.query(LicenseApproval)
        .filter(
            LicenseApproval.request_id == request.id,
            LicenseApproval.stage == stage,
            LicenseApproval.status == "Pending",
        )
        .with_for_update()
        .first()
    )
    if approval is None:
        raise HTTPException(status_code=409, detail="No pending approval stage exists.")

    now = datetime.utcnow()
    if payload.decision == "Rejected":
        approval.status = "Rejected"
        approval.comments = payload.comments.strip() if payload.comments else None
        approval.decision_at = now
        request.status = "Rejected"
        request.updated_at = now
    else:
        approval.status = "Approved"
        approval.comments = payload.comments.strip() if payload.comments else None
        approval.decision_at = now
        nxt = STAGE_ORDER[STAGE_ORDER.index(stage) + 1] if stage != STAGE_ORDER[-1] else None
        if nxt is None:
            request.status = "Approved"
        else:
            # stays Pending Approval; next stage becomes actionable
            request.status = "Pending Approval"
        request.updated_at = now
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="The approval decision could not be saved.") from exc

    request, user_ids = _accessible_request(
        db, request_id, principal, http_request
    )
    try:
        from services.mail_service import (
            _portal_link,
            build_approval_request_email,
            build_decision_email,
            issue_approval_token,
            send_mail,
        )
        _decided = _serialize_request(
            request, principal, user_ids,
            _is_local_test_session(principal, http_request),
        )
        lic = request.license
        app = lic.application if lic else None
        emp = request.employee
        if payload.decision == "Rejected" or request.status == "Approved":
            _subj, _html, _text = build_decision_email(
                employee_name=_decided["employee_name"],
                request_id=request.request_id,
                license_label=_decided.get("license_name") or _decided.get("license_type") or "license",
                decision=request.status,
                comments=approval.comments,
                approver_name=_decided.get("approver_name"),
            )
            send_mail(_decided.get("employee_email") or "", _subj, _html, _text)
        else:
            # Advance: notify next stage approver (assignee mail, or admin note).
            nxt = _current_stage(request)
            nxt_email = _stage_approver_email(db, request, nxt) if nxt else ""
            if nxt == "assignee" and nxt_email:
                token = issue_approval_token(request.request_id, nxt_email)
                base = _portal_link()
                api = "http://localhost:8000"
                submitted = request.requested_at or request.created_at
                _s2, _h2, _t2 = build_approval_request_email(
                    approver_name="Assignee",
                    request_id=request.request_id,
                    employee_name=(emp.name if emp else None) or "Employee",
                    employee_email=(emp.email if emp else None) or "",
                    department=request.department.name if request.department else "",
                    application=app.name if app else "",
                    license_label=(lic.product if lic else "") or "",
                    license_type=(lic.license_type if lic else "") or "",
                    justification=request.business_justification,
                    urgency=request.urgency,
                    raised_by=(emp.name if emp else None) or "",
                    raised_by_email=(emp.email if emp else None) or "",
                    submitted_at=submitted.strftime("%d %b %Y %H:%M UTC") if submitted else "",
                    approve_url=f"{api}/approvals/approve?token={token}",
                    decline_url=f"{api}/approvals/decline?token={token}",
                    secure_link=f"{base}/approvals/{token}",
                )
                send_mail(nxt_email, _s2, _h2, _t2)
    except Exception as exc:  # noqa: BLE001 - mail must never break decision save
        print(f"[mail/decision-failed] {exc}")
    return LicenseRequestDetail(
        **_serialize_request(
            request,
            principal,
            user_ids,
            _is_local_test_session(principal, http_request),
        ),
        approvals=[_serialize_approval(item) for item in request.approvals],
    )


@router.put("/department-approvers", status_code=status.HTTP_200_OK)
def assign_department_approver(
    payload: DepartmentApproverAssignment,
    http_request: Request,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> dict[str, str | int]:
    if _is_local_test_session(principal, http_request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The shared test account cannot assign real department approvers.",
        )
    require_role(principal, ADMIN_ROLE)
    _identity_user_ids(db, principal, http_request)
    department = db.query(Department).filter(Department.id == payload.department_id).first()
    approver = db.query(User).filter(User.id == payload.approver_user_id).first()
    if department is None or not department.active:
        raise HTTPException(status_code=404, detail="Active department not found.")
    if approver is None or not approver.external_user_id:
        raise HTTPException(
            status_code=422,
            detail="Approver must map to an individually authenticated portal user.",
        )
    mapping = (
        db.query(DepartmentApprover)
        .filter(
            DepartmentApprover.department_id == department.id,
            DepartmentApprover.employee_id == approver.id,
        )
        .first()
    )
    if mapping is None:
        mapping = DepartmentApprover(
            department_id=department.id,
            employee_id=approver.id,
            approver_name=approver.name or approver.email or "Approver",
            approver_email=approver.email,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(mapping)
    for other_mapping in (
        db.query(DepartmentApprover)
        .filter(
            DepartmentApprover.department_id == department.id,
            DepartmentApprover.active.is_(True),
        )
        .all()
    ):
        other_mapping.active = other_mapping.employee_id == approver.id
        other_mapping.updated_at = datetime.utcnow()
    mapping.approver_name = approver.name or approver.email or "Approver"
    mapping.approver_email = approver.email
    mapping.active = True
    mapping.updated_at = datetime.utcnow()
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="The approver mapping could not be saved.") from exc
    return {
        "department_id": department.id,
        "approver_user_id": approver.id,
        "status": "active",
    }
