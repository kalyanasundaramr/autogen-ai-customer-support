
import sys
from pathlib import Path

import streamlit as st
import asyncio
import os

from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient

from workflows.revision_workflow import run_revision_workflow

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / ".env")

from database.db import initialize_database
from services.ticket_query_service import (
    list_pending_review_tickets,
    list_revision_requested_tickets,
)
from services.review_service import review_ticket


st.set_page_config(
    page_title="AI Customer Support | Human Review",
    page_icon="🎫",
    layout="wide",
)

initialize_database()

st.title("Human Review Console")
st.caption("AutoGen AI Customer Support Automation")

tickets = list_pending_review_tickets()

total_pending = len(tickets)
escalated = sum(
    ticket["ticket_status"] == "Escalated"
    for ticket in tickets
)
normal = total_pending - escalated

col1, col2, col3 = st.columns(3)

col1.metric("Pending Reviews", total_pending)
col2.metric("Escalated Tickets", escalated)
col3.metric("Standard Tickets", normal)

st.divider()

if not tickets:
    st.info("No tickets are awaiting human review.")
    st.session_state["review_queue_empty"] = True
else:
    st.session_state["review_queue_empty"] = False


# ==========================================
# HUMAN REVIEW QUEUE
# ==========================================

st.subheader("Review Queue")

if tickets:

    ticket_options = {
        ticket["ticket_id"]: ticket
        for ticket in tickets
    }

    selected_id = st.selectbox(
        "Select a ticket",
        options=list(ticket_options.keys()),
        format_func=lambda ticket_id: (
            f"{ticket_id} | "
            f"{ticket_options[ticket_id]['category']} | "
            f"{ticket_options[ticket_id]['urgency']}"
        ),
    )

    ticket = ticket_options[selected_id]

    st.divider()

    left, right = st.columns([1, 1])

    with left:
        st.subheader("Customer Complaint")
        st.write(ticket["original_complaint"])

        st.subheader("Ticket Details")
        st.write("**Ticket ID:**", ticket["ticket_id"])
        st.write("**Category:**", ticket["category"])
        st.write("**Urgency:**", ticket["urgency"])
        st.write("**Sentiment:**", ticket["sentiment"])
        st.write("**Language:**", ticket["language"])
        st.write("**Ticket Status:**", ticket["ticket_status"])
        st.write(
            "**Escalation Reason:**",
            ticket["escalation_reason"] or "None",
        )

    with right:
        st.subheader("AI Proposed Response")
        st.text_area(
            "Draft response",
            value=ticket["proposed_response"],
            height=260,
            disabled=True,
        )

        st.subheader("Knowledge Base Evidence")

        sources = ticket.get("policy_sources") or []

        if sources:
            for source in sources:
                st.write(f"• {source}")
        else:
            st.warning("No policy sources recorded.")

    st.divider()

    st.subheader("Human Review Decision")

    with st.form(key=f"review_form_{selected_id}"):

        reviewer = st.text_input(
            "Reviewer name",
            placeholder="Enter your name",
        )

        action = st.radio(
            "Review action",
            options=["Approve", "Revise", "Reject"],
            horizontal=True,
        )

        notes = st.text_area(
            "Review notes",
            placeholder="Explain your decision or requested changes",
        )

        submitted = st.form_submit_button(
            "Submit Review",
            type="primary",
        )

    if submitted:
        try:
            result = review_ticket(
                ticket_id=selected_id,
                action=action,
                reviewer=reviewer,
                notes=notes,
            )

            st.success(
                f"Ticket {selected_id} reviewed successfully. "
                f"New review status: {result['review_status']}"
            )

            st.rerun()

        except ValueError as exc:
            st.error(str(exc))

else:
    st.caption(
        "All available tickets have been reviewed. "
        "Check the AI Revision queue below for revision requests."
    )

# ==========================================
# AI-ASSISTED RESPONSE REVISION
# ==========================================

st.divider()
st.header("AI-Assisted Response Revision")

revision_tickets = list_revision_requested_tickets()

st.metric(
    "Tickets Awaiting AI Revision",
    len(revision_tickets),
)

if revision_tickets:

    revision_options = {
        ticket["ticket_id"]: ticket
        for ticket in revision_tickets
    }

    selected_revision_id = st.selectbox(
        "Select a ticket for AI revision",
        options=list(revision_options.keys()),
        format_func=lambda ticket_id: (
            f"{ticket_id} | "
            f"{revision_options[ticket_id]['category']}"
        ),
        key="revision_ticket_selector",
    )

    revision_ticket = revision_options[selected_revision_id]

    st.subheader("Original Customer Complaint")
    st.write(revision_ticket["original_complaint"])

    st.subheader("Current AI Response")
    st.text_area(
        "Existing response",
        value=revision_ticket["proposed_response"],
        height=180,
        disabled=True,
        key="existing_revision_response",
    )

    reviewer_feedback = st.text_area(
        "Reviewer Feedback",
        placeholder=(
            "Explain how the AI response should be improved..."
        ),
        key="ai_revision_feedback",
    )

    if st.button(
        "Generate AI Revision",
        type="primary",
        key="generate_ai_revision",
    ):

        if not reviewer_feedback.strip():
            st.warning("Reviewer feedback is required.")

        else:
            model_client = None

            try:
                with st.spinner(
                    "AutoGen Resolution Agent is generating a revised response..."
                ):

                    async def execute_revision():
                        client = OpenAIChatCompletionClient(
                            model="gpt-4o-mini",
                            api_key=os.environ["OPENAI_API_KEY"],
                        )

                        try:
                            return await run_revision_workflow(
                                ticket_id=selected_revision_id,
                                reviewer_notes=reviewer_feedback,
                                model_client=client,
                            )
                        finally:
                            await client.close()

                    result = asyncio.run(execute_revision())

                st.success(
                    f"Revised response saved for {selected_revision_id}. "
                    "Ticket returned to Pending Human Review."
                )

                st.session_state["last_revision_result"] = result

                st.rerun()

            except Exception as exc:
                st.error(f"AI revision failed: {exc}")

else:
    st.info("No tickets currently require AI revision.")
