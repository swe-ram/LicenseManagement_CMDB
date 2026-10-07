from datetime import datetime

from sqlalchemy.orm import Session

from database.models import Application, User, License, SlackData


# =========================================================
# SAVE SLACK USERS
# =========================================================

def save_slack_users(users: list[dict]) -> dict:
    from database.database import SessionLocal

    db: Session = SessionLocal()

    try:

        application = (
            db.query(Application)
            .filter(Application.name == "Slack")
            .first()
        )

        if not application:

            application = Application(
                name="Slack",
                vendor="Slack",
                category="Collaboration",
                status="Active",
                last_sync=datetime.utcnow(),
            )

            db.add(application)
            db.flush()

        else:

            application.last_sync = datetime.utcnow()

        inserted = 0
        updated = 0

        for slack_user in users:

            slack_user_id = slack_user.get(
                "slack_user_id"
            )

            if not slack_user_id:
                continue

            existing_user = (
                db.query(User)
                .filter(
                    User.application_id == application.id,
                    User.external_user_id == slack_user_id,
                )
                .first()
            )

            role = (
                "Owner"
                if slack_user.get("is_owner")
                else "Admin"
                if slack_user.get("is_admin")
                else None
            )

            name = (
                slack_user.get("real_name")
                or slack_user.get("display_name")
                or slack_user.get("name")
            )

            if existing_user:

                existing_user.name = name
                existing_user.email = slack_user.get("email")
                existing_user.status = slack_user.get("status")
                existing_user.role = role

                updated += 1

            else:

                new_user = User(
                    application_id=application.id,
                    external_user_id=slack_user_id,
                    name=name,
                    email=slack_user.get("email"),
                    status=slack_user.get("status"),
                    role=role,
                )

                db.add(new_user)

                inserted += 1

        db.commit()

        return {
            "success": True,
            "application": "Slack",
            "inserted": inserted,
            "updated": updated,
            "total": inserted + updated,
        }

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# =========================================================
# SAVE SLACK LICENSE
# =========================================================

def save_slack_data(
    license_data: dict,
    application: Application | None = None,
) -> dict:
    from database.database import SessionLocal

    db: Session = SessionLocal()
    try:
        application_record = application or (
            db.query(Application)
            .filter(Application.name == "Slack")
            .first()
        )

        if application_record is None:
            application_record = Application(
                name="Slack",
                vendor="Slack",
                category="Collaboration",
                status="Active",
                last_sync=datetime.utcnow(),
            )
            db.add(application_record)
            db.flush()

        plan = license_data.get("plan") or "Slack"
        license_type = license_data.get("license_type") or "billable_users"

        existing_record = (
            db.query(SlackData)
            .filter(
                SlackData.application_id == application_record.id,
                SlackData.plan == plan,
                SlackData.license_type == license_type,
            )
            .first()
        )

        if existing_record is not None:
            existing_record.plan = plan
            existing_record.license_type = license_type
            existing_record.purchased_quantity = license_data.get("purchased_quantity")
            existing_record.entitled_quantity = license_data.get("entitled_quantity")
            existing_record.assigned_quantity = license_data.get("assigned_quantity")
            existing_record.available_quantity = license_data.get("available_quantity")
            existing_record.active_users = license_data.get("active_users")
            existing_record.inactive_users = license_data.get("inactive_users")
            existing_record.renewal_date = license_data.get("renewal_date")
            existing_record.cost = license_data.get("cost")
            existing_record.currency = license_data.get("currency")
            existing_record.billing_cycle = license_data.get("billing_cycle")
            existing_record.data_source = license_data.get("data_source") or "Slack API"
            existing_record.synced_at = datetime.utcnow()
            existing_record.updated_at = datetime.utcnow()
            action = "updated"
        else:
            new_record = SlackData(
                application_id=application_record.id,
                plan=plan,
                license_type=license_type,
                purchased_quantity=license_data.get("purchased_quantity"),
                entitled_quantity=license_data.get("entitled_quantity"),
                assigned_quantity=license_data.get("assigned_quantity"),
                available_quantity=license_data.get("available_quantity"),
                active_users=license_data.get("active_users"),
                inactive_users=license_data.get("inactive_users"),
                renewal_date=license_data.get("renewal_date"),
                cost=license_data.get("cost"),
                currency=license_data.get("currency"),
                billing_cycle=license_data.get("billing_cycle"),
                data_source=license_data.get("data_source") or "Slack API",
                synced_at=datetime.utcnow(),
            )
            db.add(new_record)
            action = "inserted"

        db.commit()
        return {
            "success": True,
            "application": "Slack",
            "action": action,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save_slack_license(
    license_data: dict,
) -> dict:

    from database.database import SessionLocal

    db: Session = SessionLocal()

    try:

        # -------------------------------------------------
        # Get or create Slack application
        # -------------------------------------------------

        application = (
            db.query(Application)
            .filter(Application.name == "Slack")
            .first()
        )

        if not application:

            application = Application(
                name="Slack",
                vendor="Slack",
                category="Collaboration",
                status="Active",
                last_sync=datetime.utcnow(),
            )

            db.add(application)
            db.flush()

        else:

            application.last_sync = datetime.utcnow()

        # -------------------------------------------------
        # License information
        # -------------------------------------------------

        plan = license_data.get("plan")
        if plan and isinstance(plan, str):
            import re
            plan = re.sub(r"\s*\([Tt]he\s*zastudios\)", "", plan, flags=re.IGNORECASE)
            plan = re.sub(r"the\s*zastudios|zastudios", "", plan, flags=re.IGNORECASE).strip() or "Slack Pro"

        product = plan or "Slack"

        license_type = (
            license_data.get("license_type")
            or "billable_users"
        )

        purchased_quantity = (
            license_data.get("purchased_quantity")
        )

        assigned_quantity = (
            license_data.get("assigned_quantity")
        )

        available_quantity = (
            license_data.get("available_quantity")
        )

        used_quantity = (
            license_data.get("active_users")
        )

        cost = license_data.get("cost")
        currency = license_data.get("currency")
        billing_cycle = license_data.get("billing_cycle")
        renewal_date = license_data.get("renewal_date")

        # -------------------------------------------------
        # Check existing license
        # -------------------------------------------------

        existing_license = (
            db.query(License)
            .filter(
                License.application_id == application.id,
                License.license_type == license_type,
            )
            .first()
        )

        if existing_license:

            existing_license.product = product

            existing_license.purchased_qty = (
                purchased_quantity
            )

            existing_license.assigned_qty = (
                assigned_quantity
            )

            existing_license.available_qty = (
                available_quantity
            )

            existing_license.used_qty = (
                used_quantity
            )

            existing_license.cost = cost
            existing_license.currency = currency
            existing_license.billing_cycle = billing_cycle
            existing_license.renewal_date = renewal_date

            existing_license.data_source = (
                license_data.get("data_source")
                or "Slack API"
            )

            existing_license.last_updated = (
                datetime.utcnow()
            )

            action = "updated"
            license_id = existing_license.id

        else:

            new_license = License(

                application_id=application.id,

                product=product,

                license_type=license_type,

                purchased_qty=purchased_quantity,

                assigned_qty=assigned_quantity,

                available_qty=available_quantity,

                used_qty=used_quantity,

                cost=cost,

                currency=currency,

                billing_cycle=billing_cycle,

                renewal_date=renewal_date,

                data_source=(
                    license_data.get("data_source")
                    or "Slack API"
                ),

                last_updated=datetime.utcnow(),
            )

            db.add(new_license)

            db.flush()

            action = "inserted"

            license_id = new_license.id

        db.commit()

        save_slack_data(license_data, application=application)

        return {
            "success": True,
            "application": "Slack",
            "action": action,
            "license_id": license_id,
            "assigned_quantity": assigned_quantity,
            "active_users": license_data.get(
                "active_users"
            ),
            "inactive_users": license_data.get(
                "inactive_users"
            ),
        }

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()