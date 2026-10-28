import hashlib
import hmac
import ipaddress
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import PortalSession, PortalUser

SESSION_COOKIE_NAME = "licensehub_session"
SESSION_ISSUER = "licensehub"
SESSION_AUDIENCE = "licensehub-frontend"
SHARED_ACCOUNT_SUBJECT = "shared-development-account"
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

ROLE_MAP = {
    "employee": ["License.Requester"],
    "tower_head": ["License.Requester", "License.Approver"],
    "assignee": ["License.Requester", "License.Approver"],
    "admin": ["License.Requester", "License.Approver", "License.Admin"],
}

DEFAULT_TOWER_HEAD_EMAIL = "akshayap@clouddestinations.com"
DEFAULT_ASSIGNEE_EMAIL = "swethar@clouddestinations.com"
DEFAULT_ADMIN_EMAIL = "clouddestinations@gmail.com"
DEFAULT_ADMIN_PASSWORD = "cloud@123"
def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 210_000).hex()
    return f"pbkdf2_sha256$210000${salt}${digest}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt, digest = stored.split("$", 3)
        calc = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), int(iterations)
        ).hex()
        return hmac.compare_digest(calc, digest)
    except Exception:
        return False


def _signing_secret() -> str:
    signing_secret = os.getenv("AUTH_TOKEN_SECRET", "")
    if len(signing_secret.encode("utf-8")) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Shared development authentication is not configured correctly.",
        )
    return signing_secret


def _cookie_flags() -> tuple[bool, int]:
    try:
        lifetime_minutes = int(os.getenv("AUTH_TOKEN_TTL_MINUTES", "480"))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication configuration is invalid.",
        ) from exc
    if not 1 <= lifetime_minutes <= 1440:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Shared development authentication is not configured correctly.",
        )
    secure_cookie = os.getenv("AUTH_COOKIE_SECURE", "false").strip().lower() in {"true", "1", "yes"}
    return secure_cookie, lifetime_minutes


def ensure_default_portal_users(db: Session) -> None:
    """Seed tower head + assignee + admin logins exactly once (idempotent)."""
    defaults = [
        (DEFAULT_TOWER_HEAD_EMAIL, "Tower Head", "tower_head", "Tower@123"),
        (DEFAULT_ASSIGNEE_EMAIL, "Assignee", "assignee", "Assignee@123"),
        (DEFAULT_ADMIN_EMAIL, "Administrator", "admin", os.getenv("AUTH_PASSWORD", "") or DEFAULT_ADMIN_PASSWORD),
    ]
    changed = False
    for email, name, role, password in defaults:
        existing = db.query(PortalUser).filter(PortalUser.email.ilike(email)).first()
        if existing is None:
            db.add(PortalUser(email=email.strip().lower(), name=name, password_hash=_hash_password(password), role=role, active=True))
            changed = True
        elif role == "admin" and os.getenv("AUTH_PASSWORD"):
            # Keep admin password in sync with AUTH_PASSWORD env if provided.
            existing.password_hash = _hash_password(os.getenv("AUTH_PASSWORD", ""))
            existing.active = True
            changed = True
    if changed:
        db.commit()


def _issue_session_token(db: Session, user: PortalUser, lifetime_minutes: int) -> tuple[str, datetime]:
    """Create a fresh server-side session row + signed JWT (new token per login)."""
    signing_secret = _signing_secret()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=lifetime_minutes)
    jti = secrets.token_hex(32)
    db.add(PortalSession(jti=jti, portal_user_id=user.id, expires_at=expires.replace(tzinfo=None)))
    db.commit()
    token = jwt.encode(
        {
            "sub": f"portal-user-{user.id}",
            "account_type": "portal",
            "preferred_username": user.email,
            "name": user.name,
            "portal_role": user.role,
            "roles": ROLE_MAP.get(user.role, ["License.Requester"]),
            "jti": jti,
            "iat": now,
            "exp": expires,
            "iss": SESSION_ISSUER,
            "aud": SESSION_AUDIENCE,
        },
        signing_secret,
        algorithm="HS256",
    )
    return token, expires
# __PART3__ (helpers now live at top of file)

def local_license_request_test_mode_enabled() -> bool:
    environment = os.getenv("APP_ENV", "").strip().lower()
    enabled = os.getenv("LICENSE_REQUEST_TEST_MODE", "").strip().lower()
    return environment in {"development", "local"} and enabled in {"true", "1", "yes"}


def is_loopback_request(request: Request) -> bool:
    host = request.client.host if request.client else ""
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    object_id: str
    roles: frozenset[str]
    claims: dict[str, Any]


class LoginCredentials(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=1024)


def get_current_principal(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> AuthenticatedPrincipal:
    signing_secret = _signing_secret()
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid LicenseHub session is required.",
        )

    try:
        claims = jwt.decode(
            session_token,
            signing_secret,
            algorithms=["HS256"],
            audience=SESSION_AUDIENCE,
            issuer=SESSION_ISSUER,
            options={
                "require": [
                    "exp",
                    "iat",
                    "iss",
                    "aud",
                    "sub",
                    "roles",
                    "account_type",
                    "preferred_username",
                ]
            },
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The LicenseHub session is invalid or expired.",
        ) from exc

    if claims.get("account_type") == "shared" and claims.get("sub") == SHARED_ACCOUNT_SUBJECT:
        # Legacy shared token (pre-DB auth). Accept only if it carries the
        # test-mode flag shape; real users always get portal tokens now.
        token_roles = claims.get("roles", [])
        if not isinstance(token_roles, list):
            raise HTTPException(status_code=401, detail="The LicenseHub session is invalid.")
        return AuthenticatedPrincipal(
            object_id=SHARED_ACCOUNT_SUBJECT,
            roles=frozenset(r for r in token_roles if isinstance(r, str)),
            claims=claims,
        )

    if claims.get("account_type") != "portal" or not claims.get("jti"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The LicenseHub session is invalid.",
        )

    token_roles = claims.get("roles", [])
    if not isinstance(token_roles, list) or any(
        not isinstance(role, str) for role in token_roles
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The LicenseHub session is invalid.",
        )
    # Server-side session check: logout deletes the row -> token dies even
    # before JWT expiry. Each login inserts a new jti row (fresh token).
    session_row = db.query(PortalSession).filter(PortalSession.jti == claims["jti"]).first()
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    if (
        session_row is None
        or session_row.revoked_at is not None
        or session_row.expires_at <= now_naive
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The LicenseHub session is invalid or expired.",
        )
    portal_user = db.query(PortalUser).filter(PortalUser.id == session_row.portal_user_id).first()
    if portal_user is None or not portal_user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The LicenseHub session is invalid.",
        )
    expected_roles = ROLE_MAP.get(portal_user.role, ["License.Requester"])
    return AuthenticatedPrincipal(
        object_id=f"portal-user-{portal_user.id}",
        roles=frozenset(expected_roles),
        claims={**claims, "portal_user_id": portal_user.id, "portal_role": portal_user.role},
    )


def require_role(principal: AuthenticatedPrincipal, role: str) -> None:
    if role not in principal.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"The {role} role is required.",
        )


@router.post("/login")
def login(
    credentials: LoginCredentials,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    secure_cookie, lifetime_minutes = _cookie_flags()
    ensure_default_portal_users(db)
    email = credentials.username.strip().lower()
    user = db.query(PortalUser).filter(PortalUser.email.ilike(email)).first()
    if user is None or not user.active or not _verify_password(credentials.password, user.password_hash):
        # Fall back to legacy shared admin from env for first bootstrap.
        env_user = os.getenv("AUTH_USERNAME", "").strip().lower()
        env_pass = os.getenv("AUTH_PASSWORD", "")
        if (
            user is None
            and email == env_user
            and env_pass
            and hmac.compare_digest(credentials.password, env_pass)
        ):
            admin = db.query(PortalUser).filter(PortalUser.email.ilike(env_user)).first()
            if admin is None:
                admin = PortalUser(email=env_user, name="Administrator", password_hash=_hash_password(env_pass), role="admin", active=True)
                db.add(admin)
                db.commit()
                db.refresh(admin)
            user = admin
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The username or password is incorrect.",
            )

    request_test_mode = (
        local_license_request_test_mode_enabled()
        and is_loopback_request(request)
    )
    token, expires = _issue_session_token(db, user, lifetime_minutes)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=lifetime_minutes * 60,
        expires=expires,
        path="/api/v1",
        secure=secure_cookie,
        httponly=True,
        samesite="strict",
    )
    return {
        "user": {
            "username": user.email,
            "name": user.name or user.email,
            "roles": ROLE_MAP.get(user.role, ["License.Requester"]),
            "portal_role": user.role,
            "is_shared_account": False,
            "license_request_test_mode": request_test_mode,
        }
    }


@router.get("/me")
def get_session(
    request: Request,
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> dict[str, Any]:
    if principal.claims.get("account_type") == "shared":
        return {
            "user": {
                "username": principal.claims["preferred_username"],
                "name": "Shared development account",
                "roles": sorted(list(principal.roles)),
                "is_shared_account": True,
                "license_request_test_mode": (
                    bool(principal.claims.get("license_request_test_mode"))
                    and local_license_request_test_mode_enabled()
                    and is_loopback_request(request)
                ),
            }
        }
    return {
        "user": {
            "username": principal.claims["preferred_username"],
            "name": principal.claims.get("name") or principal.claims["preferred_username"],
            "roles": sorted(list(principal.roles)),
            "portal_role": principal.claims.get("portal_role"),
            "is_shared_account": False,
            "license_request_test_mode": (
                local_license_request_test_mode_enabled()
                and is_loopback_request(request)
            ),
        }
    }


@router.post("/logout")
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    # Server-side logout: delete the session row so the token dies NOW.
    # Next login inserts a brand-new jti row -> brand-new token is issued.
    if session_token:
        try:
            claims = jwt.decode(
                session_token, _signing_secret(), algorithms=["HS256"],
                audience=SESSION_AUDIENCE, issuer=SESSION_ISSUER,
                options={"verify_exp": False},
            )
            jti = claims.get("jti")
            if jti:
                db.query(PortalSession).filter(PortalSession.jti == jti).delete()
                db.commit()
        except Exception:
            pass
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/api/v1",
        secure=os.getenv("AUTH_COOKIE_SECURE", "false").strip().lower()
        in {"true", "1", "yes"},
        httponly=True,
        samesite="strict",
    )
    return {"status": "signed out"}
