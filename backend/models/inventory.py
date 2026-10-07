from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SlackWorkspace(BaseModel):
    application: str = Field(default="Slack")
    vendor: str = Field(default="Slack")
    workspace_id: str | None = Field(default=None)
    workspace_name: str | None = Field(default=None)
    status: str = Field(default="connected")


class SlackUsage(BaseModel):
    application: str = Field(default="Slack")
    usage_available: bool = Field(default=False)
    active_users: int = Field(default=0)
    inactive_users: int = Field(default=0)
    deleted_users: int = Field(default=0)
    usage_records: list[dict[str, Any]] = Field(default_factory=list)


class SlackInventory(BaseModel):
    application: dict[str, str] = Field(default_factory=lambda: {"name": "Slack", "vendor": "Slack", "category": "Collaboration"})
    workspace: dict[str, str | None] = Field(default_factory=lambda: {"workspace_id": None, "workspace_name": None})
    license: dict[str, Any] = Field(default_factory=dict)
    users: dict[str, int | None] = Field(default_factory=lambda: {"total": 0, "active": 0, "inactive": 0, "deleted": 0, "assigned": 0})
    usage: dict[str, Any] = Field(default_factory=lambda: {"available": False, "active_users": 0, "inactive_users": 0})
    integration: dict[str, str | None | datetime] = Field(default_factory=lambda: {"status": "connected", "last_sync": None})


class OptimizationRecommendation(BaseModel):
    type: str
    slack_user_id: str | None = None
    email: str | None = None
    reason: str
    action: str
