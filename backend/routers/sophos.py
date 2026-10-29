from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.settings import get_settings
from database.sophos_repository import (
    ensure_sophos_application,
    get_sophos_licenses,
    get_sophos_users,
    save_sophos_licenses,
    save_sophos_users,
)

router = APIRouter(
    prefix="/sophos",
    tags=["Sophos"],
)


class SophosLicensePayload(BaseModel):
    license_id: str | None = None
    license_key: str | None = None
    product_name: str
    product_code: str | None = None
    license_type: str | None = "subscription"
    status: str | None = "active"
    purchased_quantity: int = 0
    assigned_quantity: int = 0
    available_quantity: int | None = None
    start_date: str | None = None
    expiration_date: str | None = None
    auto_renewal: bool = False
    cost: float | None = None
    currency: str | None = "USD"
    billing_cycle: str | None = "Annual"
    data_source: str | None = "Sophos Central API"


@router.get(
    "/auth",
    summary="Sophos credentials status",
)
async def auth_status() -> dict[str, Any]:
    """Check whether Sophos API credentials are configured in the environment."""
    settings = get_settings()
    has_client_id = bool(settings.SOPHOS_CLIENT_ID)
    has_client_secret = bool(settings.SOPHOS_CLIENT_SECRET)

    return {
        "application": "Sophos",
        "configured": has_client_id and has_client_secret,
        "has_client_id": has_client_id,
        "has_client_secret": has_client_secret,
        "message": (
            "Sophos API credentials configured"
            if (has_client_id and has_client_secret)
            else "Sophos credentials missing. Set SOPHOS_CLIENT_ID and SOPHOS_CLIENT_SECRET in .env"
        ),
    }


@router.get(
    "/license",
    summary="Sophos license inventory from database",
)
async def list_licenses() -> dict[str, Any]:
    """Return all stored Sophos licenses from the sophos_data table."""
    records = get_sophos_licenses()
    return {
        "application": "Sophos",
        "total": len(records),
        "licenses": records,
    }


@router.post(
    "/license",
    summary="Create or update a Sophos license record",
)
async def add_or_update_license(payload: SophosLicensePayload) -> dict[str, Any]:
    """Save or update a Sophos license in both sophos_data and central licenses."""
    result = save_sophos_licenses([payload.model_dump()])
    return result


@router.post(
    "/sync",
    summary="Trigger live synchronization from Sophos Central API into database",
)
async def trigger_sync() -> dict[str, Any]:
    """Fetch live data from Sophos Central API and update sophos_data table."""
    try:
        from services.sophos.sophos_sync import sync_sophos_inventory
        return sync_sophos_inventory()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/users",
    summary="Sophos users inventory from database",
)
async def list_users(
    license_id: str | None = None,
    product_code: str | None = None,
) -> dict[str, Any]:
    """Return stored Sophos users from sophos_userdata, optionally filtered by license."""
    records = get_sophos_users(license_id=license_id, product_code=product_code)
    return {
        "application": "Sophos",
        "license_id": license_id,
        "product_code": product_code,
        "total": len(records),
        "users": records,
    }


@router.get(
    "/licenses/{license_id}/assigned-users",
    summary="Get users assigned to a specific Sophos license",
)
async def get_license_assigned_users(license_id: str) -> dict[str, Any]:
    """Return users assigned to a specific Sophos license."""
    records = get_sophos_users(license_id=license_id)
    return {
        "application": "Sophos",
        "license_id": license_id,
        "total": len(records),
        "users": records,
    }


@router.post(
    "/users/sync",
    summary="Trigger live synchronization of Sophos users into sophos_userdata table",
)
async def trigger_users_sync() -> dict[str, Any]:
    """Fetch live users and endpoints from Sophos Central API and store in sophos_userdata."""
    try:
        from services.sophos.sophos_sync import sync_sophos_users
        return sync_sophos_users()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


