import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class Settings(BaseModel):
    SLACK_BOT_TOKEN: str | None = os.getenv("SLACK_BOT_TOKEN") or None
    SLACK_USER_TOKEN: str | None = os.getenv("SLACK_USER_TOKEN") or None
    SLACK_ADMIN_TOKEN: str | None = os.getenv("SLACK_ADMIN_TOKEN") or None
    MS_TENANT_ID: str | None = os.getenv("MS_TENANT_ID") or None
    MS_CLIENT_ID: str | None = os.getenv("MS_CLIENT_ID") or None
    MS_CLIENT_SECRET: str | None = os.getenv("MS_CLIENT_SECRET") or None
    APP_NAME: str = "Slack License Inventory API"


def get_settings() -> Settings:
    return Settings()
