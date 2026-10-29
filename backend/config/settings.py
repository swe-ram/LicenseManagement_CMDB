import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv()


class Settings(BaseModel):
    SLACK_BOT_TOKEN: str | None = os.getenv("SLACK_BOT_TOKEN") or None
    SLACK_USER_TOKEN: str | None = os.getenv("SLACK_USER_TOKEN") or None
    SLACK_ADMIN_TOKEN: str | None = os.getenv("SLACK_ADMIN_TOKEN") or None
    MS_TENANT_ID: str | None = os.getenv("MS_TENANT_ID") or None
    MS_CLIENT_ID: str | None = os.getenv("MS_CLIENT_ID") or None
    MS_CLIENT_SECRET: str | None = os.getenv("MS_CLIENT_SECRET") or None
    SOPHOS_CLIENT_ID: str | None = os.getenv("SOPHOS_CLIENT_ID") or None
    SOPHOS_CLIENT_SECRET: str | None = os.getenv("SOPHOS_CLIENT_SECRET") or None
    APP_NAME: str = "Slack License Inventory API"
    # ── Approval email (license request flow) ──
    MAIL_TRANSPORT: str = os.getenv("MAIL_TRANSPORT", "auto") or "auto"
    MAIL_FROM: str | None = os.getenv("MAIL_FROM") or os.getenv("SMTP_FROM") or None
    SMTP_HOST: str | None = os.getenv("SMTP_HOST") or None
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587") or 587)
    SMTP_USER: str | None = os.getenv("SMTP_USER") or None
    SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD") or None
    SMTP_FROM: str | None = os.getenv("SMTP_FROM") or os.getenv("MAIL_FROM") or None
    SMTP_TLS: bool = (os.getenv("SMTP_TLS", "true") or "true").strip().lower() in {"true", "1", "yes"}
    PORTAL_BASE_URL: str | None = os.getenv("PORTAL_BASE_URL") or None


def get_settings() -> Settings:
    return Settings()

