from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models import (
    Application,
    License,
    LicenseAssignment,
    Microsoft365Data,
    SyncLog,
    User,
)


def save_microsoft365_application() -> Application:
    db: Session = SessionLocal()
    try:
        application = (
            db.query(Application)
            .filter(Application.name == "Microsoft 365")
            .first()
        )

        if application is None:
            application = Application(
                name="Microsoft 365",
                vendor="Microsoft",
                category="Productivity",
                status="Active",
                last_sync=datetime.utcnow(),
            )
            db.add(application)
            db.flush()
        else:
            application.vendor = "Microsoft"
            application.category = "Productivity"
            application.status = "Active"
            application.last_sync = datetime.utcnow()

        db.commit()
        db.refresh(application)
        return application
    finally:
        db.close()


def ensure_microsoft365_application() -> Application:
    return save_microsoft365_application()


def save_microsoft365_licenses(
    licenses: list[dict],
    application: Application | None = None,
) -> dict:
    db: Session = SessionLocal()
    try:
        application_record = application or save_microsoft365_application()
        inserted = 0
        updated = 0

        for license_item in licenses:
            product = (
                license_item.get("product")
                or license_item.get("sku_part_number")
                or license_item.get("sku_id")
                or "Microsoft 365"
            )
            license_type = (
                license_item.get("sku_part_number")
                or license_item.get("product")
                or "Microsoft 365"
            )

            purchased_quantity = int(license_item.get("purchased_quantity") or 0)
            assigned_quantity = int(license_item.get("assigned_quantity") or 0)
            available_quantity = int(license_item.get("available_quantity") or 0)
            used_quantity = int(license_item.get("assigned_quantity") or assigned_quantity)

            existing_license = (
                db.query(License)
                .filter(
                    License.application_id == application_record.id,
                    License.product == product,
                )
                .first()
            )

            if existing_license is not None:
                existing_license.product = product
                existing_license.license_type = license_type
                existing_license.purchased_qty = purchased_quantity
                existing_license.assigned_qty = assigned_quantity
                existing_license.available_qty = available_quantity
                existing_license.used_qty = used_quantity
                existing_license.data_source = (
                    license_item.get("data_source") or "Microsoft Graph API"
                )
                existing_license.last_updated = datetime.utcnow()
                updated += 1
            else:
                new_license = License(
                    application_id=application_record.id,
                    product=product,
                    license_type=license_type,
                    purchased_qty=purchased_quantity,
                    assigned_qty=assigned_quantity,
                    available_qty=available_quantity,
                    used_qty=used_quantity,
                    data_source=(
                        license_item.get("data_source") or "Microsoft Graph API"
                    ),
                    last_updated=datetime.utcnow(),
                )
                db.add(new_license)
                inserted += 1

        db.commit()
        return {
            "success": True,
            "application": "Microsoft 365",
            "inserted": inserted,
            "updated": updated,
            "total": inserted + updated,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save_microsoft365_users(
    users: list[dict],
    application: Application | None = None,
) -> dict:
    db: Session = SessionLocal()
    try:
        application_record = application or save_microsoft365_application()
        inserted = 0
        updated = 0

        for user_item in users:
            external_user_id = user_item.get("external_user_id")
            if not external_user_id:
                continue

            existing_user = (
                db.query(User)
                .filter(
                    User.application_id == application_record.id,
                    User.external_user_id == external_user_id,
                )
                .first()
            )

            name = user_item.get("name") or user_item.get("email") or external_user_id
            email = user_item.get("email")
            status = user_item.get("status") or "active"
            role = user_item.get("job_title") or user_item.get("department")

            if existing_user is not None:
                existing_user.name = name
                existing_user.email = email
                existing_user.status = status
                existing_user.role = role
                updated += 1
            else:
                new_user = User(
                    application_id=application_record.id,
                    external_user_id=external_user_id,
                    name=name,
                    email=email,
                    status=status,
                    role=role,
                )
                db.add(new_user)
                inserted += 1

        db.commit()
        return {
            "success": True,
            "application": "Microsoft 365",
            "inserted": inserted,
            "updated": updated,
            "total": inserted + updated,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save_microsoft365_license_assignments(
    assignments: list[dict],
    application_id: int | None = None,
) -> dict:
    db: Session = SessionLocal()
    try:
        if application_id is None:
            application_record = save_microsoft365_application()
            application_id = application_record.id

        inserted = 0
        updated = 0

        for assignment in assignments:
            license_id = assignment.get("license_id")
            user_id = assignment.get("user_id")
            if not license_id or not user_id:
                continue

            existing_assignment = (
                db.query(LicenseAssignment)
                .filter(
                    LicenseAssignment.license_id == license_id,
                    LicenseAssignment.user_id == user_id,
                )
                .first()
            )

            if existing_assignment is not None:
                existing_assignment.assigned_date = (
                    assignment.get("assigned_date") or datetime.utcnow()
                )
                existing_assignment.status = assignment.get("status") or "assigned"
                updated += 1
            else:
                new_assignment = LicenseAssignment(
                    license_id=license_id,
                    user_id=user_id,
                    assigned_date=assignment.get("assigned_date") or datetime.utcnow(),
                    status=assignment.get("status") or "assigned",
                )
                db.add(new_assignment)
                inserted += 1

        db.commit()
        return {
            "success": True,
            "application": "Microsoft 365",
            "inserted": inserted,
            "updated": updated,
            "total": inserted + updated,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save_microsoft365_data(
    records: list[dict],
    application: Application | None = None,
) -> dict:
    db: Session = SessionLocal()
    try:
        application_record = application or save_microsoft365_application()
        inserted = 0
        updated = 0

        for item in records:
            sku_id = item.get("sku_id")
            if not sku_id:
                continue

            existing_record = (
                db.query(Microsoft365Data)
                .filter(
                    Microsoft365Data.application_id == application_record.id,
                    Microsoft365Data.sku_id == sku_id,
                )
                .first()
            )

            if existing_record is not None:
                existing_record.product = item.get("product") or item.get("sku_part_number")
                existing_record.sku_part_number = item.get("sku_part_number")
                existing_record.license_type = item.get("license_type") or item.get("sku_part_number") or "Microsoft 365"
                existing_record.purchased_quantity = int(item.get("purchased_quantity") or 0)
                existing_record.assigned_quantity = int(item.get("assigned_quantity") or 0)
                existing_record.available_quantity = int(item.get("available_quantity") or 0)
                existing_record.consumed_quantity = int(item.get("assigned_quantity") or 0)
                existing_record.synced_at = datetime.utcnow()
                existing_record.updated_at = datetime.utcnow()
                updated += 1
            else:
                new_record = Microsoft365Data(
                    application_id=application_record.id,
                    sku_id=sku_id,
                    product=item.get("product") or item.get("sku_part_number") or "Microsoft 365",
                    sku_part_number=item.get("sku_part_number"),
                    license_type=item.get("license_type") or item.get("sku_part_number") or "Microsoft 365",
                    purchased_quantity=int(item.get("purchased_quantity") or 0),
                    assigned_quantity=int(item.get("assigned_quantity") or 0),
                    available_quantity=int(item.get("available_quantity") or 0),
                    consumed_quantity=int(item.get("assigned_quantity") or 0),
                    synced_at=datetime.utcnow(),
                )
                db.add(new_record)
                inserted += 1

        db.commit()
        return {
            "success": True,
            "application": "Microsoft 365",
            "inserted": inserted,
            "updated": updated,
            "total": inserted + updated,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save_microsoft365_inventory(
    license_payload: dict,
    user_payload: dict,
) -> dict:
    application = save_microsoft365_application()
    license_result = save_microsoft365_licenses(
        license_payload.get("licenses", []),
        application=application,
    )
    user_result = save_microsoft365_users(
        user_payload.get("users", []),
        application=application,
    )
    vendor_result = save_microsoft365_data(
        license_payload.get("licenses", []),
        application=application,
    )
    return {
        "success": True,
        "application": "Microsoft 365",
        "licenses_processed": license_result.get("total", 0),
        "users_processed": user_result.get("total", 0),
        "vendor_data_processed": vendor_result.get("total", 0),
    }


def save_microsoft365_sync_log(
    application_id: int | None,
    status: str,
    records_processed: int,
    error_message: str | None,
) -> dict:
    db: Session = SessionLocal()
    try:
        sync_log = SyncLog(
            application_id=application_id,
            status=status,
            records_processed=records_processed,
            error_message=error_message,
            sync_time=datetime.utcnow(),
        )
        db.add(sync_log)
        db.commit()
        db.refresh(sync_log)
        return {
            "id": sync_log.id,
            "status": sync_log.status,
            "records_processed": sync_log.records_processed,
            "error_message": sync_log.error_message,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
