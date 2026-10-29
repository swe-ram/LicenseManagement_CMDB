from __future__ import annotations

from typing import Any

from database.sophos_repository import (
    ensure_sophos_application,
    get_sophos_licenses,
    get_sophos_users,
    save_sophos_licenses,
    save_sophos_users,
)
from services.sophos.sophos_client import SophosClient, SophosAPIError


def sync_sophos_users(client: SophosClient | None = None) -> dict[str, Any]:
    """Fetch live directory users and endpoints from Sophos Central and persist to sophos_userdata."""
    print("Fetching users from Sophos Central API...")
    sophos_client = client or SophosClient()
    users = sophos_client.get_users()

    if not users:
        print("[WARN] No Sophos users returned by API.")
        return {
            "success": True,
            "application": "Sophos",
            "users_processed": 0,
            "sync_status": "completed_empty",
        }

    app_record = ensure_sophos_application()
    db_result = save_sophos_users(users, application=app_record)

    print(
        f"Sophos users sync completed: {len(users)} users processed "
        f"(inserted: {db_result.get('inserted', 0)}, updated: {db_result.get('updated', 0)})."
    )

    return {
        "success": True,
        "application": "Sophos",
        "users_processed": len(users),
        "database": db_result,
        "sync_status": "completed",
    }


def sync_sophos_inventory() -> dict[str, Any]:
    """Fetch live license data and user data from Sophos Central and persist to database."""
    print("Connecting to Sophos Central API...")
    client = SophosClient()
    licenses = client.get_licenses()

    app_record = ensure_sophos_application()
    license_db_result = {}
    if licenses:
        license_db_result = save_sophos_licenses(licenses, application=app_record)
        print(
            f"Sophos licenses sync completed: {len(licenses)} licenses processed "
            f"(inserted: {license_db_result.get('inserted', 0)}, updated: {license_db_result.get('updated', 0)})."
        )
    else:
        print("[WARN] No Sophos licenses returned by API.")

    # Fetch and persist users into sophos_userdata
    users_result = sync_sophos_users(client=client)

    return {
        "success": True,
        "application": "Sophos",
        "licenses_processed": len(licenses),
        "license_database": license_db_result,
        "users_processed": users_result.get("users_processed", 0),
        "users_database": users_result.get("database", {}),
        "sync_status": "completed",
    }

