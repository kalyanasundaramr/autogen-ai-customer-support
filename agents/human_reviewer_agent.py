
from autogen_agentchat.agents import UserProxyAgent


def create_human_reviewer_agent(input_func=None):
    """
    Create a human reviewer represented by AutoGen UserProxyAgent.

    The input function can be connected to a UI or
    another application-level input mechanism.
    """

    return UserProxyAgent(
        name="human_reviewer",
        description=(
            "Represents a human customer support reviewer. "
            "Reviews escalated customer support responses "
            "and provides approval, revision, or rejection."
        ),
        input_func=input_func,
    )
