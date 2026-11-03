
import json

from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from agents.human_reviewer_agent import (
    create_human_reviewer_agent,
)


async def collect_human_review(
    reviewer: str,
    action: str,
    notes: str = "",
) -> dict:
    """
    Pass a Streamlit review decision through AutoGen UserProxyAgent.

    Returns the validated human review decision.
    """

    if not reviewer or not reviewer.strip():
        raise ValueError("Reviewer name is required.")

    if action not in {"Approve", "Revise", "Reject"}:
        raise ValueError("Invalid review action.")

    if action in {"Revise", "Reject"} and not notes.strip():
        raise ValueError(
            "Reviewer notes are required for revision or rejection."
        )

    review_payload = {
        "reviewer": reviewer.strip(),
        "action": action,
        "notes": notes.strip(),
    }

    async def review_input(prompt, cancellation_token=None):
        return json.dumps(review_payload)

    agent = create_human_reviewer_agent(
        input_func=review_input
    )

    try:
        response = await agent.on_messages(
            [
                TextMessage(
                    source="review_console",
                    content="Submit the human review decision.",
                )
            ],
            cancellation_token=CancellationToken(),
        )

        result = json.loads(response.chat_message.content)

        if result != review_payload:
            raise ValueError(
                "UserProxyAgent returned an unexpected review decision."
            )

        return result

    finally:
        await agent.close()
