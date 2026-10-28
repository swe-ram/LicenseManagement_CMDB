"""Seed + migrate approval-chain tables (portal_users, portal_sessions,
license_approvals stage/approver_email). Idempotent."""
import sys
from pathlib import Path

from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.database import engine

with engine.begin() as c:
    insp = inspect(engine)
    if not insp.has_table("portal_users"):
        c.execute(text(
            "CREATE TABLE portal_users (id SERIAL PRIMARY KEY, email VARCHAR(255) NOT NULL, "
            "name VARCHAR(255) NOT NULL DEFAULT '', password_hash VARCHAR(255) NOT NULL, "
            "role VARCHAR(50) NOT NULL DEFAULT 'employee', active BOOLEAN NOT NULL DEFAULT TRUE, "
            "created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW())"
        ))
        c.execute(text("CREATE UNIQUE INDEX ix_portal_users_email ON portal_users (email)"))
        print("portal_users created.")
    if not insp.has_table("portal_sessions"):
        c.execute(text(
            "CREATE TABLE portal_sessions (id SERIAL PRIMARY KEY, jti VARCHAR(64) NOT NULL, "
            "portal_user_id INTEGER NOT NULL REFERENCES portal_users(id), "
            "created_at TIMESTAMP DEFAULT NOW(), expires_at TIMESTAMP NOT NULL, revoked_at TIMESTAMP)"
        ))
        c.execute(text("CREATE UNIQUE INDEX ix_portal_sessions_jti ON portal_sessions (jti)"))
        print("portal_sessions created.")
    insp2 = inspect(engine)
    la_cols = {col["name"] for col in insp2.get_columns("license_approvals")}
    if "stage" not in la_cols:
        c.execute(text("ALTER TABLE license_approvals ADD COLUMN stage VARCHAR(64) NOT NULL DEFAULT 'tower_head'"))
        print("license_approvals.stage added.")
    if "approver_email" not in la_cols:
        c.execute(text("ALTER TABLE license_approvals ADD COLUMN approver_email VARCHAR(255)"))
        print("license_approvals.approver_email added.")
    # approver_id nullable for assignee/final stages (no department_approvers row)
    c.execute(text("ALTER TABLE license_approvals ALTER COLUMN approver_id DROP NOT NULL"))
    # Backfill: existing pending rows become tower_head stage
    c.execute(text("UPDATE license_approvals SET stage='tower_head' WHERE stage IS NULL OR stage=''"))
    # Ensure default tower head approver mapping exists per department
    c.execute(text(
        "INSERT INTO department_approvers (department_id, employee_id, approver_name, approver_email, active, created_at, updated_at) "
        "SELECT d.id, u.id, COALESCE(u.name, u.email), u.email, TRUE, NOW(), NOW() "
        "FROM departments d CROSS JOIN (SELECT id, name, email FROM users WHERE LOWER(email)='akshayap@clouddestinations.com' ORDER BY id LIMIT 1) u "
        "WHERE d.active IS NOT FALSE AND NOT EXISTS "
        "(SELECT 1 FROM department_approvers da WHERE da.department_id=d.id AND da.active IS TRUE)"
    ))
print("Approval-chain migration completed.")
