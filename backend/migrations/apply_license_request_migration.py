import sys
from pathlib import Path

from sqlalchemy import inspect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.database import engine


def main() -> None:
    if engine.dialect.name != "postgresql":
        raise RuntimeError("The license request migration requires PostgreSQL.")

    required_tables = {
        "users",
        "departments",
        "applications",
        "licenses",
        "license_requests",
        "license_approvals",
        "department_approvers",
    }
    missing_tables = required_tables - set(inspect(engine).get_table_names())
    if missing_tables:
        raise RuntimeError(
            "The migration expects the existing portal schema; missing tables: "
            + ", ".join(sorted(missing_tables))
        )

    migration = Path(__file__).with_name("001_license_request_approval.sql").read_text(
        encoding="utf-8"
    )
    with engine.begin() as connection:
        connection.exec_driver_sql(migration)
    print(
        "Existing license-request schema extended with additive columns and a "
        "nullable approver link; no tables or records were replaced."
    )


if __name__ == "__main__":
    main()
