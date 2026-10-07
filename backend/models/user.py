from pydantic import BaseModel, Field


class SlackUser(BaseModel):
    slack_user_id: str | None = Field(default=None, description="Slack unique user id")
    name: str | None = Field(default=None, description="Slack username")
    display_name: str | None = Field(default=None, description="Display name from user profile")
    real_name: str | None = Field(default=None, description="Real name from Slack profile")
    email: str | None = Field(default=None, description="Primary email address if returned by Slack")
    status: str | None = Field(default=None, description="User state such as active, inactive, deleted")
    is_admin: bool = Field(default=False, description="Whether the user is a Slack admin")
    is_owner: bool = Field(default=False, description="Whether the user is a workspace owner")
    timezone: str | None = Field(default=None, description="Slack timezone if available")
