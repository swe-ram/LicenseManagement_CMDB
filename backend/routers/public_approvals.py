"""Public no-login approval endpoints for one-click email buttons.

Links are HMAC-signed (services.mail_service.issue/verify_approval_token),
expire after 72h, and record the decision through the same code path as the
portal drawer so the Requests UI reflects it instantly.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import LicenseApproval, LicenseRequest
from services.mail_service import verify_approval_token

router = APIRouter(prefix="/api/v1/approvals", tags=["Public Approvals"])
legacy_router = APIRouter(prefix="/approvals", tags=["Public Approvals"])


class PublicDecision(BaseModel):
    token: str = Field(min_length=10)
    comments: str | None = Field(default=None, max_length=5000)


def _apply_token_decision(db: Session, token: str, decision: str, comments: str | None) -> dict:
    try:
        claims = verify_approval_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    request = (
        db.query(LicenseRequest)
        .filter(LicenseRequest.request_id == claims["request_id"])
        .first()
    )
    if request is None:
        raise HTTPException(status_code=404, detail="License request not found.")
    pending = [a for a in request.approvals if a.status == "Pending"]
    if request.status != "Pending Approval" or not pending:
        return {
            "request_id": request.request_id,
            "status": request.status,
            "message": f"This request has already been {request.status.lower()}.",
        }
    order = {"tower_head": 0, "assignee": 1, "final": 2}
    pending.sort(key=lambda a: (order.get(a.stage, 99), a.id))
    approval = pending[0]
    token_email = (claims.get("approver_email") or "").strip().lower()
    if token_email and (approval.approver_email or "").strip().lower() and token_email != (approval.approver_email or "").strip().lower():
        raise HTTPException(status_code=403, detail="This link belongs to a different approver.")
    now = datetime.utcnow()
    if decision == "Rejected":
        approval.status = "Rejected"
        approval.comments = (comments or "").strip() or None
        approval.decision_at = now
        request.status = "Rejected"
        request.updated_at = now
        final_status = "Rejected"
    else:
        approval.status = "Approved"
        approval.comments = (comments or "").strip() or None
        approval.decision_at = now
        if len(pending) == 1:
            request.status = "Approved"
            final_status = "Approved"
        else:
            request.status = "Pending Approval"
            final_status = "Pending Approval"
        request.updated_at = now
    db.commit()
    try:
        from services.mail_service import (
            _portal_link,
            build_approval_request_email,
            build_decision_email,
            issue_approval_token,
            send_mail,
        )
        emp = request.employee
        lic = request.license
        app = lic.application if lic else None
        if final_status in ("Approved", "Rejected"):
            subject, html, text = build_decision_email(
                employee_name=(emp.name if emp else None) or "Employee",
                request_id=request.request_id,
                license_label=(lic.product if lic else "license"),
                decision=final_status,
                comments=approval.comments,
                approver_name=(request.approver.approver_name if request.approver else None),
            )
            send_mail((emp.email if emp else None) or "", subject, html, text)
        else:
            # Advance: mail the next stage approver (assignee). Final stage
            # has no email -> the admin acts in the portal.
            nxt = [a for a in request.approvals if a.status == "Pending"]
            nxt.sort(key=lambda a: ({"tower_head": 0, "assignee": 1, "final": 2}.get(a.stage, 99), a.id))
            if nxt and (nxt[0].approver_email or "").strip():
                tok = issue_approval_token(request.request_id, nxt[0].approver_email or "")
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
                    approve_url=f"{api}/approvals/approve?token={tok}",
                    decline_url=f"{api}/approvals/decline?token={tok}",
                    secure_link=f"{base}/approvals/{tok}",
                )
                send_mail(nxt[0].approver_email or "", _s2, _h2, _t2)
    except Exception as exc:  # noqa: BLE001 - mail must never break decision
        print(f"[mail/decision-failed] {exc}")
    return {
        "request_id": request.request_id,
        "status": final_status,
        "message": (
            f"Request {request.request_id} has been {final_status.lower()}."
            if final_status != "Pending Approval"
            else f"Stage approved. Request {request.request_id} moved to the next approver."
        ),
    }


def _preview(db: Session, token: str) -> dict:
    try:
        claims = verify_approval_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    request = (
        db.query(LicenseRequest)
        .filter(LicenseRequest.request_id == claims["request_id"])
        .first()
    )
    if request is None:
        raise HTTPException(status_code=404, detail="License request not found.")
    emp = request.employee
    lic = request.license
    app = lic.application if lic else None
    return {
        "request_id": request.request_id,
        "application": app.name if app else "",
        "license_label": lic.product if lic else "",
        "license_type": lic.license_type if lic else "",
        "employee_name": (emp.name if emp else None) or "",
        "employee_email": (emp.email if emp else None) or "",
        "department": request.department.name if request.department else "",
        "justification": request.business_justification,
        "urgency": request.urgency,
        "status": request.status,
        "submitted_at": (request.requested_at or request.created_at).isoformat() if (request.requested_at or request.created_at) else "",
    }


@router.get("/preview")
def preview(token: str = Query(min_length=10), db: Session = Depends(get_db)):
    return _preview(db, token)


@router.get("/approve")
def approve_get(
    token: str = Query(min_length=10),
    comments: str | None = Query(default=None, max_length=5000),
    db: Session = Depends(get_db),
):
    return _apply_token_decision(db, token, "Approved", comments)


@router.get("/decline")
def decline_get(
    token: str = Query(min_length=10),
    comments: str | None = Query(default=None, max_length=5000),
    db: Session = Depends(get_db),
):
    return _apply_token_decision(db, token, "Rejected", comments)


@router.post("/approve")
def approve(payload: PublicDecision, db: Session = Depends(get_db)):
    return _apply_token_decision(db, payload.token, "Approved", payload.comments)


@router.post("/decline")
def decline(payload: PublicDecision, db: Session = Depends(get_db)):
    return _apply_token_decision(db, payload.token, "Rejected", payload.comments)


@legacy_router.get("/preview")
def legacy_preview(token: str = Query(min_length=10), db: Session = Depends(get_db)):
    return _preview(db, token)


@legacy_router.get("/approve")
def legacy_approve_get(
    token: str = Query(min_length=10),
    comments: str | None = Query(default=None, max_length=5000),
    db: Session = Depends(get_db),
):
    return _apply_token_decision(db, token, "Approved", comments)


@legacy_router.get("/decline")
def legacy_decline_get(
    token: str = Query(min_length=10),
    comments: str | None = Query(default=None, max_length=5000),
    db: Session = Depends(get_db),
):
    return _apply_token_decision(db, token, "Rejected", comments)


@legacy_router.post("/approve")
def legacy_approve(payload: PublicDecision, db: Session = Depends(get_db)):
    return _apply_token_decision(db, payload.token, "Approved", payload.comments)


@legacy_router.post("/decline")
def legacy_decline(payload: PublicDecision, db: Session = Depends(get_db)):
    return _apply_token_decision(db, payload.token, "Rejected", payload.comments)
