from __future__ import annotations

from datetime import datetime
from typing import Any

from database.database import SessionLocal
from database.microsoft365_assigned_users_repository import (
    bulk_upsert_assigned_users,
    mark_stale_assignments_revoked,
)
from database.microsoft365_repository import (
    save_microsoft365_application,
    save_microsoft365_data,
    save_microsoft365_licenses,
    save_microsoft365_license_assignments,
    save_microsoft365_sync_log,
    save_microsoft365_users,
)
from database.models import License, LicenseAssignment, Microsoft365Data, User


def sync_microsoft365_inventory() -> dict[str, Any]:
    application = save_microsoft365_application()

    try:
        from services.microsoft365.microsoft365_license import get_microsoft365_license_inventory
        from services.microsoft365.microsoft365_users import get_microsoft365_user_inventory

        license_payload = get_microsoft365_license_inventory()
        user_payload = get_microsoft365_user_inventory()

        license_result = save_microsoft365_licenses(
            license_payload.get("licenses", []),
            application=application,
        )
        vendor_result = save_microsoft365_data(
            license_payload.get("licenses", []),
            application=application,
        )
        user_result = save_microsoft365_users(
            user_payload.get("users", []),
            application=application,
        )

        db = SessionLocal()
        try:
            license_rows = (
                db.query(License)
                .filter(License.application_id == application.id)
                .all()
            )
            license_by_product: dict[str, list[License]] = {}
            for license_row in license_rows:
                if license_row.product:
                    license_by_product.setdefault(license_row.product, []).append(
                        license_row
                    )
            license_by_type: dict[str, list[License]] = {}
            for license_row in license_rows:
                if license_row.license_type:
                    license_by_type.setdefault(license_row.license_type, []).append(
                        license_row
                    )

            sku_rows = (
                db.query(Microsoft365Data)
                .filter(Microsoft365Data.application_id == application.id)
                .all()
            )
            active_sku_ids = {
                str(item["sku_id"])
                for item in license_payload.get("licenses", [])
                if item.get("sku_id")
            }
            sku_to_license: dict[str, License] = {}
            for sku_row in sku_rows:
                if sku_row.sku_id not in active_sku_ids:
                    continue
                matching_licenses = license_by_product.get(sku_row.product, [])
                if not matching_licenses and sku_row.sku_part_number:
                    matching_licenses = license_by_type.get(
                        sku_row.sku_part_number,
                        [],
                    )
                if len(matching_licenses) > 1:
                    raise ValueError(
                        f"Microsoft Graph SKU {sku_row.sku_id} matches "
                        "multiple license records"
                    )
                if matching_licenses:
                    sku_to_license[sku_row.sku_id] = matching_licenses[0]

            user_rows = (
                db.query(User)
                .filter(User.application_id == application.id)
                .all()
            )
            user_lookup = {user.external_user_id: user for user in user_rows}

            assignment_records: list[dict[str, Any]] = []
            assigned_user_records: list[dict[str, Any]] = []
            for user_item in user_payload.get("users", []):
                external_user_id = user_item.get("external_user_id")
                if not external_user_id:
                    continue

                user_row = user_lookup.get(external_user_id)
                if user_row is None:
                    continue

                assigned_skus = user_item.get("assigned_licenses") or []
                seen = set()
                for sku_id in assigned_skus:
                    license_row = sku_to_license.get(sku_id)

                    if not license_row or license_row.id in seen:
                        continue

                    seen.add(license_row.id)
                    assignment_records.append(
                        {
                            "license_id": license_row.id,
                            "user_id": user_row.id,
                            "assigned_date": datetime.utcnow(),
                            "status": "assigned",
                        }
                    )
                    assigned_user_records.append(
                        {
                            "application_id": application.id,
                            "license_id": license_row.id,
                            "user_id": user_row.id,
                            "sku_id": sku_id,
                            "display_name": user_row.name,
                            "email": user_row.email,
                            "external_user_id": user_row.external_user_id,
                            "status": "assigned",
                            "assigned_at": datetime.utcnow(),
                        }
                    )

            existing_assignments = (
                db.query(LicenseAssignment)
                .join(License, LicenseAssignment.license_id == License.id)
                .filter(License.application_id == application.id)
                .all()
            )

            current_keys = {
                (record["license_id"], record["user_id"])
                for record in assignment_records
            }

            for assignment in existing_assignments:
                key = (assignment.license_id, assignment.user_id)
                if key not in current_keys:
                    assignment.status = "revoked"
                    assignment.assigned_date = datetime.utcnow()

            db.commit()

            assignment_result = save_microsoft365_license_assignments(
                assignment_records,
                application_id=application.id,
            )
            assigned_users_result = bulk_upsert_assigned_users(
                application_id=application.id,
                assigned_users=assigned_user_records,
            )
            current_keys = {
                (record["license_id"], record["user_id"])
                for record in assignment_records
            }
            mark_stale_assignments_revoked(
                application_id=application.id,
                current_keys=current_keys,
            )

            total_processed = (
                int(license_result.get("total", 0))
                + int(vendor_result.get("total", 0))
                + int(user_result.get("total", 0))
                + int(assignment_result.get("total", 0))
                + int(assigned_users_result.get("total", 0))
            )

            save_microsoft365_sync_log(
                application_id=application.id,
                status="success",
                records_processed=total_processed,
                error_message=None,
            )

            return {
                "success": True,
                "application": "Microsoft 365",
                "licenses_processed": int(license_result.get("total", 0)),
                "microsoft365_data_processed": int(vendor_result.get("total", 0)),
                "users_processed": int(user_result.get("total", 0)),
                "assignments_processed": int(assignment_result.get("total", 0)),
                "assigned_users_processed": int(assigned_users_result.get("total", 0)),
                "sync_status": "completed",
            }
        finally:
            db.close()
    except Exception as exc:
        try:
            save_microsoft365_sync_log(
                application_id=application.id,
                status="failed",
                records_processed=0,
                error_message=str(exc),
            )
        except Exception:
            pass
        raise
