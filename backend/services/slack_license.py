from typing import Any

from services.slack_client import SlackClient
from database.license_repository import save_slack_license


def get_license_data(client: SlackClient) -> dict[str, Any]:

    base_response: dict[str, Any] = {
        "application": "Slack",
        "vendor": "Slack",

        # License information
        "plan": None,
        "license_type": None,

        # Quantities
        "purchased_quantity": None,
        "entitled_quantity": None,
        "assigned_quantity": None,
        "available_quantity": None,

        # Users
        "active_users": None,
        "inactive_users": None,

        # Commercial information
        "renewal_date": None,
        "cost": None,
        "currency": None,
        "billing_cycle": None,

        # Source
        "data_source": "Slack API",
        "data_available": False,

        "reason": None,
        "required_action": None,
    }

    # ---------------------------------------------------------
    # GET SLACK TOKEN
    # ---------------------------------------------------------

    token = client.get_token_for_scope("billing")

    if not token:

        return {
            **base_response,
            "reason": (
                "Slack billing/license information requires "
                "appropriate administrative permissions."
            ),
            "required_action": (
                "Configure the appropriate Slack admin/user token "
                "and required billing permissions."
            ),
            "license_data_available": False,
        }

    # ---------------------------------------------------------
    # WORKSPACE / PLAN
    # ---------------------------------------------------------

    try:

        team_info = client.request(
            "team.info",
            token=token,
        )

        team_data = (
            team_info.get("team", {})
            if isinstance(team_info, dict)
            else {}
        )

        plan = team_data.get("plan")

        if isinstance(plan, dict):
            raw_plan = (
                plan.get("name")
                or plan.get("id")
                or plan.get("name_normalized")
            )
        elif plan:
            raw_plan = plan
        else:
            raw_plan = None

        if raw_plan and isinstance(raw_plan, str):
            import re
            cleaned_plan = re.sub(r"\s*\([Tt]he\s*zastudios\)", "", raw_plan, flags=re.IGNORECASE)
            cleaned_plan = re.sub(r"the\s*zastudios|zastudios", "", cleaned_plan, flags=re.IGNORECASE).strip() or "Slack Pro"
            base_response["plan"] = cleaned_plan
        else:
            base_response["plan"] = raw_plan
    except Exception as exc:

        base_response["reason"] = (
            f"Unable to retrieve Slack plan: {str(exc)}"
        )

    # ---------------------------------------------------------
    # BILLABLE USERS
    # ---------------------------------------------------------

    try:

        billable_info = client.request(
            "team.billableInfo",
            params={"limit": 200},
            token=token,
        )

        billable_data = (
            billable_info.get("billable_info", {})
            if isinstance(billable_info, dict)
            else {}
        )

        if isinstance(billable_data, dict):

            assigned_users = 0
            active_users = 0
            inactive_users = 0

            for user_id, user_data in billable_data.items():

                if not isinstance(user_data, dict):
                    continue

                assigned_users += 1

                billing_active = user_data.get(
                    "billing_active"
                )

                if billing_active is True:

                    active_users += 1

                elif billing_active is False:

                    inactive_users += 1

            base_response["assigned_quantity"] = (
                assigned_users
            )

            base_response["active_users"] = (
                active_users
            )

            base_response["inactive_users"] = (
                inactive_users
            )

            base_response["license_type"] = (
                "billable_users"
            )

            base_response["data_available"] = True

    except Exception as exc:

        if not base_response["reason"]:

            base_response["reason"] = (
                "Unable to retrieve billable user "
                f"information: {str(exc)}"
            )

    # ---------------------------------------------------------
    # AVAILABLE LICENSES
    # ---------------------------------------------------------

    entitled = base_response.get(
        "entitled_quantity"
    )

    assigned = base_response.get(
        "assigned_quantity"
    )

    if entitled is not None and assigned is not None:

        base_response["available_quantity"] = max(
            entitled - assigned,
            0,
        )

    # ---------------------------------------------------------
    # FINAL RESPONSE
    # ---------------------------------------------------------

    base_response["license_data_available"] = (
        base_response["data_available"]
    )

    # ---------------------------------------------------------
    # SAVE TO POSTGRESQL
    # ---------------------------------------------------------

    if base_response["data_available"]:

        try:

            database_result = save_slack_license(
                base_response
            )

        except Exception as exc:

            database_result = {
                "success": False,
                "error": str(exc),
            }

    else:

        database_result = {
            "success": False,
            "error": (
                "No license data available from Slack API."
            ),
        }

    base_response["database"] = database_result

    return base_response


def get_slack_license_info(
    client: SlackClient,
) -> dict[str, Any]:
    """
    Compatibility wrapper.

    Uses the already configured SlackClient instead of creating
    a second client with empty tokens.
    """

    return get_license_data(client)