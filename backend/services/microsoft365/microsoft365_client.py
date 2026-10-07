import os
from typing import Any

import requests


class MicrosoftGraphError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        retry_after: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.retry_after = retry_after


class MicrosoftGraphClient:
    def __init__(self) -> None:
        self.tenant_id = os.getenv("MS_TENANT_ID")
        self.client_id = os.getenv("MS_CLIENT_ID")
        self.client_secret = os.getenv("MS_CLIENT_SECRET")
        self.base_url = "https://graph.microsoft.com"

        missing = [
            name
            for name, value in {
                "MS_TENANT_ID": self.tenant_id,
                "MS_CLIENT_ID": self.client_id,
                "MS_CLIENT_SECRET": self.client_secret,
            }.items()
            if not value
        ]

        if missing:
            raise MicrosoftGraphError(
                "Missing Microsoft Graph environment configuration: "
                + ", ".join(missing)
            )

    def _get_token(self) -> str:
        token_url = (
            f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        )

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
        }

        try:
            response = requests.post(
                token_url,
                data=payload,
                timeout=30,
            )
        except requests.Timeout as exc:  # pragma: no cover - simple timeout guard
            raise MicrosoftGraphError(
                "Microsoft Graph authentication timed out.",
                status_code=504,
            ) from exc
        except requests.RequestException as exc:  # pragma: no cover - simple network guard
            raise MicrosoftGraphError(
                f"Microsoft Graph authentication request failed: {exc}",
                status_code=500,
            ) from exc

        if response.status_code != 200:
            detail = response.text.strip() or "Unknown authentication error"
            raise MicrosoftGraphError(
                f"Microsoft Graph authentication failed: {detail}",
                status_code=response.status_code,
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise MicrosoftGraphError(
                "Microsoft Graph authentication returned an invalid JSON payload.",
                status_code=500,
            ) from exc

        token = data.get("access_token")
        if not token:
            raise MicrosoftGraphError(
                "Microsoft Graph authentication succeeded but no access token was returned.",
                status_code=401,
            )

        return token

    def authenticate(self) -> dict[str, Any]:
        token = self._get_token()
        return {"authenticated": bool(token), "tenant_id": self.tenant_id}

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        token = self._get_token()
        if path.startswith("http://") or path.startswith("https://"):
            url = path
        else:
            url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30,
            )
        except requests.Timeout as exc:
            raise MicrosoftGraphError(
                "Microsoft Graph request timed out.",
                status_code=504,
            ) from exc
        except requests.RequestException as exc:
            raise MicrosoftGraphError(
                f"Microsoft Graph request failed: {exc}",
                status_code=500,
            ) from exc

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise MicrosoftGraphError(
                "Microsoft Graph rate limit reached; please retry later.",
                status_code=429,
                retry_after=retry_after,
            )

        if response.status_code in (401, 403):
            detail = response.text.strip() or "Authorization failed"
            raise MicrosoftGraphError(
                f"Microsoft Graph authorization failed: {detail}",
                status_code=response.status_code,
            )

        if response.status_code >= 400:
            detail = response.text.strip() or "Unknown Microsoft Graph API error"
            raise MicrosoftGraphError(
                f"Microsoft Graph request failed: {detail}",
                status_code=response.status_code,
            )

        if not response.content:
            return {}

        try:
            return response.json()
        except ValueError as exc:
            raise MicrosoftGraphError(
                "Microsoft Graph returned an invalid JSON response.",
                status_code=500,
            ) from exc

    def get_all(self, path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        url_path = path
        aggregated: list[dict[str, Any]] = []

        while url_path:
            payload = self.get(url_path, params=params)
            items = payload.get("value", [])
            if isinstance(items, list):
                aggregated.extend(items)
            next_link = payload.get("@odata.nextLink")
            if next_link:
                url_path = next_link
                params = None
                continue
            break

        return aggregated
