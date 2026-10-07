
import logging
import time
from typing import Any

import requests
from fastapi import HTTPException, status


logger = logging.getLogger("slack_license_inventory")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )
    )
    logger.addHandler(handler)


class SlackClient:
    BASE_URL = "https://slack.com/api"
    MAX_RETRIES = 3

    def __init__(
        self,
        bot_token: str | None = None,
        user_token: str | None = None,
        admin_token: str | None = None,
    ):
        self.bot_token = bot_token
        self.user_token = user_token
        self.admin_token = admin_token

    # ---------------------------------------------------------
    # TOKEN SELECTION
    # ---------------------------------------------------------

    def get_token_for_scope(
        self,
        scope: str = "general",
    ) -> str | None:

        """
        Select the appropriate Slack token for an API category.

        users      -> User token first, then Bot token
        billing    -> Admin token first, then User token
        admin      -> Admin token first, then User token
        enterprise -> Admin token first, then User token
        general    -> Bot token first
        """

        # User/member APIs
        if scope in {
            "user",
            "users",
            "presence",
        }:

            if self.user_token:
                return self.user_token

            if self.bot_token:
                return self.bot_token

            return None

        # Billing/admin APIs
        if scope in {
            "billing",
            "admin",
            "enterprise",
        }:

            if self.admin_token:
                return self.admin_token

            if self.user_token:
                return self.user_token

            if self.bot_token:
                return self.bot_token

            return None

        # General APIs
        if self.bot_token:
            return self.bot_token

        if self.user_token:
            return self.user_token

        if self.admin_token:
            return self.admin_token

        return None

    # ---------------------------------------------------------
    # TOKEN TYPE
    # ---------------------------------------------------------

    def get_token_type(
        self,
        token: str | None,
    ) -> str:

        if not token:
            return "none"

        if self.user_token and token == self.user_token:
            return "user_token"

        if self.admin_token and token == self.admin_token:
            return "admin_token"

        if self.bot_token and token == self.bot_token:
            return "bot_token"

        return "unknown_token"

    # ---------------------------------------------------------
    # SLACK API REQUEST
    # ---------------------------------------------------------

    def request(
        self,
        api_method: str,
        params: dict[str, Any] | None = None,
        token: str | None = None,
        max_retries: int = MAX_RETRIES,
    ) -> dict[str, Any]:

        route = f"{self.BASE_URL}/{api_method}"

        request_data = params.copy() if params else {}

        chosen_token = (
            token
            or self.get_token_for_scope()
        )

        token_type = self.get_token_type(chosen_token)

        if not chosen_token:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "missing_token",
                    "message": (
                        "No Slack token is configured "
                        "for this endpoint."
                    ),
                    "endpoint": f"/{api_method}",
                },
            )

        headers = {
            "Authorization": f"Bearer {chosen_token}",
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
        }

        logger.info(
            "Slack API request started",
            extra={
                "endpoint": f"/{api_method}",
                "method": "POST",
                "token_type": token_type,
                "token_present": True,
            },
        )

        for attempt in range(
            1,
            max_retries + 1,
        ):

            try:

                response = requests.post(
                    route,
                    data=request_data,
                    headers=headers,
                    timeout=30,
                )

            except requests.RequestException as exc:

                raise HTTPException(
                    status_code=(
                        status.HTTP_503_SERVICE_UNAVAILABLE
                    ),
                    detail={
                        "error": "network_error",
                        "message": (
                            "The Slack API request failed "
                            "due to a network or connectivity "
                            "problem."
                        ),
                        "endpoint": f"/{api_method}",
                    },
                ) from exc

            # -------------------------------------------------
            # RATE LIMIT
            # -------------------------------------------------

            if response.status_code == 429:

                try:
                    retry_after = int(
                        response.headers.get(
                            "Retry-After",
                            "1",
                        )
                    )
                except ValueError:
                    retry_after = 1

                logger.warning(
                    "Slack API rate limit hit",
                    extra={
                        "endpoint": f"/{api_method}",
                        "retry_after": retry_after,
                        "attempt": attempt,
                    },
                )

                if attempt >= max_retries:

                    raise HTTPException(
                        status_code=(
                            status.HTTP_429_TOO_MANY_REQUESTS
                        ),
                        detail={
                            "error": "rate_limited",
                            "message": (
                                "Slack rate limiting prevented "
                                "the request from completing."
                            ),
                            "endpoint": f"/{api_method}",
                            "retry_after": retry_after,
                        },
                    )

                time.sleep(
                    min(
                        retry_after,
                        10,
                    )
                )

                continue

            # -------------------------------------------------
            # JSON RESPONSE
            # -------------------------------------------------

            try:

                payload = response.json()

            except ValueError as exc:

                raise HTTPException(
                    status_code=(
                        status.HTTP_502_BAD_GATEWAY
                    ),
                    detail={
                        "error": "invalid_slack_response",
                        "message": (
                            "Slack returned an invalid "
                            "response payload."
                        ),
                        "endpoint": f"/{api_method}",
                    },
                ) from exc

            # -------------------------------------------------
            # SLACK API ERROR
            # -------------------------------------------------

            if not payload.get("ok", False):

                error_code = payload.get(
                    "error",
                    "slack_api_error",
                )

                status_code = (
                    status.HTTP_400_BAD_REQUEST
                )

                message = (
                    "Slack API returned an error."
                )

                required_scopes = []

                # ---------------------------------------------
                # AUTH ERRORS
                # ---------------------------------------------

                if error_code in {
                    "invalid_auth",
                    "account_inactive",
                    "token_expired",
                    "not_authed",
                    "token_revoked",
                }:

                    status_code = (
                        status.HTTP_401_UNAUTHORIZED
                    )

                    message = (
                        "The configured Slack token "
                        "is invalid, expired, or "
                        "not authorized."
                    )

                # ---------------------------------------------
                # PERMISSION ERRORS
                # ---------------------------------------------

                elif error_code in {
                    "missing_scope",
                    "not_allowed_token_type",
                }:

                    status_code = (
                        status.HTTP_403_FORBIDDEN
                    )

                    message = (
                        "The configured Slack token does "
                        "not have the required permission."
                    )

                    # Known endpoint requirements
                    if api_method == "users.list":

                        required_scopes = [
                            "users:read",
                            "users:read.email",
                        ]

                    elif api_method == "team.billableInfo":

                        required_scopes = [
                            "admin/billing-related "
                            "permissions as applicable"
                        ]

                    elif api_method == "team.info":

                        required_scopes = [
                            "team:read"
                        ]

                # ---------------------------------------------
                # RATE LIMIT
                # ---------------------------------------------

                elif error_code == "rate_limited":

                    status_code = (
                        status.HTTP_429_TOO_MANY_REQUESTS
                    )

                    message = (
                        "Slack rate limiting prevented "
                        "the request from completing."
                    )

                # ---------------------------------------------
                # CHANNEL ERRORS
                # ---------------------------------------------

                elif error_code in {
                    "method_not_supported_for_channel_type",
                    "not_in_channel",
                }:

                    status_code = (
                        status.HTTP_400_BAD_REQUEST
                    )

                    message = (
                        "The Slack API method is not "
                        "supported for the current resource "
                        "or channel context."
                    )

                logger.error(
                    "Slack API returned an error",
                    extra={
                        "endpoint": f"/{api_method}",
                        "error": error_code,
                        "status_code": status_code,
                        "token_type": token_type,
                    },
                )

                raise HTTPException(
                    status_code=status_code,
                    detail={
                        "error": error_code,
                        "message": message,
                        "endpoint": f"/{api_method}",
                        "token_type": token_type,
                        "required_scopes": required_scopes,
                        "required_action": (
                            "Add the required Slack scopes "
                            "to the application and reinstall "
                            "the Slack app to refresh the OAuth "
                            "token."
                            if error_code
                            in {
                                "missing_scope",
                                "not_allowed_token_type",
                            }
                            else None
                        ),
                    },
                )

            # -------------------------------------------------
            # SUCCESS
            # -------------------------------------------------

            logger.info(
                "Slack API call succeeded",
                extra={
                    "endpoint": f"/{api_method}",
                    "status_code": response.status_code,
                    "token_type": token_type,
                },
            )

            return payload

        # -----------------------------------------------------
        # RETRIES EXHAUSTED
        # -----------------------------------------------------

        raise HTTPException(
            status_code=(
                status.HTTP_429_TOO_MANY_REQUESTS
            ),
            detail={
                "error": "rate_limited",
                "message": (
                    "Slack rate limiting prevented the "
                    "request from completing after "
                    "retry attempts."
                ),
                "endpoint": f"/{api_method}",
            },
        )

    # ---------------------------------------------------------
    # AUTH TEST
    # ---------------------------------------------------------

    def auth_test(self) -> dict[str, Any]:

        return self.request(
            "auth.test"
        )

    # ---------------------------------------------------------
    # PAGINATION
    # ---------------------------------------------------------

    def paginate(
        self,
        api_method: str,
        response_key: str,
        params: dict[str, Any] | None = None,
        token: str | None = None,
        max_pages: int = 25,
    ) -> list[dict[str, Any]]:

        collected: list[dict[str, Any]] = []

        cursor = ""

        page_number = 0

        request_params = {
            "limit": 200
        }

        request_params.update(
            params or {}
        )

        while page_number < max_pages:

            current_params = (
                request_params.copy()
            )

            if cursor:
                current_params[
                    "cursor"
                ] = cursor

            payload = self.request(
                api_method,
                params=current_params,
                token=token,
            )

            items = payload.get(
                response_key,
                [],
            )

            if isinstance(
                items,
                list,
            ):

                collected.extend(
                    items
                )

            logger.info(
                "Slack pagination completed",
                extra={
                    "endpoint": f"/{api_method}",
                    "page_number": (
                        page_number + 1
                    ),
                    "records_fetched": (
                        len(collected)
                    ),
                },
            )

            metadata = payload.get(
                "response_metadata",
                {},
            )

            next_cursor = (
                metadata.get("next_cursor")
                or payload.get("next_cursor")
            )

            if not next_cursor:
                break

            cursor = next_cursor

            page_number += 1

        logger.info(
            "Slack pagination summary",
            extra={
                "endpoint": f"/{api_method}",
                "total_records": len(collected),
                "page_count": (
                    page_number + 1
                ),
            },
        )

