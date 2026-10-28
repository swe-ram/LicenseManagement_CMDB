from sqlalchemy import inspect, text

from database.database import engine, Base
from database import models


print("Creating database tables...")

Base.metadata.create_all(bind=engine)

inspector = inspect(engine)
if inspector.has_table("license_assigned_users"):
    existing_columns = {col["name"] for col in inspector.get_columns("license_assigned_users")}
    with engine.begin() as connection:
        if "department" not in existing_columns:
            print("Adding 'department' column to license_assigned_users...")
            connection.execute(
                text("ALTER TABLE license_assigned_users ADD COLUMN IF NOT EXISTS department VARCHAR(255)")
            )

    unique_constraints = inspector.get_unique_constraints("license_assigned_users")
    has_license_user_unique = any(
        set(constraint.get("column_names") or [])
        == {"license_id", "user_id"}
        for constraint in unique_constraints
    )
    if not has_license_user_unique:
        with engine.begin() as connection:
            duplicates = connection.execute(
                text(
                    """
                    SELECT license_id, user_id
                    FROM license_assigned_users
                    GROUP BY license_id, user_id
                    HAVING COUNT(*) > 1
                    LIMIT 1
                    """
                )
            ).first()
            if duplicates:
                raise RuntimeError(
                    "Cannot enforce license_id + user_id uniqueness: "
                    "duplicate assigned-user relationships already exist."
                )
            connection.execute(
                text(
                    "ALTER TABLE license_assigned_users "
                    "DROP CONSTRAINT IF EXISTS "
                    "uq_license_assigned_users_app_license_user"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE license_assigned_users "
                    "ADD CONSTRAINT uq_license_assigned_users_license_user "
                    "UNIQUE (license_id, user_id)"
                )
            )

if inspector.has_table("users"):
    user_columns = {col["name"] for col in inspector.get_columns("users")}
    if "department" not in user_columns:
        with engine.begin() as connection:
            print("Adding 'department' column to users...")
            connection.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(255)")
            )

print("Database tables created successfully!")