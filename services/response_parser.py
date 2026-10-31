
import re


def extract_customer_response(agent_output: str) -> str:
    """
    Extract only the customer-facing draft from
    the Resolution Agent's structured output.

    Reject missing or empty customer responses.
    """

    if not isinstance(agent_output, str):
        raise ValueError("Agent output must be a string.")

    pattern = (
        r"^\s*Customer Response:\s*"
        r"(.*?)"
        r"(?=^\s*Supporting Policies:|\Z)"
    )

    match = re.search(
        pattern,
        agent_output,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )

    if not match:
        raise ValueError(
            "Customer Response section not found."
        )

    response = match.group(1).strip()

    if not response:
        raise ValueError(
            "Customer response cannot be empty."
        )

    # Reject internal workflow sections that may have
    # leaked into the customer-facing draft.
    internal_sections = [
        "Supporting Policies:",
        "Recommended Action:",
        "Human Review Recommended:",
    ]

    if any(
        re.search(
            rf"(?im)^\s*{re.escape(section)}",
            response,
        )
        for section in internal_sections
    ):
        raise ValueError(
            "Customer response contains internal workflow sections."
        )

    return response
