from __future__ import annotations

from typing import Any

from services.microsoft365.microsoft365_client import MicrosoftGraphClient, MicrosoftGraphError


def _normalize_license(item: dict[str, Any]) -> dict[str, Any]:
    prepaid_units = item.get("prepaidUnits") or {}
    purchased_quantity = prepaid_units.get("enabled") or 0
    suspended_quantity = prepaid_units.get("suspended") or 0
    warning_quantity = prepaid_units.get("warning") or 0
    assigned_quantity = item.get("consumedUnits") or 0
    available_quantity = max(purchased_quantity - assigned_quantity, 0)

    product_name = item.get("productName") or item.get("skuPartNumber") or "Microsoft 365"

    return {
        "sku_id": item.get("skuId"),
        "sku_part_number": item.get("skuPartNumber"),
        "product": product_name,
        "capability_status": item.get("capabilityStatus") or "Unknown",
        "purchased_quantity": purchased_quantity,
        "assigned_quantity": assigned_quantity,
        "available_quantity": available_quantity,
        "suspended_quantity": suspended_quantity,
        "warning_quantity": warning_quantity,
        "applies_to": item.get("appliesTo"),
        "service_plans": item.get("servicePlans") or [],
        "data_source": "Microsoft Graph API",
    }


def get_microsoft365_license_inventory() -> dict[str, Any]:
    client = MicrosoftGraphClient()
    response = client.get_all("/v1.0/subscribedSkus")
    licenses = [_normalize_license(item) for item in response]

    return {
        "application": "Microsoft 365",
        "vendor": "Microsoft",
        "data_available": bool(licenses),
        "total_skus": len(licenses),
        "licenses": licenses,
    }
