from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv(Path(__file__).resolve().parents[3] / ".env")


class SophosAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SophosClient:
    AUTH_URL = "https://id.sophos.com/api/v2/oauth2/token"
    WHOAMI_URL = "https://api.central.sophos.com/whoami/v1"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        self.client_id = client_id or os.getenv("SOPHOS_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SOPHOS_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise SophosAPIError(
                "Missing Sophos API credentials: SOPHOS_CLIENT_ID and SOPHOS_CLIENT_SECRET must be configured."
            )

        self._access_token: str | None = None
        self._tenant_id: str | None = None
        self._id_type: str | None = None
        self._global_host: str = "https://api.central.sophos.com"
        self._data_region: str | None = None

    def authenticate(self) -> str:
        """Authenticate with Sophos OAuth 2.0 and retrieve JWT access token."""
        try:
            response = requests.post(
                self.AUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "token",
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            raise SophosAPIError(f"Sophos authentication network error: {exc}", status_code=500) from exc

        if response.status_code != 200:
            raise SophosAPIError(
                f"Sophos authentication failed: {response.status_code} - {response.text}",
                status_code=response.status_code,
            )

        data = response.json()
        token = data.get("access_token")
        if not token:
            raise SophosAPIError("Sophos authentication succeeded but access_token was missing.", status_code=500)

        self._access_token = token
        return token

    def _ensure_whoami(self) -> None:
        """Fetch caller identity (tenant ID, data region, API hosts)."""
        if self._tenant_id and self._data_region:
            return

        token = self._access_token or self.authenticate()
        try:
            resp = requests.get(
                self.WHOAMI_URL,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
        except requests.RequestException as exc:
            raise SophosAPIError(f"Sophos whoami request error: {exc}", status_code=500) from exc

        if resp.status_code != 200:
            raise SophosAPIError(
                f"Sophos whoami call failed: {resp.status_code} - {resp.text}",
                status_code=resp.status_code,
            )

        whoami_data = resp.json()
        self._tenant_id = whoami_data.get("id")
        self._id_type = whoami_data.get("idType")
        api_hosts = whoami_data.get("apiHosts", {})
        self._global_host = api_hosts.get("global", "https://api.central.sophos.com")
        self._data_region = api_hosts.get("dataRegion", self._global_host)

    def _get_headers(self) -> dict[str, str]:
        self._ensure_whoami()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "X-Tenant-ID": self._tenant_id or "",
        }

    def get_licenses(self) -> list[dict[str, Any]]:
        """Fetch both core product licenses and firewall licenses from Sophos Central."""
        headers = self._get_headers()
        all_licenses: list[dict[str, Any]] = []

        # 1. Fetch main licenses
        try:
            main_url = f"{self._global_host}/licenses/v1/licenses"
            resp = requests.get(main_url, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for lic in data.get("licenses", []):
                    prod = lic.get("product", {})
                    usage = lic.get("usage", {}).get("current", {})
                    qty = int(lic.get("quantity") or 0)
                    used = int(usage.get("count") or 0)
                    avail = max(0, qty - used)

                    all_licenses.append(
                        {
                            "license_id": lic.get("id"),
                            "license_key": lic.get("licenseIdentifier"),
                            "product_name": prod.get("name") or "Sophos License",
                            "product_code": prod.get("code"),
                            "license_type": lic.get("type", "term"),
                            "status": "active" if not lic.get("expired") else "expired",
                            "purchased_quantity": qty,
                            "assigned_quantity": used,
                            "available_quantity": avail,
                            "start_date": lic.get("startDate"),
                            "expiration_date": lic.get("endDate"),
                            "auto_renewal": bool(lic.get("autoRenewal", False)),
                            "data_source": "Sophos Central API",
                        }
                    )
        except Exception as exc:
            print(f"[WARN] Failed to fetch Sophos main licenses: {exc}")

        # 2. Fetch firewall licenses
        try:
            fw_url = f"{self._global_host}/licenses/v1/licenses/firewalls"
            resp = requests.get(fw_url, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("items", []):
                    for lic in item.get("licenses", []):
                        prod = lic.get("product", {})
                        usage = lic.get("usage", {}).get("current", {})
                        qty = int(lic.get("quantity") or 0)
                        used = int(usage.get("count") or 0)
                        avail = max(0, qty - used)

                        all_licenses.append(
                            {
                                "license_id": lic.get("id"),
                                "license_key": lic.get("licenseIdentifier"),
                                "product_name": prod.get("name") or "Sophos Firewall License",
                                "product_code": prod.get("code"),
                                "license_type": lic.get("type", "trial"),
                                "status": "active",
                                "purchased_quantity": qty,
                                "assigned_quantity": used,
                                "available_quantity": avail,
                                "start_date": lic.get("startDate"),
                                "expiration_date": lic.get("endDate"),
                                "auto_renewal": bool(lic.get("autoRenewal", False)),
                                "data_source": "Sophos Central Firewall API",
                            }
                        )
        except Exception as exc:
            print(f"[WARN] Failed to fetch Sophos firewall licenses: {exc}")

        return all_licenses

    def get_users(self) -> list[dict[str, Any]]:
        """Fetch directory users and their assigned endpoints from Sophos Central."""
        headers = self._get_headers()

        # 1. Fetch endpoints to map to users
        person_endpoints: dict[str, dict[str, Any]] = {}
        person_name_endpoints: dict[str, dict[str, Any]] = {}

        try:
            ep_url = f"{self._data_region}/endpoint/v1/endpoints?pageSize=500"
            resp = requests.get(ep_url, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for ep in data.get("items", []):
                    person = ep.get("associatedPerson")
                    if person:
                        pid = person.get("id")
                        pname = (person.get("name") or "").lower().strip()
                        if pid:
                            person_endpoints[pid] = ep
                        if pname:
                            person_name_endpoints[pname] = ep
        except Exception as exc:
            print(f"[WARN] Failed to fetch Sophos endpoints: {exc}")

        # 2. Fetch directory users with pagination
        all_users: list[dict[str, Any]] = []
        page = 1
        page_size = 100

        while True:
            try:
                users_url = f"{self._data_region}/common/v1/directory/users?page={page}&pageSize={page_size}"
                resp = requests.get(users_url, headers=headers, timeout=30)
                if resp.status_code != 200:
                    print(f"[WARN] Sophos users page {page} failed with status {resp.status_code}")
                    break

                data = resp.json()
                items = data.get("items", [])
                if not items:
                    break

                for u in items:
                    uid = u.get("id")
                    name = u.get("name") or "Sophos User"
                    email = u.get("email")

                    # Extract department from groups
                    dept = None
                    groups_data = u.get("groups", {})
                    group_items = groups_data.get("items", []) if isinstance(groups_data, dict) else []
                    if group_items:
                        dept = group_items[0].get("displayName") or group_items[0].get("name")

                    # Match with endpoint by ID or name
                    matched_ep = person_endpoints.get(uid) or person_name_endpoints.get(name.lower().strip())
                    endpoint_hostname = matched_ep.get("hostname") if matched_ep else None
                    endpoint_os = matched_ep.get("os", {}).get("name") if matched_ep else None

                    assigned_prods = None
                    if matched_ep:
                        prods = [p.get("code") for p in matched_ep.get("assignedProducts", []) if p.get("code")]
                        assigned_prods = ", ".join(prods) if prods else "endpointProtection, interceptX"
                    else:
                        assigned_prods = "endpointProtection"

                    last_act = matched_ep.get("lastSeenAt") if matched_ep else u.get("updatedAt")

                    # Infer role
                    is_admin = any(
                        keyword in (name or "").lower() or keyword in (email or "").lower()
                        for keyword in ["admin", "director", "manager", "head"]
                    )

                    all_users.append(
                        {
                            "sophos_user_id": uid,
                            "name": name,
                            "email": email,
                            "department": dept or "Information Technology",
                            "role": "Admin" if is_admin else "User",
                            "status": "active",
                            "source_type": u.get("source", {}).get("type", "custom"),
                            "endpoint_hostname": endpoint_hostname,
                            "endpoint_os": endpoint_os,
                            "assigned_products": assigned_prods,
                            "created_in_sophos_at": u.get("createdAt"),
                            "last_activity": last_act,
                        }
                    )

                page += 1
            except Exception as exc:
                print(f"[WARN] Error fetching Sophos users on page {page}: {exc}")
                break

        return all_users

