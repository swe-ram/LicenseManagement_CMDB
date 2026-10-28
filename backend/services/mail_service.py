"""Approval email transport for the license request flow.

Primary transport is Microsoft Graph sendMail (app-only, same MS_* creds as
inventory sync) because SMTP AUTH is disabled for this tenant
(Microsoft error 5.7.139). SMTP is kept as fallback, then file log.

MAIL_TRANSPORT=auto -> Graph first, SMTP fallback, else log file.
MAIL_TRANSPORT=graph|smtp|log forces a single transport.
"""
import base64
import hashlib
import hmac
import json
import os
import smtplib
import time
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

LOG_FILE = Path(__file__).resolve().parents[1] / "logs" / "mail.log"

APPROVAL_TOKEN_TTL_HOURS = 72


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or default).strip()


def approval_token_secret() -> str:
    secret = _env("AUTH_TOKEN_SECRET") or _env("APPROVAL_TOKEN_SECRET")
    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError("AUTH_TOKEN_SECRET (>=32 chars) is required for approval links.")
    return secret


def issue_approval_token(request_id: str, approver_email: str = "") -> str:
    """Issue a short-lived HMAC-signed token for no-login approve/decline links."""
    payload = {
        "rid": request_id,
        "em": (approver_email or "").strip().lower(),
        "exp": int(time.time()) + APPROVAL_TOKEN_TTL_HOURS * 3600,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    sig = hmac.new(approval_token_secret().encode(), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw + b"." + sig).decode().rstrip("=")


def verify_approval_token(token: str) -> dict:
    """Verify token -> {'request_id':..., 'approver_email':...} or raise."""
    padded = token + "=" * (-len(token) % 4)
    try:
        blob = base64.urlsafe_b64decode(padded.encode())
        raw, sig = blob.rsplit(b".", 1)
    except Exception as exc:
        raise ValueError("Invalid approval link.") from exc
    expect = hmac.new(approval_token_secret().encode(), raw, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expect):
        raise ValueError("Invalid approval link.")
    try:
        payload = json.loads(raw.decode())
    except Exception as exc:
        raise ValueError("Invalid approval link.") from exc
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("This approval link has expired.")
    if not payload.get("rid"):
        raise ValueError("Invalid approval link.")
    return {"request_id": payload["rid"], "approver_email": payload.get("em", "")}



def _graph_token() -> str:
    tenant = _env("MS_TENANT_ID")
    client = _env("MS_CLIENT_ID")
    secret = _env("MS_CLIENT_SECRET")
    if not (tenant and client and secret):
        raise RuntimeError("MS Graph mail credentials are not configured.")
    resp = requests.post(
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        data={
            "client_id": client,
            "client_secret": secret,
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Graph token failed ({resp.status_code}): {resp.text[:500]}")
    token = resp.json().get("access_token", "")
    if not token:
        raise RuntimeError("Graph token response had no access_token.")
    return token


def _send_via_graph(to: str, subject: str, html: str, text: str) -> dict:
    sender = _env("MAIL_FROM") or _env("SMTP_FROM") or _env("SMTP_USER")
    if not sender:
        raise RuntimeError("MAIL_FROM / SMTP_FROM is not configured.")
    token = _graph_token()
    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html},
            "toRecipients": [{"emailAddress": {"address": to}}],
        },
        "saveToSentItems": "true",
    }
    resp = requests.post(
        f"https://graph.microsoft.com/v1.0/users/{sender}/sendMail",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if resp.status_code not in (200, 201, 202):
        raise RuntimeError(f"Graph sendMail failed ({resp.status_code}): {resp.text[:1000]}")
    return {"transport": "graph", "status": resp.status_code}

def _send_via_smtp(to: str, subject: str, html: str, text: str) -> dict:
    host = _env("SMTP_HOST", "smtp.office365.com")
    port = int(_env("SMTP_PORT", "587") or 587)
    user = _env("SMTP_USER")
    password = (_env("SMTP_PASSWORD", "") or "").strip().strip('"').strip("'")
    sender = _env("SMTP_FROM") or _env("MAIL_FROM") or user
    use_tls = (_env("SMTP_TLS", "true") or "true").lower() in {"true", "1", "yes"}
    if not (user and password and sender):
        raise RuntimeError("SMTP_USER / SMTP_PASSWORD / SMTP_FROM not configured.")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.attach(MIMEText(text or html, "plain"))
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP(host, port, timeout=30) as server:
        if use_tls:
            server.starttls()
        server.login(user, password)
        server.sendmail(sender, [to], msg.as_string())
    return {"transport": "smtp", "status": "sent"}


def _log_mail(to: str, subject: str, text: str) -> dict:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(f"\n{'='*70}\n[{stamp}] TO: {to}\nSUBJECT: {subject}\n{text}\n")
    print(f"[mail/log] to={to} subject={subject} (logs/mail.log)")
    return {"transport": "log", "status": "logged"}


def send_mail(to: str, subject: str, html_body: str, text_body: str = "") -> dict:
    """Send one email via configured transport with graceful fallback."""
    if not to or "@" not in to:
        print(f"[mail/skip] no valid recipient for subject={subject!r}")
        return {"transport": "skipped", "status": "no-recipient"}
    mode = (_env("MAIL_TRANSPORT", "auto") or "auto").lower()
    if mode in {"graph", "auto"}:
        try:
            return _send_via_graph(to, subject, html_body, text_body or html_body)
        except Exception as exc:
            print(f"[mail/graph-failed] {exc}")
            if mode == "graph":
                return _log_mail(to, subject, text_body or html_body)
    if mode in {"smtp", "auto"}:
        try:
            return _send_via_smtp(to, subject, html_body, text_body or html_body)
        except Exception as exc:
            print(f"[mail/smtp-failed] {exc}")
            if mode == "smtp":
                return _log_mail(to, subject, text_body or html_body)
    return _log_mail(to, subject, text_body or html_body)


def _portal_link() -> str:
    base = _env("PORTAL_BASE_URL", "http://localhost:3000") or "http://localhost:3000"
    return base.rstrip("/")


def build_approval_request_email(
    *, approver_name: str, request_id: str, employee_name: str,
    employee_email, department: str, application: str,
    license_label: str, license_type: str = "", justification: str,
    urgency: str, raised_by: str = "", raised_by_email: str = "",
    submitted_at: str = "", approve_url: str = "", decline_url: str = "",
    secure_link: str = "",
):
    urgency_label = {"Standard": "Normal"}.get(urgency or "", urgency or "Normal")
    subject = f"Approval needed: {request_id} - {employee_name} requests {license_label}"
    rows = [
        ("Request ID", request_id),
        ("Application", application),
        ("License / Product", license_label),
        ("License Type", license_type or "Business"),
        ("Request Type", "New License"),
        ("Quantity", "1"),
        ("Priority", urgency_label),
        ("Requested For", f"{employee_name} ({employee_email})" if employee_email else employee_name),
        ("Raised By", f"{raised_by} ({raised_by_email})" if raised_by_email else (raised_by or employee_name)),
        ("Justification", justification),
        ("Submitted At", submitted_at),
    ]
    row_html = "".join(
        f"<tr><td style='padding:8px 12px;color:#64748b;font-size:13px;width:38%;'>{k}</td>"
        f"<td style='padding:8px 12px;color:#0f172a;font-size:13px;font-weight:500;'>{v or '-'}</td></tr>"
        for k, v in rows
    )
    row_text = "\n".join(f"{k}: {v}" for k, v in rows)
    text = (
        f"You are approving as: Tower Head\n\n{row_text}\n\n"
        f"Approve:\n{approve_url}\n\nDecline:\n{decline_url}\n\n"
        f"Or open this secure link (no portal login required):\n{secure_link}\n"
    )
    html = (
        "<div style='font-family:Segoe UI,Arial,sans-serif;color:#0f172a;'>"
        "<p style='color:#93c5fd;font-size:13px;'>You are approving as: Tower Head</p>"
        f"<table style='width:100%;border:1px solid #e2e8f0;border-collapse:collapse;'>{row_html}</table>"
        "<div style='text-align:center;margin:22px 0 10px;'>"
        f"<a href='{approve_url}' style='display:inline-block;background:#16a34a;color:#fff;"
        "font-weight:700;font-size:15px;padding:12px 34px;border-radius:8px;text-decoration:none;"
        "margin-right:14px;'>&#10003; Approve</a>"
        f"<a href='{decline_url}' style='display:inline-block;background:#dc2626;color:#fff;"
        "font-weight:700;font-size:15px;padding:12px 34px;border-radius:8px;text-decoration:none;'>"
        "&#10007; Decline</a></div>"
        "<p style='text-align:center;color:#64748b;font-size:12px;'>"
        "Or open this secure link (no portal login required):<br>"
        f"<a href='{secure_link}' style='color:#1d4ed8;'>{secure_link}</a></p></div>"
    )
    return subject, html, text


def build_decision_email(
    *, employee_name: str, request_id: str, license_label: str,
    decision: str, comments, approver_name,
):
    link = f"{_portal_link()}/license-requests"
    subject = f"License request {request_id} {decision}"
    text = (
        f"Hi {employee_name},\n\n"
        f"Your request {request_id} for '{license_label}' was {decision}"
        f"{f' by {approver_name}' if approver_name else ''}.\n"
        f"{f'Comments: {comments}' if comments else ''}\n\n"
        f"Track it here:\n{link}\n"
    )
    html = (
        f"<p>Hi {employee_name},</p>"
        f"<p>Your request <b>{request_id}</b> for <b>{license_label}</b> "
        f"was <b>{decision}</b>{f' by {approver_name}' if approver_name else ''}.</p>"
        f"{f'<p>Comments: {comments}</p>' if comments else ''}"
        f"<p><a href='{link}'>Track it in the portal</a></p>"
    )
    return subject, html, text
