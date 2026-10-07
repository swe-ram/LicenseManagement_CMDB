
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

SLACK_BILLING_URL = "https://slack.com/api/team.billing.info"


async def get_slack_license_info():
    token = os.getenv("SLACK_BOT_TOKEN")

    if not token:
        return {
            "application": "Slack",
            "license_data_available": False,
            "error": "SLACK_BOT_TOKEN is not configured."
        }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                SLACK_BILLING_URL,
                headers={"Authorization": f"Bearer {token}"}
            )

            response.raise_for_status()
            data = response.json()

        if not data.get("ok"):
            return {
                "application": "Slack",
                "license_data_available": False,
                "error": data.get("error", "Slack API request failed"),
                "required_action": (
                    "Verify team.billing:read scope, token permissions, "
                    "and app installation."
                )
            }

        plan = data.get("plan", "unknown")

        plan_names = {
            "free": "Free",
            "std": "Pro",
            "plus": "Business+",
            "enterprise": "Enterprise",
            "compliance": "Enterprise Compliance Select"
        }

        return {
            "application": "Slack",
            "license_data_available": True,
            "plan_code": plan,
            "plan_name": plan_names.get(plan, plan),
            "purchased_seat_count": None,
            "message": (
                "Workspace plan retrieved. Purchased seat quantity "
                "is not returned by this endpoint."
            )
        }

    except httpx.HTTPError as exc:
        return {
            "application": "Slack",
            "license_data_available": False,
            "error": str(exc)
        }