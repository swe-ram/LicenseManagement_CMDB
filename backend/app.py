
import asyncio
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from services.microsoft365.microsoft365_sync import (
    sync_microsoft365_inventory,
)

load_dotenv()


# ============================================================
# MICROSOFT 365 AUTOMATIC SYNC
# ============================================================

async def run_microsoft365_sync():
    """
    Automatically synchronize Microsoft 365 data to PostgreSQL
    when FastAPI starts.
    """

    try:
        from services.microsoft365.microsoft365_sync import (
            sync_microsoft365_inventory,
        )

        print()
        print("=" * 70)
        print("MICROSOFT 365 AUTOMATIC SYNC STARTED")
        print("=" * 70)

        result = await asyncio.to_thread(
            sync_microsoft365_inventory
        )

        print("=" * 70)
        print("MICROSOFT 365 AUTOMATIC SYNC COMPLETED")
        print("=" * 70)

        if isinstance(result, dict):
            print(
                f"Licenses processed: "
                f"{result.get('licenses_processed', 0)}"
            )

            print(
                f"Users processed: "
                f"{result.get('users_processed', 0)}"
            )

            print(
                f"Assignments processed: "
                f"{result.get('assignments_processed', 0)}"
            )

            print(
                f"Sync status: "
                f"{result.get('sync_status', 'completed')}"
            )

        print()

    except Exception as exc:

        print()
        print("=" * 70)
        print("MICROSOFT 365 AUTOMATIC SYNC FAILED")
        print("=" * 70)
        print(f"Error: {exc}")
        print("=" * 70)
        print()


# ============================================================
# SLACK AUTOMATIC SYNC
# ============================================================

async def run_slack_sync():
    """
    Automatically synchronize Slack data to PostgreSQL
    when FastAPI starts.
    """

    try:
        from config.settings import get_settings

        from services.slack_client import SlackClient
        from services.slack_license import get_license_data
        from services.slack_usage import get_usage_summary
        from services.slack_users import list_slack_users

        settings = get_settings()

        client = SlackClient(
            bot_token=settings.SLACK_BOT_TOKEN,
            user_token=settings.SLACK_USER_TOKEN,
            admin_token=settings.SLACK_ADMIN_TOKEN,
        )

        print()
        print("=" * 70)
        print("SLACK AUTOMATIC SYNC STARTED")
        print("=" * 70)

        # ----------------------------------------------------
        # 1. Slack Users
        # ----------------------------------------------------

        print("Syncing Slack users...")

        users_result = await asyncio.to_thread(
            list_slack_users,
            client,
        )

        if isinstance(users_result, dict):

            print(
                f"Slack users processed: "
                f"{users_result.get('total_users', 0)}"
            )

            database_result = users_result.get(
                "database",
                {},
            )

            if isinstance(database_result, dict):
                print(
                    "Slack users database status: "
                    f"{database_result.get('success')}"
                )

        # ----------------------------------------------------
        # 2. Slack License
        # ----------------------------------------------------

        print("Syncing Slack license information...")

        license_result = await asyncio.to_thread(
            get_license_data,
            client,
        )

        if isinstance(license_result, dict):

            print(
                "Slack license data available: "
                f"{license_result.get('data_available')}"
            )

            database_result = license_result.get(
                "database",
                {},
            )

            if isinstance(database_result, dict):
                print(
                    "Slack license database status: "
                    f"{database_result.get('success')}"
                )

        # ----------------------------------------------------
        # 3. Slack Usage
        # ----------------------------------------------------

        print("Syncing Slack usage information...")

        usage_result = await asyncio.to_thread(
            get_usage_summary,
            client,
        )

        if isinstance(usage_result, dict):

            print(
                "Slack usage synchronization completed."
            )

        print("=" * 70)
        print("SLACK AUTOMATIC SYNC COMPLETED")
        print("=" * 70)
        print()

    except Exception as exc:

        print()
        print("=" * 70)
        print("SLACK AUTOMATIC SYNC FAILED")
        print("=" * 70)
        print(f"Error: {exc}")
        print("=" * 70)
        print()


# ============================================================
# SOPHOS AUTOMATIC SYNC
# ============================================================

async def run_sophos_sync():
    """
    Automatically synchronize Sophos data to PostgreSQL
    when FastAPI starts.
    """
    try:
        from services.sophos.sophos_sync import sync_sophos_inventory

        print()
        print("=" * 70)
        print("SOPHOS AUTOMATIC SYNC STARTED")
        print("=" * 70)

        result = await asyncio.to_thread(sync_sophos_inventory)

        print("=" * 70)
        print("SOPHOS AUTOMATIC SYNC COMPLETED")
        print("=" * 70)
        if isinstance(result, dict):
            print(f"Licenses processed: {result.get('licenses_processed', 0)}")
            print(f"Sync status: {result.get('sync_status', 'completed')}")
        print()

    except Exception as exc:
        print()
        print("=" * 70)
        print("SOPHOS AUTOMATIC SYNC FAILED")
        print("=" * 70)
        print(f"Error: {exc}")
        print("=" * 70)
        print()


# ============================================================
# FASTAPI LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print()
    print("=" * 70)
    print("LICENSE MANAGEMENT API STARTING")
    print("=" * 70)

    # --------------------------------------------------------
    # Start synchronization tasks
    # --------------------------------------------------------

    microsoft365_task = asyncio.create_task(
        run_microsoft365_sync()
    )

    slack_task = asyncio.create_task(
        run_slack_sync()
    )

    sophos_task = asyncio.create_task(
        run_sophos_sync()
    )

    print("Microsoft 365 automatic sync started.")
    print("Slack automatic sync started.")
    print("Sophos automatic sync started.")
    print("FastAPI is ready.")
    print("=" * 70)
    print()

    yield

    # --------------------------------------------------------
    # SHUTDOWN
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("LICENSE MANAGEMENT API SHUTTING DOWN")
    print("=" * 70)

    for task in (
        microsoft365_task,
        slack_task,
        sophos_task,
    ):
        if not task.done():
            task.cancel()

    print("Background synchronization tasks stopped.")
    print()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="License Management API",
    version="1.0.0",
    description=(
        "Centralized license inventory and usage collection "
        "for enterprise license management."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
)
async def health() -> dict[str, str]:

    return {
        "status": "healthy",
        "service": "License Management API",
    }


# ============================================================
# ROUTERS
# ============================================================

from routers.microsoft365 import (
    router as microsoft365_router,
)

from routers.slack import (
    router as slack_router,
)
from routers.license_requests import (
    legacy_router as legacy_license_requests_router,
    router as license_requests_router,
)
from routers.public_approvals import (
    legacy_router as legacy_public_approvals_router,
    router as public_approvals_router,
)
from auth.session import router as authentication_router
from routers.sophos import router as sophos_router


app.include_router(authentication_router)
app.include_router(slack_router)

app.include_router(microsoft365_router)
app.include_router(sophos_router)
app.include_router(license_requests_router)
app.include_router(legacy_license_requests_router)
app.include_router(public_approvals_router)
app.include_router(legacy_public_approvals_router)


# ============================================================
# UNIFIED LICENSE USERS ENDPOINT
# ============================================================

@app.get(
    "/licenses/{license_id}/users",
    tags=["Licenses"],
    summary="Get users assigned to a license from DB",
)
async def get_license_users_direct(license_id: str):
    from database.microsoft365_assigned_users_repository import (
        get_assigned_users_by_license,
    )
    from database.database import SessionLocal
    from database.models import User, Application

    # Check Microsoft assigned users in DB
    ms_users = get_assigned_users_by_license(license_id)
    if ms_users:
        return {
            "application": "Microsoft 365",
            "license_id": license_id,
            "total_users": len(ms_users),
            "users": ms_users,
        }

    # If Slack license requested
    if "slack" in license_id.lower() or license_id in ["1", "2", "7"]:
        db = SessionLocal()
        try:
            slack_app = db.query(Application).filter(Application.name == "Slack").first()
            if slack_app:
                slack_users = db.query(User).filter(User.application_id == slack_app.id).all()
                users_list = [
                    {
                        "user_id": u.id,
                        "name": u.name or "Slack User",
                        "email": u.email,
                        "role": u.role or "Member",
                        "status": u.status or "active",
                        "department": "Engineering & Operations",
                        "application_name": "Slack",
                        "license_id": license_id,
                        "license_name": "Slack Pro",
                        "assigned_date": "2024-01-25",
                    }
                    for u in slack_users
                ]
                return {
                    "application": "Slack",
                    "license_id": license_id,
                    "total_users": len(users_list),
                    "users": users_list,
                }
        finally:
            db.close()

    # If Sophos license requested
    if (
        "sophos" in license_id.lower()
        or any(k in license_id.lower() for k in ["cix", "xg", "xstream", "email", "webserver", "appliance", "xsp", "emp", "wsp"])
        or license_id in ["19", "20", "21", "22", "23", "9WRF-9LT7-F6QK-MMKR", "LKBUBQB-SVJ-CP8863ACM", "LK36MC8-1GQ-YFX7VJJT0", "LKPCL7S-LFW-V8B2DGF33", "V01001VHHQ7CP33"]
    ):
        from database.sophos_repository import get_sophos_users
        sophos_users = get_sophos_users(license_id=license_id)
        if sophos_users:
            users_list = [
                {
                    "user_id": u["id"],
                    "name": u["name"] or "Sophos User",
                    "email": u["email"],
                    "role": u["role"] or "User",
                    "status": u["status"] or "active",
                    "department": u["department"] or "Information Technology",
                    "application_name": "Sophos",
                    "license_id": license_id,
                    "license_name": u.get("license_name") or u.get("assigned_products") or "Sophos License",
                    "assigned_date": u.get("created_in_sophos_at") or "2024-01-01",
                    "endpoint_hostname": u.get("endpoint_hostname"),
                    "endpoint_os": u.get("endpoint_os"),
                }
                for u in sophos_users
            ]
            return {
                "application": "Sophos",
                "license_id": license_id,
                "total_users": len(users_list),
                "users": users_list,
            }

    # Check if license in database belongs to Sophos
    db = SessionLocal()
    try:
        from database.models import License
        lic_record = None
        if license_id.isdigit():
            lic_record = db.query(License).filter(License.id == int(license_id)).first()
        if not lic_record:
            lic_record = db.query(License).filter(License.product.ilike(f"%{license_id}%")).first()
        if lic_record:
            app_rec = db.query(Application).filter(Application.id == lic_record.application_id).first()
            if app_rec and "sophos" in app_rec.name.lower():
                from database.sophos_repository import get_sophos_users
                sophos_users = get_sophos_users(license_id=lic_record.product or license_id)
                users_list = [
                    {
                        "user_id": u["id"],
                        "name": u["name"] or "Sophos User",
                        "email": u["email"],
                        "role": u["role"] or "User",
                        "status": u["status"] or "active",
                        "department": u["department"] or "Information Technology",
                        "application_name": "Sophos",
                        "license_id": license_id,
                        "license_name": lic_record.product or u.get("license_name"),
                        "assigned_date": u.get("created_in_sophos_at") or "2024-01-01",
                        "endpoint_hostname": u.get("endpoint_hostname"),
                        "endpoint_os": u.get("endpoint_os"),
                    }
                    for u in sophos_users
                ]
                return {
                    "application": "Sophos",
                    "license_id": license_id,
                    "total_users": len(users_list),
                    "users": users_list,
                }
    finally:
        db.close()

    return {
        "license_id": license_id,
        "total_users": 0,
        "users": [],
    }


# ============================================================
# RUN APPLICATION DIRECTLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
