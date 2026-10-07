from datetime import datetime, timezone
from typing import Any


def build_inventory_payload(
    workspace_info: dict[str, Any],
    license_info: dict[str, Any],
    users_payload: dict[str, Any],
    usage_payload: dict[str, Any],
) -> dict[str, Any]:
    users_data = users_payload or {}
    usage_data = usage_payload or {}
    license_data = license_info or {}

    import re

    def _clean(val: Any) -> Any:
        if not val or not isinstance(val, str):
            return val
        cleaned = re.sub(r"\s*\([Tt]he\s*zastudios\)", "", val, flags=re.IGNORECASE)
        cleaned = re.sub(r"the\s*zastudios|zastudios", "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned or val

    clean_license = {
        "plan": _clean(license_data.get("plan")),
        "license_type": license_data.get("license_type"),
        "entitled_quantity": license_data.get("entitled_quantity"),
        "assigned_quantity": license_data.get("assigned_quantity"),
        "available_quantity": license_data.get("available_quantity"),
        "renewal_date": license_data.get("renewal_date"),
        "cost": license_data.get("cost"),
        "currency": license_data.get("currency"),
        "data_source": license_data.get("data_source", "Slack API"),
        "data_available": bool(license_data.get("data_available", False)),
    }

    users_summary = {
        "total": users_data.get("total_users", 0),
        "active": users_data.get("active_users", 0),
        "inactive": 0,
        "deleted": users_data.get("deleted_users", 0),
        "assigned": license_data.get("assigned_quantity", 0) or 0,
    }

    return {
        "application": {
            "name": "Slack",
            "vendor": "Slack",
            "category": "Collaboration",
        },
        "workspace": {
            "workspace_id": workspace_info.get("workspace_id"),
            "workspace_name": _clean(workspace_info.get("workspace_name")),
        },
        "license": clean_license,
        "users": users_summary,
        "usage": {
            "available": bool(usage_data.get("usage_available", False)),
            "active_users": usage_data.get("active_users", 0),
            "inactive_users": usage_data.get("inactive_users", 0),
        },
        "integration": {
            "status": workspace_info.get("status", "connected"),
            "last_sync": datetime.now(timezone.utc).isoformat(),
        },
    }


def get_optimization_recommendations(
    users_payload: dict[str, Any],
    usage_payload: dict[str, Any],
    license_info: dict[str, Any],
) -> dict[str, Any]:
    recommendations: list[dict[str, Any]] = []
    users = users_payload.get("users", [])

    for user in users:
        if user.get("status") == "active":
            continue
        recommendations.append(
            {
                "type": "inactive_user",
                "slack_user_id": user.get("slack_user_id"),
                "email": user.get("email"),
                "reason": "User is not active in the Slack workspace and should be reviewed against entitlement.",
                "action": "Review license assignment",
            }
        )

    deleted_users = users_payload.get("deleted_users", 0)
    if deleted_users:
        recommendations.append(
            {
                "type": "deleted_user",
                "slack_user_id": None,
                "email": None,
                "reason": "Deleted Slack users remain in the workspace inventory and may require review against assignments.",
                "action": "Review deleted user records",
            }
        )

    if not license_info.get("data_available", False):
        recommendations.append(
            {
                "type": "missing_license_data",
                "slack_user_id": None,
                "email": None,
                "reason": "Slack billing or license data is not available with the current token and permissions.",
                "action": "Request enterprise or admin permissions to retrieve billing entitlements",
            }
        )

    usage = usage_payload or {}
    if usage.get("inactive_users", 0):
        recommendations.append(
            {
                "type": "inactive_usage",
                "slack_user_id": None,
                "email": None,
                "reason": "Some Slack users appear inactive and could represent optimization opportunities.",
                "action": "Review team activity for possible subscription optimization",
            }
        )

    return {"application": "Slack", "recommendations": recommendations}
