
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    field_validator,
)

class TicketRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal[
        "Shipping", "Refund", "Account",
        "Product", "Billing", "Other"
    ]

    urgency: Literal["Low", "Medium", "High"]

    sentiment: Literal[
        "Positive", "Neutral", "Negative", "Very Angry"
    ]

    language: str = Field(min_length=2)
    summary: str = Field(min_length=1)

    escalation_signals: list[str]
    evidence_found: StrictBool
    policy_sources: list[str]

    proposed_response: str = Field(min_length=1)

    escalation_decision: Literal["Pending", "Escalated"]
    escalation_reason: str | None

    ticket_status: Literal["Pending", "Escalated"]
    review_status: Literal["Pending"]

    @field_validator(
        "language",
        "summary",
        "proposed_response",
    )
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Text cannot be blank")
        return value

    @field_validator(
        "escalation_signals",
        "policy_sources",
    )
    @classmethod
    def validate_string_lists(
        cls, values: list[str]
    ) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError(
                "List entries cannot be blank"
            )
        return values


def validate_ticket_record(record: dict) -> dict:
    """
    Validate the Log Agent's structured output.

    Returns a normalized dictionary.
    Raises ValidationError for invalid records.
    """
    validated = TicketRecord.model_validate(record)
    return validated.model_dump()
