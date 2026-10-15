import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite://")

import jwt
from fastapi.testclient import TestClient

from app import app
from auth.session import SESSION_AUDIENCE, SESSION_ISSUER, SESSION_COOKIE_NAME


class SharedAuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.settings = patch.dict(
            os.environ,
            {
                "AUTH_USERNAME": "clouddestinations@gmail.com",
                "AUTH_PASSWORD": "cloud@123",
                "AUTH_TOKEN_SECRET": "test-only-signing-key-with-at-least-32-bytes",
                "AUTH_TOKEN_TTL_MINUTES": "30",
                "AUTH_COOKIE_SECURE": "false",
                "APP_ENV": "production",
                "LICENSE_REQUEST_TEST_MODE": "false",
            },
        )
        self.settings.start()
        self.client = TestClient(app, client=("127.0.0.1", 50000))

    def tearDown(self):
        self.client.close()
        self.settings.stop()

    def test_valid_login_sets_http_only_session_without_returning_token(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "clouddestinations@gmail.com",
                "password": "cloud@123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("token", response.json())
        self.assertEqual(response.json()["user"]["roles"], [])
        self.assertTrue(response.json()["user"]["is_shared_account"])
        cookie = response.headers["set-cookie"].lower()
        self.assertIn(f"{SESSION_COOKIE_NAME}=", cookie)
        self.assertIn("httponly", cookie)
        self.assertIn("samesite=strict", cookie)
        self.assertNotIn("cloud@123", response.text)

    def test_invalid_login_is_rejected(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "clouddestinations@gmail.com",
                "password": "incorrect",
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["detail"],
            "The username or password is incorrect.",
        )

    def test_request_api_requires_session_and_shared_account_has_no_request_role(self):
        unauthenticated = self.client.get("/api/v1/license-requests/options")
        self.assertEqual(unauthenticated.status_code, 401)

        self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "clouddestinations@gmail.com",
                "password": "cloud@123",
            },
        )
        shared_account = self.client.get("/api/v1/license-requests/options")
        self.assertEqual(shared_account.status_code, 403)

    def test_logout_clears_cookie_and_protected_session(self):
        self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "clouddestinations@gmail.com",
                "password": "cloud@123",
            },
        )
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 200)

        response = self.client.post("/api/v1/auth/logout")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)

    def test_expired_session_is_rejected(self):
        now = datetime.now(timezone.utc)
        expired_token = jwt.encode(
            {
                "sub": "shared-development-account",
                "account_type": "shared",
                "preferred_username": "clouddestinations@gmail.com",
                "roles": [],
                "iat": now - timedelta(minutes=2),
                "exp": now - timedelta(minutes=1),
                "iss": SESSION_ISSUER,
                "aud": SESSION_AUDIENCE,
            },
            os.environ["AUTH_TOKEN_SECRET"],
            algorithm="HS256",
        )
        self.client.cookies.set(SESSION_COOKIE_NAME, expired_token, path="/api/v1")

        response = self.client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_local_request_test_mode_requires_explicit_flag_and_loopback(self):
        login_body = {
            "username": "clouddestinations@gmail.com",
            "password": "cloud@123",
        }
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "development",
                "LICENSE_REQUEST_TEST_MODE": "true",
            },
        ):
            local = self.client.post("/api/v1/auth/login", json=login_body)
            self.assertTrue(local.json()["user"]["license_request_test_mode"])

            remote_client = TestClient(app, client=("192.0.2.10", 50000))
            try:
                remote = remote_client.post("/api/v1/auth/login", json=login_body)
                self.assertFalse(remote.json()["user"]["license_request_test_mode"])
            finally:
                remote_client.close()

        disabled = self.client.post("/api/v1/auth/login", json=login_body)
        self.assertFalse(disabled.json()["user"]["license_request_test_mode"])


if __name__ == "__main__":
    unittest.main()
