from typing import Any

from services.slack_client import SlackClient
from database.license_repository import save_slack_users


def normalize_slack_user(member: dict[str, Any]) -> dict[str, Any]:
    profile = member.get("profile", {}) or {}

    if member.get("deleted"):
        status = "deleted"
    elif member.get("is_bot"):
        status = "bot"
    else:
        status = "active"

    return {
        "slack_user_id": member.get("id"),
        "name": member.get("name"),
        "display_name": profile.get("display_name") or member.get("name"),
        "real_name": profile.get("real_name"),
        "email": profile.get("email"),
        "status": status,
        "is_admin": bool(member.get("is_admin")),
        "is_owner": bool(member.get("is_owner")),
        "timezone": member.get("tz"),
        "timezone_label": member.get("tz_label"),
        "timezone_offset": member.get("tz_offset"),
        "is_restricted": bool(member.get("is_restricted")),
        "is_ultra_restricted": bool(member.get("is_ultra_restricted")),
        "is_invited_user": bool(member.get("is_invited_user")),
        "updated": member.get("updated"),
    }


def list_slack_users(client: SlackClient) -> dict[str, Any]:

    token = client.get_token_for_scope("users")

    if not token:
        return {
            "application": "Slack",
            "data_available": False,
            "total_users": 0,
            "active_users": 0,
            "deleted_users": 0,
            "bot_users": 0,
            "users_with_email": 0,
            "users": [],
            "error": "No Slack token configured for users.",
            "required_scopes": [
                "users:read",
                "users:read.email",
            ],
        }

    try:
        # Slack pagination may return None.
        # Convert None to an empty list so the code below
        # can safely iterate over the result.
        members = client.paginate(
            "users.list",
            response_key="members",
            params={"limit": 200},
            token=token,
        ) or []

    except Exception as exc:

        error_text = str(exc)

        return {
            "application": "Slack",
            "data_available": False,
            "total_users": 0,
            "active_users": 0,
            "deleted_users": 0,
            "bot_users": 0,
            "users_with_email": 0,
            "users": [],
            "error": error_text,
            "required_scopes": [
                "users:read",
                "users:read.email",
            ],
            "required_action": (
                "Add users:read and users:read.email to the Slack app, "
                "then reinstall the app to the workspace and update the token."
            ),
        }

    # Normalize Slack API users
    normalized = [
        normalize_slack_user(member)
        for member in members
        if isinstance(member, dict)
    ]

    # Count active users
    active_count = sum(
        1
        for item in normalized
        if item.get("status") == "active"
    )

    # Count deleted users
    deleted_count = sum(
        1
        for item in normalized
        if item.get("status") == "deleted"
    )

    # Count bot users
    bot_count = sum(
        1
        for item in normalized
        if item.get("status") == "bot"
    )

    # Count users with email
    users_with_email = sum(
        1
        for item in normalized
        if item.get("email")
    )

    # --------------------------------------------------
    # Save Slack users into PostgreSQL
    # --------------------------------------------------
    try:
        database_result = save_slack_users(normalized)

    except Exception as exc:

        database_result = {
            "success": False,
            "error": str(exc),
        }

    return {
        "application": "Slack",
        "data_available": True,
        "total_users": len(normalized),
        "active_users": active_count,
        "deleted_users": deleted_count,
        "bot_users": bot_count,
        "users_with_email": users_with_email,
        "users": normalized,
        "data_source": "Slack API - users.list",
        "database": database_result,
    }


def get_user_mapping(client: SlackClient) -> dict[str, Any]:

    users_payload = list_slack_users(client)

    if not users_payload.get("data_available"):
        return {
            "application": "Slack",
            "data_available": False,
            "total_mappings": 0,
            "mappings": [],
            "error": users_payload.get("error"),
            "required_scopes": users_payload.get(
                "required_scopes",
                [],
            ),
        }

    mappings = []

    for user in users_payload.get("users", []):

        email = user.get("email")

        mappings.append(
            {
                "slack_user_id": user.get("slack_user_id"),
                "name": (
                    user.get("real_name")
                    or user.get("display_name")
                    or user.get("name")
                ),
                "email": email,
                "employee_id": None,
                "mapping_status": (
                    "pending"
                    if email
                    else "missing_email"
                ),
            }
        )

    return {
        "application": "Slack",
        "data_available": True,
        "total_mappings": len(mappings),
        "mappings": mappings,
    }