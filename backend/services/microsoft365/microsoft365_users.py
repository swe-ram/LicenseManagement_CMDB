from __future__ import annotations

from typing import Any

from services.microsoft365.microsoft365_client import MicrosoftGraphClient


def _normalize_user(item: dict[str, Any]) -> dict[str, Any]:
    assigned_licenses = item.get("assignedLicenses") or []
    license_ids = [
        license.get("skuId")
        for license in assigned_licenses
        if isinstance(license, dict) and license.get("skuId")
    ]
    email = item.get("mail") or item.get("userPrincipalName")

    return {
        "external_user_id": item.get("id"),
        "name": item.get("displayName") or item.get("userPrincipalName"),
        "email": email,
        "status": "active" if item.get("accountEnabled") is not False else "inactive",
        "department": item.get("department"),
        "job_title": item.get("jobTitle"),
        "assigned_licenses": license_ids,
    }


def get_microsoft365_user_inventory() -> dict[str, Any]:
    client = MicrosoftGraphClient()
    params = {
        "$select": (
            "id,displayName,userPrincipalName,mail,accountEnabled,jobTitle,department,assignedLicenses"
        )
    }
    response = client.get_all("/v1.0/users", params=params)
    users = [_normalize_user(item) for item in response]

    return {
        "application": "Microsoft 365",
        "vendor": "Microsoft",
        "data_available": bool(users),
        "total_users": len(users),
        "users": users,
    }
