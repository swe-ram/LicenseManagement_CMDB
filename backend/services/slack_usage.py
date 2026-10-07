from typing import Any

from fastapi import HTTPException

from services.slack_client import SlackClient
from services.slack_users import list_slack_users


def get_usage_summary(client: SlackClient) -> dict[str, Any]:
    users_payload = list_slack_users(client)
    users = users_payload.get("users", [])
    deleted_users = sum(1 for user in users if user.get("status") == "deleted")
    active_users = sum(1 for user in users if user.get("status") == "active")
    inactive_users = 0

    usage_records: list[dict[str, Any]] = []
    token = client.get_token_for_scope("presence")
    if token:
        for user in users:
            if user.get("status") == "deleted":
                continue
            try:
                presence_payload = client.request("users.getPresence", params={"user": user.get("slack_user_id")}, token=token)
            except HTTPException:
                continue

            presence_status = presence_payload.get("presence")
            if presence_status in {"away", "auto"}:
                inactive_users += 1

            usage_records.append(
                {
                    "slack_user_id": user.get("slack_user_id"),
                    "email": user.get("email"),
                    "presence": presence_status,
                    "last_activity": presence_payload.get("last_activity_ts"),
                    "status": user.get("status"),
                }
            )

    usage_available = any(record.get("presence") is not None for record in usage_records)
    return {
        "application": "Slack",
        "usage_available": usage_available,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "deleted_users": deleted_users,
        "usage_records": usage_records,
    }
