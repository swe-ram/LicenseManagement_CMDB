"""One-time repair: reconcile legacy live DB with models.

Legacy problems (Oct 2026):
  1. users lacks department_id/job_title/last_activity -> M365 sync crash.
  2. license_requests is OLD tower-head shape -> migration 001 fails.
This script: adds users cols, seeds departments, backs up legacy requests,
recreates portal-shape license_requests. Idempotent.
"""
import sys
from pathlib import Path

from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.database import engine

STANDARD_DEPARTMENTS = [
    "Engineering & Operations",
    "Information Technology",
    "Human Resources",
    "Finance",
    "Sales & Marketing",
    "Customer Support",
    "Legal & Compliance",
    "Administration",
]

with engine.begin() as c:
    insp = inspect(engine)
    def cols(t):
        return {col["name"] for col in insp.get_columns(t)} if insp.has_table(t) else set()

    ucols = cols("users")
    if "department_id" not in ucols:
        print("users: adding department_id...")
        c.execute(text("ALTER TABLE users ADD COLUMN department_id INTEGER"))
    if "job_title" not in ucols:
        print("users: adding job_title...")
        c.execute(text("ALTER TABLE users ADD COLUMN job_title VARCHAR(255)"))
    if "last_activity" not in ucols:
        print("users: adding last_activity...")
        c.execute(text("ALTER TABLE users ADD COLUMN last_activity TIMESTAMP"))

    for name in STANDARD_DEPARTMENTS:
        c.execute(
            text("INSERT INTO departments (name, active) SELECT :n, TRUE "
                 "WHERE NOT EXISTS (SELECT 1 FROM departments WHERE LOWER(name)=LOWER(:n))"),
            {"n": name},
        )
    print("departments seeded.")
    c.execute(text(
        "UPDATE users SET department_id = d.id FROM departments d "
        "WHERE users.department_id IS NULL AND users.department IS NOT NULL "
        "AND users.department <> '' AND LOWER(d.name) = LOWER(users.department)"
    ))
    c.execute(text(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_users_department_id') THEN "
        "ALTER TABLE users ADD CONSTRAINT fk_users_department_id "
        "FOREIGN KEY (department_id) REFERENCES departments(id); END IF; END $$"
    ))

    lr_cols = cols("license_requests")
    if "request_number" not in lr_cols:
        print("license_requests: legacy table - backing up...")
        c.execute(text("DROP TABLE IF EXISTS license_requests_legacy_backup"))
        c.execute(text("CREATE TABLE license_requests_legacy_backup AS SELECT * FROM license_requests"))
        n = c.execute(text("SELECT COUNT(*) FROM license_requests_legacy_backup")).scalar()
        print(f"  backed up {n} legacy rows.")
        # license_approvals.request_id FK blocks DROP; back it up as well
        c.execute(text("DROP TABLE IF EXISTS license_approvals_legacy_backup"))
        c.execute(text("CREATE TABLE license_approvals_legacy_backup AS SELECT * FROM license_approvals"))
        m = c.execute(text("SELECT COUNT(*) FROM license_approvals_legacy_backup")).scalar()
        print(f"  backed up {m} legacy approval rows.")
        c.execute(text("DROP TABLE license_requests CASCADE"))
        c.execute(text(
            "CREATE TABLE license_requests ("
            "id SERIAL PRIMARY KEY,"
            "request_number VARCHAR(64) NOT NULL,"
            "idempotency_key VARCHAR(64),"
            "employee_id INTEGER NOT NULL REFERENCES users(id),"
            "department_id INTEGER NOT NULL REFERENCES departments(id),"
            "license_id INTEGER NOT NULL REFERENCES licenses(id),"
            "approver_id INTEGER REFERENCES department_approvers(id),"
            "business_justification TEXT NOT NULL,"
            "urgency VARCHAR(64) NOT NULL DEFAULT 'Standard',"
            "status VARCHAR(30) DEFAULT 'Pending Approval',"
            "submission_timestamp TIMESTAMP DEFAULT NOW(),"
            "provisioning_status VARCHAR(50),"
            "failure_details TEXT,"
            "created_at TIMESTAMP DEFAULT NOW(),"
            "updated_at TIMESTAMP DEFAULT NOW(),"
            "requested_duration VARCHAR(50),"
            "requester_identity VARCHAR(255))"
        ))
        c.execute(text("CREATE UNIQUE INDEX ix_license_requests_request_number ON license_requests (request_number)"))
        c.execute(text("CREATE UNIQUE INDEX uq_license_requests_employee_idempotency "
                       "ON license_requests (employee_id, idempotency_key) WHERE idempotency_key IS NOT NULL"))
        print("license_requests: recreated portal shape.")
        # recreate fresh portal-shape license_approvals (legacy rows kept in backup)
        c.execute(text("DROP TABLE IF EXISTS license_approvals CASCADE"))
        c.execute(text(
            "CREATE TABLE license_approvals ("
            "id SERIAL PRIMARY KEY,"
            "request_id INTEGER NOT NULL REFERENCES license_requests(id),"
            "approver_id INTEGER NOT NULL REFERENCES department_approvers(id),"
            "decision VARCHAR(20) NOT NULL DEFAULT 'Pending',"
            "comments TEXT,"
            "decision_timestamp TIMESTAMP,"
            "created_at TIMESTAMP DEFAULT NOW(),"
            "updated_at TIMESTAMP)"
        ))
        print("license_approvals: recreated portal shape.")
    else:
        print("license_requests: portal-shaped, ensuring columns...")
        for ddl in [
            "ALTER TABLE license_requests ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(64)",
            "ALTER TABLE license_requests ADD COLUMN IF NOT EXISTS urgency VARCHAR(64) NOT NULL DEFAULT 'Standard'",
            "ALTER TABLE license_requests ADD COLUMN IF NOT EXISTS requester_identity VARCHAR(255)",
            "ALTER TABLE license_requests ADD COLUMN IF NOT EXISTS approver_id INTEGER",
        ]:
            c.execute(text(ddl))

    for ddl in [
        "ALTER TABLE license_approvals ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
        "ALTER TABLE license_approvals ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
    ]:
        c.execute(text(ddl))

print("Schema repair completed successfully!")
