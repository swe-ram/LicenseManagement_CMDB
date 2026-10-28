# Slack License Inventory API

This project provides a FastAPI-based module for gathering Slack workspace, user, license, and usage information into a normalized inventory payload that can later be inserted into a centralized license management platform.

## 1. What the project does

The API reads real Slack data from the Slack API using configured bot, user, or admin tokens. It exposes endpoints to retrieve:

- authentication status
- workspace metadata
- member inventory
- employee mapping placeholders for future identity integration
- licensing information when available from Slack admin APIs
- usage information when available from Slack APIs
- a combined normalized inventory payload
- optimization recommendations without making automatic changes

The implementation intentionally distinguishes between:

- workspace/member inventory
- commercial license entitlement data
- license assignment data
- actual product usage data
- billing metadata

This avoids accidentally manufacturing Slack licensing values when the API does not provide them.

## 2. Slack API architecture

The service layer is intentionally modular so it can later integrate additional vendors such as Microsoft 365, Adobe, Salesforce, Zoom, and Atlassian.

At a high level:

- global configuration loads .env values
- the Slack client manages outbound API requests, errors, and pagination
- workspace, user, license, and usage services normalize Slack data into central inventory-ready shapes
- the router exposes the REST endpoints for the application
- the application output can later be inserted into a centralized database model

## 3. Required Slack app setup

Create a Slack app in the Slack API portal and configure the following:

- OAuth scopes needed for the endpoints you want to use
- proper token types for the bot, user, or admin workflow
- workspace installation and admin approval if required by your Slack environment

For a production deployment, use least-privilege scopes and only grant the minimum permissions required for the relevant data.

## 4. Required OAuth scopes

Common scopes that may be needed include:

- `users:read` to read user lists and metadata
- `team:read` to read workspace and team information
- `users:read.email` if you need user email addresses
- `users.profile:read` depending on the Slack app configuration and API availability
- `admin`-level scopes or enterprise admin APIs for commercial billing/license data

The specific scopes depend on the workspace type (free, standard, enterprise) and the APIs available to the Slack installation. Some commercial license and billing APIs may require admin or enterprise privileges and may not be available to a normal user or bot token.

## 5. How to create/configure Slack tokens

1. Open Slack API and create an app.
2. Add the needed OAuth scopes to the app.
3. Install the app to the workspace.
4. Copy the generated tokens into your .env file.
5. Use the token type that matches the endpoint requirements.

Example:

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_USER_TOKEN=xoxp-...
SLACK_ADMIN_TOKEN=xoxp-...
```

Do not paste secrets into application source code. Keep them only in .env.

## 6. Which endpoints require admin permissions

The following areas are generally admin or enterprise dependent:

- Slack commercial license/billing entitlement data
- enterprise-level license information
- billable user assignment data
- renewal or cost details when the Slack admin APIs expose them

The service will check for the appropriate token and permission level and return a permission-aware error instead of inventing values when the current token cannot access those endpoints.

## 7. How to configure .env

Create a .env file using the example file:

```bash
cp .env.example .env
```

Then update the values with your own Slack tokens. At minimum:

```env
SLACK_BOT_TOKEN=
SLACK_USER_TOKEN=
SLACK_ADMIN_TOKEN=
```

The application accepts whichever token is configured and returns clear permission errors when an endpoint needs a stronger scope or admin token.

## 8. How to install dependencies

From the workspace root:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 9. How to run FastAPI

Start the API with:

```bash
python -m uvicorn app:app --reload --port 8000
```

Then open:

- http://localhost:8000/docs
- http://localhost:8000/health

## 10. How to test /docs

Navigate to the Swagger UI at:

```text
http://localhost:8000/docs
```

The Swagger UI exposes the endpoints:

- GET /health
- GET /slack/auth
- GET /slack/workspace
- GET /slack/users
- GET /slack/users/mapping
- GET /slack/license
- GET /slack/usage
- GET /slack/inventory
- GET /slack/optimization

## 11. How to troubleshoot missing_scope

If Slack returns `missing_scope`, it usually means:

- the app/token is missing the required OAuth scope
- the required admin enterprise API is not available for the token type
- the app was not installed or approved for the workspace

Typical actions:

- verify the app has the correct scopes
- confirm the token is the correct one for the endpoint
- verify the workspace installation is active
- check whether the workspace requires enterprise/admin permissions for billing data

## 12. How the data will eventually connect to the central license database

This module outputs normalized JSON structures designed to map to a central database with tables such as:

- USERS
- APPLICATIONS
- PRODUCTS
- LICENSE_ENTITLEMENTS
- LICENSE_ASSIGNMENTS
- USAGE

The shape of the Slack inventory is intentionally aligned with those entities so future integration can load the data into Power BI, Power Apps, Power Automate, or a database-driven central license catalog.

## 13. Future normalization model

The Slack module creates records that can be mapped to the following structure:

- user_id -> Slack user metadata and later employee_id binding
- application_name -> Slack
- vendor -> Slack
- category -> Collaboration
- product -> Slack workspace/licensing product
- entitlement -> purchased or entitled commercial quantities when available
- assignment -> user-to-license mapping when available
- usage -> presence and activity information if Slack exposes it

## 14. Important implementation guidance

This project intentionally does not fabricate Slack user counts, billing quantities, plan data, or usage measures. If Slack does not return these values through the configured API, the service reports `null`, `false`, or a permission-aware error instead of guessing.

## 15. Endpoints summary

- `/health` returns service status
- `/slack/auth` returns non-sensitive authentication info
- `/slack/workspace` returns normalized workspace info
- `/slack/users` returns the Slack user inventory
- `/slack/users/mapping` returns pending employee mapping placeholders
- `/slack/license` returns license data when admin APIs are available
- `/slack/usage` returns usage data when available
- `/slack/inventory` returns the combined normalized payload
- `/slack/optimization` returns recommended optimization actions

## Microsoft 365 assigned-user inventory

The Microsoft 365 sync stores Graph `assignedLicenses` relationships in
`license_assigned_users`. Run the schema/table setup once, then trigger the
existing sync:

```powershell
.\.venv\Scripts\python.exe .\create_tables.py
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/microsoft365/sync"
```

The stored assignments can be read without calling Microsoft Graph:

```text
GET /microsoft365/licenses/assigned-users
```

The response groups currently assigned users by Microsoft 365 license and
includes licenses with no current assignments. Previously assigned users are
retained with `status = "revoked"` in the database but omitted from the active
user lists.

## Development shared-account authentication

Authentication uses backend environment variables only. Set
`AUTH_USERNAME`, `AUTH_PASSWORD`, and a random `AUTH_TOKEN_SECRET` of at least
32 bytes in the backend `.env` file. `AUTH_TOKEN_TTL_MINUTES` controls the
session lifetime (1-1440 minutes); `AUTH_COOKIE_SECURE` must be `true` when
serving over HTTPS and can be `false` for local HTTP development. Keep `.env`
out of source control. Never put these values in Vite environment variables.

The API issues a signed, expiring session token in an HttpOnly, SameSite=Strict
cookie. The shared account intentionally has no employee identity or application
roles. It cannot view or submit individual license requests, or take approval
actions. Request APIs continue to require authenticated identities and
server-side authorization; do not map the shared login to an employee or grant
it `License.Requester`, `License.Approver`, or `License.Admin`. Individual
request/approval workflows require a separately configured, individually
authenticated account.

Authentication endpoints are `POST /api/v1/auth/login`, `GET
/api/v1/auth/me`, and `POST /api/v1/auth/logout`. Expired sessions are rejected
with HTTP 401 and the frontend returns to the login page.

## License request approval workflow

Outside local test mode, the request APIs remain protected by the authenticated
session and existing server-side role/ownership checks. The shared account does
not identify an employee or approver and cannot access individual request
records or submit decisions.

For local development only, the License Requests employee-selection workflow
can be enabled by setting both `APP_ENV=development` (or `local`) and
`LICENSE_REQUEST_TEST_MODE=true` in the backend `.env`. The test-mode session
flag is issued only to logins from a loopback address, and request test routes
also require loopback access. Leave the flag false or unset outside local
development. Test mode allows this shared account to list requests, load
employee/license options, create requests for an explicitly selected database
employee, and inspect saved request details. The request records the selected
employee as the requested-for employee and marks `requester_identity` as
`shared-development-account`; it does not identify that employee as the
submitter. Test requests do not create approval records or enable approve/reject
actions. When no approval record exists, the UI marks pending stages as a
non-persistent test preview, not approval history.

The additive request migration also adds `requester_identity` and allows
`approver_id` to be null for requests awaiting an approver mapping. Apply the
reviewed migration to the configured local database before using this flow.

The portal database already contains `license_requests`, `license_approvals`,
and `department_approvers`. The API maps to those existing tables and to their
existing foreign keys (`employee_id`, `request_number`, and the department
approver row IDs); it does not create parallel request or approval tables.
Migration `001_license_request_approval.sql` only adds the request idempotency
key and urgency fields and creates uniqueness indexes for official request
numbers and non-null per-employee idempotency keys. It raises an error rather
than removing or changing duplicate request records if the existing data
prevents a unique request-number index.

After reviewing the migration and backing up production data, apply the
additive PostgreSQL migration explicitly from this directory:

```powershell
.\.venv\Scripts\python.exe .\migrations\apply_license_request_migration.py
```

The migration runner verifies that the portal's existing tables are present
before changing anything. Do not use the command against production until the
migration has been reviewed and approved. It does not create tables; use the
project's normal schema setup for a fresh development database before applying
it.

Request endpoints:

- `POST /api/v1/license-requests` creates a request and its pending approval
- `GET /api/v1/license-requests` lists only requests visible to the caller
- `GET /api/v1/license-requests/options` returns the caller's employee record
  and licenses available in the database
- `GET /api/v1/license-requests/{request_id}` returns authorized request detail
  and the recorded approval history
- `GET /api/v1/license-requests/{request_id}/approvals` returns approval history
- `POST /api/v1/license-requests/{request_id}/decision` approves or rejects a
  request assigned to the authenticated approver

Request IDs use the database-generated primary key (`LIC-<year>-<id>`), and
request creation accepts a per-user idempotency key to make a network retry
return the original saved request rather than create another.
