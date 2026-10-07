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
