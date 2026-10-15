import os
import unittest
import uuid
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import app
from auth.session import AuthenticatedPrincipal, get_current_principal
from database.database import Base, get_db
from database.models import (
    Application,
    Department,
    DepartmentApprover,
    License,
    LicenseApproval,
    LicenseRequest,
    User,
)


class LicenseRequestApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, autoflush=False)
        self.db = self.Session()

        department = Department(name="Software Engineering", active=True)
        application = Application(name="Microsoft 365", status="Active")
        self.db.add_all([department, application])
        self.db.flush()

        self.employee = User(
            external_user_id="employee-oid",
            name="Test Employee",
            email="employee@example.test",
            status="active",
            department_id=department.id,
        )
        self.approver = User(
            external_user_id="approver-oid",
            name="Test Approver",
            email="approver@example.test",
            status="active",
            department_id=department.id,
        )
        self.outsider = User(
            external_user_id="outsider-oid",
            name="Other Employee",
            email="other@example.test",
            status="active",
            department_id=department.id,
        )
        self.db.add_all([self.employee, self.approver, self.outsider])
        self.db.flush()

        self.license = License(
            application_id=application.id,
            product="Microsoft 365 Business Premium",
            license_type="Business Suite",
            available_qty=10,
        )
        self.db.add(self.license)
        self.db.add(
            DepartmentApprover(
                department_id=department.id,
                employee_id=self.approver.id,
                approver_name=self.approver.name,
                approver_email=self.approver.email,
                active=True,
            )
        )
        self.db.commit()

        self.principal = AuthenticatedPrincipal(
            object_id=self.employee.external_user_id,
            roles=frozenset({"License.Requester"}),
            claims={},
        )
        app.dependency_overrides[get_db] = self._get_db
        app.dependency_overrides[get_current_principal] = lambda: self.principal
        self.client = TestClient(app, client=("127.0.0.1", 50000))

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def _get_db(self):
        yield self.db

    def _payload(self, **overrides):
        payload = {
            "user_id": self.employee.id,
            "idempotency_key": str(uuid.uuid4()),
            "department": "Software Engineering",
            "application_name": "Microsoft 365",
            "license_id": self.license.id,
            "business_justification": "Required for assigned project work.",
            "urgency": "Standard",
        }
        payload.update(overrides)
        return payload

    def test_create_is_persisted_and_idempotent(self):
        payload = self._payload()
        first = self.client.post("/api/v1/license-requests", json=payload)
        retry = self.client.post("/api/v1/license-requests", json=payload)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(retry.status_code, 201)
        self.assertEqual(first.json()["request_id"], retry.json()["request_id"])
        self.assertTrue(first.json()["request_id"].startswith("LIC-"))
        self.assertEqual(first.json()["status"], "Pending Approval")
        self.assertEqual(self.db.query(LicenseRequest).count(), 1)
        self.assertEqual(self.db.query(LicenseApproval).count(), 1)

        another = self.client.post(
            "/api/v1/license-requests",
            json=self._payload(),
        )
        self.assertEqual(another.status_code, 201)
        self.assertNotEqual(first.json()["request_id"], another.json()["request_id"])

    def test_rejects_client_selected_other_employee(self):
        response = self.client.post(
            "/api/v1/license-requests",
            json=self._payload(user_id=self.outsider.id),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.db.query(LicenseRequest).count(), 0)

    def test_employee_cannot_read_another_employees_request(self):
        response = self.client.post(
            "/api/v1/license-requests",
            json=self._payload(),
        )
        request_id = response.json()["request_id"]
        self.principal = AuthenticatedPrincipal(
            object_id=self.outsider.external_user_id,
            roles=frozenset({"License.Requester"}),
            claims={},
        )
        detail = self.client.get(f"/api/v1/license-requests/{request_id}")
        self.assertEqual(detail.status_code, 403)

    def test_only_assigned_approver_can_decide(self):
        response = self.client.post(
            "/api/v1/license-requests",
            json=self._payload(),
        )
        request_id = response.json()["request_id"]

        self.principal = AuthenticatedPrincipal(
            object_id=self.outsider.external_user_id,
            roles=frozenset({"License.Approver"}),
            claims={},
        )
        unauthorized = self.client.post(
            f"/api/v1/license-requests/{request_id}/decision",
            json={"decision": "Approved"},
        )
        self.assertEqual(unauthorized.status_code, 403)

        self.principal = AuthenticatedPrincipal(
            object_id=self.approver.external_user_id,
            roles=frozenset({"License.Approver"}),
            claims={},
        )
        approved = self.client.post(
            f"/api/v1/license-requests/{request_id}/decision",
            json={"decision": "Approved", "comments": "Approved for current project."},
        )
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.json()["status"], "Approved")
        self.assertEqual(approved.json()["approvals"][0]["decision"], "Approved")
        self.assertEqual(
            self.db.query(LicenseRequest).one().status,
            "Approved",
        )

    def test_department_mismatch_and_license_application_mismatch_are_rejected(self):
        wrong_department = self.client.post(
            "/api/v1/license-requests",
            json=self._payload(department="Finance"),
        )
        wrong_license = self.client.post(
            "/api/v1/license-requests",
            json=self._payload(license_id=999),
        )
        self.assertEqual(wrong_department.status_code, 422)
        self.assertEqual(wrong_license.status_code, 422)
        self.assertEqual(self.db.query(LicenseRequest).count(), 0)

    def test_shared_account_local_test_mode_can_create_and_view_without_approver(self):
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "development",
                "LICENSE_REQUEST_TEST_MODE": "true",
            },
        ):
            self.principal = AuthenticatedPrincipal(
                object_id="shared-development-account",
                roles=frozenset(),
                claims={
                    "account_type": "shared",
                    "license_request_test_mode": True,
                },
            )

            options = self.client.get("/api/v1/license-requests/options")
            self.assertEqual(options.status_code, 200)
            self.assertTrue(options.json()["test_mode"])
            self.assertGreater(len(options.json()["users"]), 0)
            self.assertGreater(len(options.json()["licenses"]), 0)

            payload = self._payload()
            created = self.client.post("/api/v1/license-requests", json=payload)
            self.assertEqual(created.status_code, 201, created.text)
            saved = created.json()
            self.assertTrue(saved["request_id"].startswith("LIC-"))
            self.assertEqual(saved["status"], "Pending Approval")
            self.assertEqual(saved["employee_name"], self.employee.name)
            self.assertEqual(saved["requester_identity"], "shared-development-account")
            self.assertTrue(saved["test_mode"])
            self.assertFalse(saved["can_decide"])
            self.assertIsNone(saved["approver_id"])
            self.assertEqual(saved["approvals"], [])

            request_record = self.db.query(LicenseRequest).one()
            self.assertEqual(request_record.user_id, self.employee.id)
            self.assertEqual(request_record.requester_identity, "shared-development-account")
            self.assertIsNone(request_record.approver_id)
            self.assertEqual(self.db.query(LicenseApproval).count(), 0)

            listed = self.client.get("/api/v1/license-requests")
            self.assertEqual(listed.status_code, 200)
            self.assertEqual(listed.json()[0]["request_id"], saved["request_id"])

            detail = self.client.get(
                f"/api/v1/license-requests/{saved['request_id']}"
            )
            self.assertEqual(detail.status_code, 200)
            self.assertTrue(detail.json()["test_mode"])
            self.assertEqual(detail.json()["approvals"], [])

            decision = self.client.post(
                f"/api/v1/license-requests/{saved['request_id']}/decision",
                json={"decision": "Approved"},
            )
            self.assertEqual(decision.status_code, 403)

            with patch.dict(os.environ, {"LICENSE_REQUEST_TEST_MODE": "false"}):
                disabled = self.client.get("/api/v1/license-requests/options")
            self.assertEqual(disabled.status_code, 403)


if __name__ == "__main__":
    unittest.main()
