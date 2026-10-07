from typing import Any

from fastapi import APIRouter

from config.settings import get_settings

from services.inventory_service import (
    build_inventory_payload,
    get_optimization_recommendations,
)

from services.slack_client import SlackClient
from services.slack_license import get_license_data
from services.slack_usage import get_usage_summary
from services.slack_users import (
    get_user_mapping,
    list_slack_users,
)
from services.slack_workspace import get_workspace_info


router = APIRouter(
    prefix="/slack",
    tags=["Slack"],
)


def _build_client() -> SlackClient:

    settings = get_settings()

    return SlackClient(
        bot_token=settings.SLACK_BOT_TOKEN,
        user_token=settings.SLACK_USER_TOKEN,
        admin_token=settings.SLACK_ADMIN_TOKEN,
    )


# ============================================================
# Slack Authentication
# ============================================================

@router.get(
    "/auth",
    summary="Slack authentication status",
)
async def auth() -> dict[str, Any]:

    client = _build_client()

    auth_payload = client.auth_test()

    return {
        "ok": auth_payload.get("ok"),
        "team_id": auth_payload.get("team_id"),
        "team": auth_payload.get("team"),
        "user_id": auth_payload.get("user_id"),
        "user": auth_payload.get("user"),
    }


# ============================================================
# Slack Workspace
# ============================================================

@router.get(
    "/workspace",
    summary="Slack workspace metadata",
)
async def workspace() -> dict[str, Any]:

    client = _build_client()

    return get_workspace_info(client)


# ============================================================
# Slack Users
# ============================================================

@router.get(
    "/users",
    summary="Slack users",
)
async def users() -> dict[str, Any]:

    client = _build_client()

    return list_slack_users(client)


# ============================================================
# Slack User Mapping
# ============================================================

@router.get(
    "/users/mapping",
    summary="Slack user to employee mapping",
)
async def users_mapping() -> dict[str, Any]:

    client = _build_client()

    return get_user_mapping(client)


# ============================================================
# Slack License
# ============================================================

@router.get(
    "/license",
    summary="Slack license information",
)
async def slack_license() -> dict[str, Any]:

    client = _build_client()

    return get_license_data(client)


# ============================================================
# Slack Usage
# ============================================================

@router.get(
    "/usage",
    summary="Slack usage information",
)
async def usage() -> dict[str, Any]:

    client = _build_client()

    return get_usage_summary(client)


# ============================================================
# Combined Slack Inventory
# ============================================================

@router.get(
    "/inventory",
    summary="Combined Slack inventory",
)
async def inventory() -> dict[str, Any]:

    client = _build_client()

    workspace_info = get_workspace_info(client)

    users_payload = list_slack_users(client)

    license_payload = get_license_data(client)

    usage_payload = get_usage_summary(client)

    return build_inventory_payload(
        workspace_info,
        license_payload,
        users_payload,
        usage_payload,
    )


# ============================================================
# Slack Optimization
# ============================================================

@router.get(
    "/optimization",
    summary="Slack optimization recommendations",
)
async def optimization() -> dict[str, Any]:

    client = _build_client()

    users_payload = list_slack_users(client)

    usage_payload = get_usage_summary(client)

    license_payload = get_license_data(client)

    return get_optimization_recommendations(
        users_payload,
        usage_payload,
        license_payload,
    )