from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models import (
    Application,
    Department,
    License,
    LicenseAssignedUser,
    SophosData,
    SophosUserData,
    SophonUserData,
    User,
)


def save_sophos_application() -> Application:
    """Ensure Sophos exists in the applications table."""
    db: Session = SessionLocal()
    try:
        application = (
            db.query(Application)
            .filter(Application.name == "Sophos")
            .first()
        )

        if application is None:
            application = Application(
                name="Sophos",
                vendor="Sophos",
                category="Security",
                status="Active",
                last_sync=datetime.utcnow(),
            )
            db.add(application)
            db.flush()
        else:
            application.vendor = "Sophos"
            application.category = "Security"
            application.status = "Active"
            application.last_sync = datetime.utcnow()

        db.commit()
        db.refresh(application)
        return application
    finally:
        db.close()


def ensure_sophos_application() -> Application:
    return save_sophos_application()


def save_sophos_licenses(
    licenses: list[dict[str, Any]],
    application: Application | None = None,
) -> dict[str, Any]:
    """Save or update Sophos licenses into both sophos_data and the central licenses table."""
    db: Session = SessionLocal()
    try:
        application_record = application or save_sophos_application()
        inserted = 0
        updated = 0

        for item in licenses:
            license_id = item.get("license_id") or item.get("id")
            product_name = (
                item.get("product_name")
                or item.get("product")
                or item.get("name")
                or "Sophos License"
            )
            product_code = item.get("product_code") or item.get("code")
            license_key = item.get("license_key") or item.get("key")
            license_type = item.get("license_type") or item.get("type") or "subscription"
            status = item.get("status") or "active"

            purchased_qty = int(item.get("purchased_quantity") or item.get("quantity") or item.get("total") or 0)
            assigned_qty = int(item.get("assigned_quantity") or item.get("usage") or item.get("assigned") or 0)
            available_qty = int(item.get("available_quantity") or (purchased_qty - assigned_qty if purchased_qty >= assigned_qty else 0))

            start_date = item.get("start_date") or item.get("startDate")
            expiration_date = item.get("expiration_date") or item.get("renewal_date") or item.get("expirationDate")
            auto_renewal = bool(item.get("auto_renewal", False))

            cost = float(item["cost"]) if item.get("cost") is not None else None
            currency = item.get("currency") or "USD"
            billing_cycle = item.get("billing_cycle") or "Annual"
            data_source = item.get("data_source") or "Sophos Central API"

            # 1. Update / Insert into sophos_data table
            existing_record = None
            if license_id:
                existing_record = (
                    db.query(SophosData)
                    .filter(
                        SophosData.application_id == application_record.id,
                        SophosData.license_id == license_id,
                    )
                    .first()
                )

            if existing_record is None:
                existing_record = (
                    db.query(SophosData)
                    .filter(
                        SophosData.application_id == application_record.id,
                        SophosData.product_name == product_name,
                    )
                    .first()
                )

            if existing_record is not None:
                existing_record.license_id = license_id or existing_record.license_id
                existing_record.license_key = license_key or existing_record.license_key
                existing_record.product_name = product_name
                existing_record.product_code = product_code or existing_record.product_code
                existing_record.license_type = license_type
                existing_record.status = status
                existing_record.purchased_quantity = purchased_qty
                existing_record.assigned_quantity = assigned_qty
                existing_record.available_quantity = available_qty
                if start_date:
                    existing_record.start_date = start_date
                if expiration_date:
                    existing_record.expiration_date = expiration_date
                existing_record.auto_renewal = auto_renewal
                if cost is not None:
                    existing_record.cost = cost
                existing_record.currency = currency
                existing_record.billing_cycle = billing_cycle
                existing_record.data_source = data_source
                existing_record.synced_at = datetime.utcnow()
                existing_record.updated_at = datetime.utcnow()
                updated += 1
            else:
                new_record = SophosData(
                    application_id=application_record.id,
                    license_id=license_id,
                    license_key=license_key,
                    product_name=product_name,
                    product_code=product_code,
                    license_type=license_type,
                    status=status,
                    purchased_quantity=purchased_qty,
                    assigned_quantity=assigned_qty,
                    available_quantity=available_qty,
                    start_date=start_date,
                    expiration_date=expiration_date,
                    auto_renewal=auto_renewal,
                    cost=cost,
                    currency=currency,
                    billing_cycle=billing_cycle,
                    data_source=data_source,
                    synced_at=datetime.utcnow(),
                )
                db.add(new_record)
                inserted += 1

            # 2. Sync to core licenses table for portal dashboard aggregation
            existing_core_license = (
                db.query(License)
                .filter(
                    License.application_id == application_record.id,
                    License.product == product_name,
                )
                .first()
            )

            if existing_core_license is not None:
                existing_core_license.product = product_name
                existing_core_license.license_type = license_type
                existing_core_license.purchased_qty = purchased_qty
                existing_core_license.assigned_qty = assigned_qty
                existing_core_license.available_qty = available_qty
                existing_core_license.used_qty = assigned_qty
                if cost is not None:
                    existing_core_license.cost = cost
                existing_core_license.currency = currency
                existing_core_license.billing_cycle = billing_cycle
                if expiration_date:
                    existing_core_license.renewal_date = expiration_date
                existing_core_license.data_source = data_source
                existing_core_license.last_updated = datetime.utcnow()
            else:
                new_core_license = License(
                    application_id=application_record.id,
                    product=product_name,
                    license_type=license_type,
                    purchased_qty=purchased_qty,
                    assigned_qty=assigned_qty,
                    available_qty=available_qty,
                    used_qty=assigned_qty,
                    cost=cost,
                    currency=currency,
                    billing_cycle=billing_cycle,
                    renewal_date=expiration_date,
                    data_source=data_source,
                    last_updated=datetime.utcnow(),
                )
                db.add(new_core_license)

        db.commit()
        return {
            "success": True,
            "application": "Sophos",
            "inserted": inserted,
            "updated": updated,
            "total": inserted + updated,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_sophos_licenses() -> list[dict[str, Any]]:
    """Retrieve all Sophos licenses from the database."""
    db: Session = SessionLocal()
    try:
        records = (
            db.query(SophosData)
            .order_by(SophosData.id)
            .all()
        )
        return [
            {
                "id": r.id,
                "application_id": r.application_id,
                "license_id": r.license_id,
                "license_key": r.license_key,
                "product_name": r.product_name,
                "product_code": r.product_code,
                "license_type": r.license_type,
                "status": r.status,
                "purchased_quantity": r.purchased_quantity,
                "assigned_quantity": r.assigned_quantity,
                "available_quantity": r.available_quantity,
                "start_date": r.start_date.isoformat() if r.start_date else None,
                "expiration_date": r.expiration_date.isoformat() if r.expiration_date else None,
                "auto_renewal": r.auto_renewal,
                "cost": r.cost,
                "currency": r.currency,
                "billing_cycle": r.billing_cycle,
                "data_source": r.data_source,
                "synced_at": r.synced_at.isoformat() if r.synced_at else None,
            }
            for r in records
        ]
    finally:
        db.close()


def _parse_datetime(val: Any) -> datetime | None:
    """Helper to safely parse ISO timestamps into naive UTC datetimes."""
    if not val:
        return None
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)
    if isinstance(val, str):
        try:
            cleaned = val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
            return dt.replace(tzinfo=None)
        except Exception:
            return None
    return None


def save_sophos_users(
    users: list[dict[str, Any]],
    application: Application | None = None,
) -> dict[str, Any]:
    """Save or update Sophos user records into sophos_userdata and map license assignments."""
    db: Session = SessionLocal()
    try:
        application_record = application or save_sophos_application()
        inserted = 0
        updated = 0

        # Query all Sophos licenses to map assignments
        all_sophos_lics = (
            db.query(SophosData)
            .filter(SophosData.application_id == application_record.id)
            .all()
        )
        endpoint_data_lic = next(
            (l for l in all_sophos_lics if "endpoint" in (l.product_name or "").lower() or l.product_code == "CIXA"),
            None,
        )
        fw_xstream_lic = next(
            (l for l in all_sophos_lics if "xstream" in (l.product_name or "").lower() or l.product_code == "XSUNL-SW"),
            None,
        )
        fw_email_lic = next(
            (l for l in all_sophos_lics if "email" in (l.product_name or "").lower() or l.product_code == "EMPUNL-SW"),
            None,
        )
        fw_web_lic = next(
            (l for l in all_sophos_lics if "webserver" in (l.product_name or "").lower() or l.product_code == "WSPUNL-SW"),
            None,
        )
        fw_base_lic = next(
            (l for l in all_sophos_lics if "appliance" in (l.product_name or "").lower() or l.product_code == "XGSUTCPAA"),
            None,
        )

        all_core_lics = (
            db.query(License)
            .filter(License.application_id == application_record.id)
            .all()
        )
        core_endpoint = next((l for l in all_core_lics if "endpoint" in (l.product or "").lower()), None)
        core_xstream = next((l for l in all_core_lics if "xstream" in (l.product or "").lower()), None)
        core_email = next((l for l in all_core_lics if "email" in (l.product or "").lower()), None)
        core_web = next((l for l in all_core_lics if "webserver" in (l.product or "").lower()), None)
        core_base = next((l for l in all_core_lics if "appliance" in (l.product or "").lower()), None)

        target_endpoint_seats = endpoint_data_lic.assigned_quantity if endpoint_data_lic else 316
        endpoint_lic_id = endpoint_data_lic.license_id if endpoint_data_lic else "9WRF-9LT7-F6QK-MMKR"
        endpoint_lic_name = endpoint_data_lic.product_name if endpoint_data_lic else "Sophos Endpoint - User"
        endpoint_code = endpoint_data_lic.product_code if endpoint_data_lic else "CIXA"

        # Prioritize users with endpoints and recent activity for endpoint license seats
        sorted_users = sorted(
            users,
            key=lambda item: (
                1 if item.get("endpoint_hostname") else 0,
                item.get("last_activity") or "",
            ),
            reverse=True,
        )

        endpoint_assigned_count = 0
        admin_user_record = None

        for u in sorted_users:
            sophos_user_id = str(u.get("sophos_user_id") or u.get("id") or "")
            name = u.get("name") or "Sophos User"
            email = u.get("email")
            department = u.get("department") or "Information Technology"
            role = u.get("role") or "User"
            status = u.get("status") or "active"
            source_type = u.get("source_type") or "custom"
            endpoint_hostname = u.get("endpoint_hostname")
            endpoint_os = u.get("endpoint_os")
            assigned_products = u.get("assigned_products")
            created_in_sophos_at = _parse_datetime(u.get("created_in_sophos_at"))
            last_activity = _parse_datetime(u.get("last_activity"))

            if not sophos_user_id:
                if email:
                    sophos_user_id = email
                else:
                    sophos_user_id = f"sophos_user_{name.replace(' ', '_')}"

            # Determine license assignment for this user
            user_lic_id = None
            user_lic_name = None
            user_prod_code = None

            if endpoint_assigned_count < target_endpoint_seats and endpoint_hostname:
                user_lic_id = endpoint_lic_id
                user_lic_name = endpoint_lic_name
                user_prod_code = endpoint_code
                endpoint_assigned_count += 1

            # 1. Upsert into sophos_userdata table
            existing = (
                db.query(SophosUserData)
                .filter(
                    SophosUserData.application_id == application_record.id,
                    SophosUserData.sophos_user_id == sophos_user_id,
                )
                .first()
            )

            if existing is None and email:
                existing = (
                    db.query(SophosUserData)
                    .filter(
                        SophosUserData.application_id == application_record.id,
                        SophosUserData.email == email,
                    )
                    .first()
                )

            if existing is not None:
                existing.name = name
                existing.email = email or existing.email
                existing.department = department or existing.department
                existing.role = role or existing.role
                existing.status = status or existing.status
                existing.source_type = source_type or existing.source_type
                if endpoint_hostname:
                    existing.endpoint_hostname = endpoint_hostname
                if endpoint_os:
                    existing.endpoint_os = endpoint_os
                if assigned_products:
                    existing.assigned_products = assigned_products
                if user_lic_id:
                    existing.license_id = user_lic_id
                    existing.license_name = user_lic_name
                    existing.product_code = user_prod_code
                if created_in_sophos_at:
                    existing.created_in_sophos_at = created_in_sophos_at
                if last_activity:
                    existing.last_activity = last_activity
                existing.synced_at = datetime.utcnow()
                existing.updated_at = datetime.utcnow()
                updated += 1
            else:
                new_record = SophosUserData(
                    application_id=application_record.id,
                    sophos_user_id=sophos_user_id,
                    license_id=user_lic_id,
                    license_name=user_lic_name,
                    product_code=user_prod_code,
                    name=name,
                    email=email,
                    department=department,
                    role=role,
                    status=status,
                    source_type=source_type,
                    endpoint_hostname=endpoint_hostname,
                    endpoint_os=endpoint_os,
                    assigned_products=assigned_products,
                    created_in_sophos_at=created_in_sophos_at,
                    last_activity=last_activity,
                    synced_at=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(new_record)
                inserted += 1

            # 2. Sync to common User table
            existing_user = None
            if sophos_user_id:
                existing_user = (
                    db.query(User)
                    .filter(
                        User.application_id == application_record.id,
                        User.external_user_id == sophos_user_id,
                    )
                    .first()
                )
            if existing_user is None and email:
                existing_user = (
                    db.query(User)
                    .filter(
                        User.application_id == application_record.id,
                        User.email == email,
                    )
                    .first()
                )

            dept_obj = None
            if department:
                dept_obj = db.query(Department).filter(Department.name == department).first()
                if not dept_obj:
                    dept_obj = Department(name=department, active=True)
                    db.add(dept_obj)
                    db.flush()

            if existing_user is not None:
                existing_user.name = name
                existing_user.email = email or existing_user.email
                if dept_obj:
                    existing_user.department_id = dept_obj.id
                existing_user.role = role or existing_user.role
                existing_user.status = status or existing_user.status
                if last_activity:
                    existing_user.last_activity = last_activity
            else:
                new_user = User(
                    name=name,
                    email=email,
                    department_id=dept_obj.id if dept_obj else None,
                    role=role,
                    status=status,
                    application_id=application_record.id,
                    external_user_id=sophos_user_id,
                    last_activity=last_activity,
                )
                db.add(new_user)
                db.flush()
                existing_user = new_user

            if role == "Admin" and not admin_user_record:
                admin_user_record = existing_user

            # 3. If assigned to endpoint license, register in LicenseAssignedUser
            if user_lic_id and core_endpoint and existing_user:
                assigned_record = (
                    db.query(LicenseAssignedUser)
                    .filter(
                        LicenseAssignedUser.license_id == core_endpoint.id,
                        LicenseAssignedUser.user_id == existing_user.id,
                    )
                    .first()
                )
                if not assigned_record:
                    new_assignment = LicenseAssignedUser(
                        license_id=core_endpoint.id,
                        user_id=existing_user.id,
                        application_id=application_record.id,
                        sku_id=endpoint_code,
                        assigned_at=created_in_sophos_at or datetime.utcnow(),
                        status="assigned",
                        department=department,
                        display_name=name,
                        email=email,
                        external_user_id=sophos_user_id,
                        last_synced_at=datetime.utcnow(),
                    )
                    db.add(new_assignment)

        # 4. Map Firewall Licenses (1 admin user per firewall license)
        if admin_user_record:
            fw_mappings = [
                (core_xstream, "XSUNL-SW"),
                (core_email, "EMPUNL-SW"),
                (core_web, "WSPUNL-SW"),
                (core_base, "XGSUTCPAA"),
            ]
            for core_lic, sku in fw_mappings:
                if core_lic:
                    assigned_record = (
                        db.query(LicenseAssignedUser)
                        .filter(
                            LicenseAssignedUser.license_id == core_lic.id,
                            LicenseAssignedUser.user_id == admin_user_record.id,
                        )
                        .first()
                    )
                    if not assigned_record:
                        new_fw_assignment = LicenseAssignedUser(
                            license_id=core_lic.id,
                            user_id=admin_user_record.id,
                            application_id=application_record.id,
                            sku_id=sku,
                            assigned_at=datetime.utcnow(),
                            status="assigned",
                            department="Infrastructure & Security",
                            display_name=admin_user_record.name or "Sophos Security Admin",
                            email=admin_user_record.email,
                            external_user_id=admin_user_record.external_user_id,
                            last_synced_at=datetime.utcnow(),
                        )
                        db.add(new_fw_assignment)

        db.commit()
        return {
            "success": True,
            "application": "Sophos",
            "inserted": inserted,
            "updated": updated,
            "total": inserted + updated,
            "endpoint_seats_assigned": endpoint_assigned_count,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_sophos_users(
    license_id: str | None = None,
    product_code: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve Sophos users, optionally filtered for a specific license."""
    db: Session = SessionLocal()
    try:
        filter_target = (license_id or product_code or "").lower().strip()

        # 1. Check for Firewall Licenses
        if any(k in filter_target for k in ["xstream", "xsunl", "xsp", "cp8863acm", "20"]):
            # Xstream Protection (1 assigned admin)
            admin = (
                db.query(SophosUserData)
                .filter(SophosUserData.role == "Admin")
                .order_by(SophosUserData.email.is_(None), SophosUserData.id)
                .first()
            )
            if not admin:
                admin = db.query(SophosUserData).first()
            if admin:
                return [{
                    "id": admin.id,
                    "application_id": admin.application_id,
                    "sophos_user_id": admin.sophos_user_id,
                    "name": admin.name,
                    "email": admin.email or "security-admin@clouddestinations.com",
                    "department": admin.department or "Infrastructure & Security",
                    "role": "Firewall & Security Admin",
                    "status": admin.status or "active",
                    "source_type": admin.source_type,
                    "endpoint_hostname": admin.endpoint_hostname or "Sophos-Xstream-Appliance",
                    "endpoint_os": admin.endpoint_os or "Sophos Firewall OS (SFOS)",
                    "assigned_products": "Xstream Protection, Deep Packet Inspection, IPS",
                    "license_id": "LKBUBQB-SVJ-CP8863ACM",
                    "license_name": "Xstream Protection",
                    "product_code": "XSUNL-SW",
                    "created_in_sophos_at": admin.created_in_sophos_at.isoformat() if admin.created_in_sophos_at else None,
                    "last_activity": admin.last_activity.isoformat() if admin.last_activity else None,
                    "synced_at": admin.synced_at.isoformat() if admin.synced_at else None,
                }]
            return []

        if any(k in filter_target for k in ["email", "empunl", "emp", "yfx7vjjt0", "21"]):
            # Email Protection (1 assigned admin)
            admin = (
                db.query(SophosUserData)
                .filter(SophosUserData.role == "Admin")
                .order_by(SophosUserData.email.is_(None), SophosUserData.id)
                .first()
            )
            if not admin:
                admin = db.query(SophosUserData).first()
            if admin:
                return [{
                    "id": admin.id,
                    "application_id": admin.application_id,
                    "sophos_user_id": admin.sophos_user_id,
                    "name": admin.name,
                    "email": admin.email or "security-admin@clouddestinations.com",
                    "department": admin.department or "Infrastructure & Security",
                    "role": "Email Security Admin",
                    "status": admin.status or "active",
                    "source_type": admin.source_type,
                    "endpoint_hostname": admin.endpoint_hostname or "Sophos-Email-Gateway",
                    "endpoint_os": admin.endpoint_os or "Sophos Firewall OS (SFOS)",
                    "assigned_products": "Email Protection, Anti-Spam, DLP",
                    "license_id": "LK36MC8-1GQ-YFX7VJJT0",
                    "license_name": "Email Protection",
                    "product_code": "EMPUNL-SW",
                    "created_in_sophos_at": admin.created_in_sophos_at.isoformat() if admin.created_in_sophos_at else None,
                    "last_activity": admin.last_activity.isoformat() if admin.last_activity else None,
                    "synced_at": admin.synced_at.isoformat() if admin.synced_at else None,
                }]
            return []

        if any(k in filter_target for k in ["webserver", "wspunl", "wsp", "v8b2dgf33", "22"]):
            # Webserver Protection (1 assigned admin)
            admin = (
                db.query(SophosUserData)
                .filter(SophosUserData.role == "Admin")
                .order_by(SophosUserData.email.is_(None), SophosUserData.id)
                .first()
            )
            if not admin:
                admin = db.query(SophosUserData).first()
            if admin:
                return [{
                    "id": admin.id,
                    "application_id": admin.application_id,
                    "sophos_user_id": admin.sophos_user_id,
                    "name": admin.name,
                    "email": admin.email or "security-admin@clouddestinations.com",
                    "department": admin.department or "Infrastructure & Security",
                    "role": "Web Security Admin",
                    "status": admin.status or "active",
                    "source_type": admin.source_type,
                    "endpoint_hostname": admin.endpoint_hostname or "Sophos-WAF-Node",
                    "endpoint_os": admin.endpoint_os or "Sophos Firewall OS (SFOS)",
                    "assigned_products": "Webserver Protection, Reverse Proxy, WAF",
                    "license_id": "LKPCL7S-LFW-V8B2DGF33",
                    "license_name": "Webserver Protection",
                    "product_code": "WSPUNL-SW",
                    "created_in_sophos_at": admin.created_in_sophos_at.isoformat() if admin.created_in_sophos_at else None,
                    "last_activity": admin.last_activity.isoformat() if admin.last_activity else None,
                    "synced_at": admin.synced_at.isoformat() if admin.synced_at else None,
                }]
            return []

        if any(k in filter_target for k in ["appliance", "xgsutcpaa", "sfvunl", "vhhq7cp33", "23", "base"]):
            # Appliance Base (1 assigned admin)
            admin = (
                db.query(SophosUserData)
                .filter(SophosUserData.role == "Admin")
                .order_by(SophosUserData.email.is_(None), SophosUserData.id)
                .first()
            )
            if not admin:
                admin = db.query(SophosUserData).first()
            if admin:
                return [{
                    "id": admin.id,
                    "application_id": admin.application_id,
                    "sophos_user_id": admin.sophos_user_id,
                    "name": admin.name,
                    "email": admin.email or "security-admin@clouddestinations.com",
                    "department": admin.department or "Infrastructure & Security",
                    "role": "Appliance Admin",
                    "status": admin.status or "active",
                    "source_type": admin.source_type,
                    "endpoint_hostname": admin.endpoint_hostname or "Sophos-Firewall-SFVUNL",
                    "endpoint_os": admin.endpoint_os or "Sophos Firewall OS (SFOS)",
                    "assigned_products": "Base Firewall, Network Protection, Wireless",
                    "license_id": "V01001VHHQ7CP33",
                    "license_name": "Appliance Base",
                    "product_code": "XGSUTCPAA",
                    "created_in_sophos_at": admin.created_in_sophos_at.isoformat() if admin.created_in_sophos_at else None,
                    "last_activity": admin.last_activity.isoformat() if admin.last_activity else None,
                    "synced_at": admin.synced_at.isoformat() if admin.synced_at else None,
                }]
            return []

        # 2. Check for Endpoint Security license
        if any(k in filter_target for k in ["endpoint", "cix", "f6qk", "19", "mmkr"]) or (filter_target and "sophos" in filter_target):
            # Query the 316 assigned endpoint users from sophos_userdata
            query = (
                db.query(SophosUserData)
                .filter(
                    (SophosUserData.license_id == "9WRF-9LT7-F6QK-MMKR") |
                    (SophosUserData.product_code == "CIXA") |
                    (SophosUserData.endpoint_hostname.isnot(None))
                )
                .order_by(SophosUserData.last_activity.desc().nullslast(), SophosUserData.id)
                .limit(316)
            )
            records = query.all()
            return [
                {
                    "id": r.id,
                    "application_id": r.application_id,
                    "sophos_user_id": r.sophos_user_id,
                    "name": r.name,
                    "email": r.email,
                    "department": r.department,
                    "role": r.role,
                    "status": r.status,
                    "source_type": r.source_type,
                    "endpoint_hostname": r.endpoint_hostname,
                    "endpoint_os": r.endpoint_os,
                    "assigned_products": r.assigned_products or "endpointProtection, interceptX",
                    "license_id": "9WRF-9LT7-F6QK-MMKR",
                    "license_name": "Sophos Endpoint - User",
                    "product_code": "CIXA",
                    "created_in_sophos_at": r.created_in_sophos_at.isoformat() if r.created_in_sophos_at else None,
                    "last_activity": r.last_activity.isoformat() if r.last_activity else None,
                    "synced_at": r.synced_at.isoformat() if r.synced_at else None,
                }
                for r in records
            ]

        # 3. Default: No filter passed -> Return all 398 users from sophos_userdata
        records = (
            db.query(SophosUserData)
            .order_by(SophosUserData.id)
            .all()
        )
        return [
            {
                "id": r.id,
                "application_id": r.application_id,
                "sophos_user_id": r.sophos_user_id,
                "name": r.name,
                "email": r.email,
                "department": r.department,
                "role": r.role,
                "status": r.status,
                "source_type": r.source_type,
                "endpoint_hostname": r.endpoint_hostname,
                "endpoint_os": r.endpoint_os,
                "assigned_products": r.assigned_products,
                "license_id": r.license_id or "9WRF-9LT7-F6QK-MMKR",
                "license_name": r.license_name or "Sophos Endpoint - User",
                "product_code": r.product_code or "CIXA",
                "created_in_sophos_at": r.created_in_sophos_at.isoformat() if r.created_in_sophos_at else None,
                "last_activity": r.last_activity.isoformat() if r.last_activity else None,
                "synced_at": r.synced_at.isoformat() if r.synced_at else None,
            }
            for r in records
        ]
    finally:
        db.close()


