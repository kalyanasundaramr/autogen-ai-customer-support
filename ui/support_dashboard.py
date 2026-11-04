
import asyncio
import os

from autogen_ext.models.openai import OpenAIChatCompletionClient
from services.support_service import process_customer_complaint

from services.human_review_agent_service import (
    collect_human_review,
)
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from services.ticket_service import get_ticket

from services.ticket_lifecycle_service import (
    ALLOWED_TRANSITIONS,
    TicketLifecycleError,
    update_ticket_status,
)

from services.delivery_persistence_service import (
    save_simulated_delivery,
    DuplicateDeliveryError,
)
from services.review_service import review_ticket
from workflows.revision_workflow import run_revision_workflow

import json

from services.ticket_audit_query_service import (
    list_ticket_audit_history,
)
from services.delivery_query_service import (
    list_delivery_history,
)
from services.ticket_export_service import (
    export_tickets_csv,
)

# --------------------------------------------------
# Project setup
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

from database.db import initialize_database
from services.ticket_query_service import (
    list_all_tickets,
    list_pending_review_tickets,
    list_revision_requested_tickets,
)

st.set_page_config(
    page_title="AI Customer Support Desk",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

initialize_database()

# --------------------------------------------------
# Dashboard styling
# --------------------------------------------------

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        max-width: 1500px;
    }

    h1, h2, h3 {
        letter-spacing: -0.025em;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,0.20);
        border-radius: 12px;
        padding: 16px;
    }

    button[data-baseweb="tab"] {
        font-weight: 600;
        padding: 12px 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("🎧 AI Customer Support Desk")
st.caption(
    "AutoGen Multi-Agent Support Automation | "
    "FAISS RAG | Human-in-the-Loop"
)

st.divider()

# --------------------------------------------------
# Load ticket statistics
# --------------------------------------------------

tickets = list_all_tickets()
pending_reviews = list_pending_review_tickets()
revision_requests = list_revision_requested_tickets()

total = len(tickets)

pending = sum(
    t["ticket_status"] == "Pending"
    for t in tickets
)

escalated = sum(
    t["ticket_status"] == "Escalated"
    for t in tickets
)

resolved = sum(
    t["ticket_status"] == "Resolved"
    for t in tickets
)

closed = sum(
    t["ticket_status"] == "Closed"
    for t in tickets
)

# --------------------------------------------------
# Main navigation
# --------------------------------------------------

tab_dashboard, tab_complaint, tab_tickets, tab_review, tab_audit = st.tabs(
    [
        "📊 Dashboard",
        "📝 New Complaint",
        "🎫 Tickets",
        "👤 Human Review",
        "📋 Audit & Reports",
    ]
)

with tab_dashboard:
    st.subheader("Support Operations Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Tickets", total)
    col2.metric("Pending", pending)
    col3.metric("Escalated", escalated)
    col4.metric("Resolved", resolved)
    col5.metric("Closed", closed)

    st.divider()

    col1, col2 = st.columns(2)

    col1.metric("Awaiting Human Review", len(pending_reviews))
    col2.metric("AI Revisions Requested", len(revision_requests))

    st.subheader("Recent Support Tickets")

    if tickets:
        rows = [
            {
                "Ticket ID": t["ticket_id"],
                "Category": t["category"],
                "Urgency": t["urgency"],
                "Ticket Status": t["ticket_status"],
                "Review Status": t["review_status"],
            }
            for t in tickets
        ]

        st.dataframe(
            rows[:10],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No support tickets found.")


with tab_complaint:
    st.subheader("Submit a Customer Complaint")
    st.caption(
        "AI-powered complaint analysis using four AutoGen agents."
    )

    with st.form("new_complaint_form", clear_on_submit=False):
        complaint = st.text_area(
            "Customer Complaint",
            placeholder=(
                "Example: My order is delayed beyond the "
                "estimated delivery date. Can you help?"
            ),
            height=150,
        )

        submitted = st.form_submit_button(
            "Process Complaint",
            type="primary",
        )

    if submitted:
        if not complaint.strip():
            st.warning("Please enter a customer complaint.")

        elif not os.getenv("OPENAI_API_KEY"):
            st.error("OPENAI_API_KEY is missing.")

        else:
            async def execute_workflow():
                client = OpenAIChatCompletionClient(
                    model="gpt-4o-mini",
                    api_key=os.environ["OPENAI_API_KEY"],
                )
                try:
                    return await process_customer_complaint(
                        complaint=complaint.strip(),
                        model_client=client,
                    )
                finally:
                    await client.close()

            try:
                with st.spinner(
                    "Processing complaint through AutoGen agents..."
                ):
                    result = asyncio.run(execute_workflow())

                st.session_state["latest_complaint_result"] = result
                st.rerun()

                st.success(
                    f"Ticket {result['ticket_id']} created successfully."
                )

            except Exception as exc:
                st.error(f"Complaint processing failed: {exc}")

    result = st.session_state.get("latest_complaint_result")

    if result:
        ticket = result["ticket"]

        st.divider()

        st.success("Complaint registered successfully!")

        col_ticket, col_review = st.columns([2, 1])

        with col_ticket:
            st.metric(
                "Ticket ID",
                result["ticket_id"],
            )

        with col_review:
            st.metric(
                "Review Status",
                ticket.get("review_status") or "Pending",
            )

        st.caption(
            "Please keep this Ticket ID for tracking "
            "your complaint."
        )

        st.subheader("AI Processing Results")

        st.markdown("#### Agent Execution")

        agent_labels = {
            "customer_query_agent": "Query Agent",
            "knowledge_base_agent": "Knowledge Agent",
            "resolution_agent": "Resolution Agent",
            "log_agent": "Log Agent",
        }

        execution_order = result.get("execution_order", [])

        agent_columns = st.columns(4)

        for index, agent_name in enumerate(execution_order[:4]):
            with agent_columns[index]:
                st.success(
                    f"✓ {agent_labels.get(agent_name, agent_name)}"
                )

        col1, col2, col3 = st.columns(3)
        col1.metric("Category", ticket["category"])
        col2.metric("Urgency", ticket["urgency"])
        col3.metric("Ticket Status", ticket["ticket_status"])

        st.write(
            "**Escalation Reason:**",
            ticket.get("escalation_reason") or "None",
        )

        confidence = ticket.get("confidence_score")

        if (
            isinstance(confidence, (int, float))
            and not isinstance(confidence, bool)
        ):
            st.metric("AI Confidence", f"{confidence:.2f}")
        else:
            st.warning("AI confidence unavailable.")

        st.write(
            ticket.get("confidence_explanation")
            or "No confidence explanation available."
        )

        st.markdown("#### Proposed Customer Response")
        
        st.text_area(
        "AI-generated draft",
        value=ticket["proposed_response"],
        height=230,
        disabled=False,
        key=f"ai_response_{ticket['ticket_id']}",
        help="AI-generated draft for review. Editing this field does not save changes to the ticket.",
    )

        st.markdown("#### Knowledge Base Evidence")

        sources = ticket.get("policy_sources") or []
        if sources:
            for source in sources:
                st.write(f"- {source}")
        else:
            st.warning("No supporting policy sources found.")

        st.info(
            "This response is a draft. "
            "Human approval is required before delivery."
        )



with tab_tickets:
    st.subheader("Support Ticket Management")
    st.caption(
        "Search and inspect customer support tickets."
    )

    search_id = st.text_input(
        "Search Ticket ID",
        placeholder="Example: TKT-000016",
        key="ticket_search",
    )

    filtered_tickets = [
        ticket for ticket in tickets
        if search_id.strip().lower()
        in ticket["ticket_id"].lower()
    ]

    if filtered_tickets:
        st.dataframe(
            [
                {
                    "Ticket ID": t["ticket_id"],
                    "Category": t["category"],
                    "Urgency": t["urgency"],
                    "Ticket Status": t["ticket_status"],
                    "Review Status": t["review_status"],
                }
                for t in filtered_tickets
            ],
            use_container_width=True,
            hide_index=True,
        )

        ticket_options = {
            t["ticket_id"]: t
            for t in filtered_tickets
        }

        # Automatically select the latest ticket when a new one appears.
        ticket_ids = list(ticket_options.keys())

        # Find the newest standard ticket ID.
        # Ignore nonnumeric test IDs when determining the latest ticket.
        numeric_ticket_ids = [
            ticket_id
            for ticket_id in ticket_ids
            if ticket_id.rsplit("-", 1)[-1].isdigit()
        ]

        if numeric_ticket_ids:
            latest_ticket_id = max(
                numeric_ticket_ids,
                key=lambda ticket_id: int(
                    ticket_id.rsplit("-", 1)[-1]
                ),
            )
        else:
            # Fall back safely if only test IDs exist.
            latest_ticket_id = ticket_ids[0]

        previous_latest = st.session_state.get(
            "ticket_management_latest_seen"
        )

        if previous_latest != latest_ticket_id:
            st.session_state["ticket_management_selector"] = latest_ticket_id
            st.session_state["ticket_management_latest_seen"] = latest_ticket_id

        elif (
            st.session_state.get("ticket_management_selector")
            not in ticket_ids
        ):
            st.session_state["ticket_management_selector"] = latest_ticket_id

        selected_id = st.selectbox(
            "Select Ticket",
            options=ticket_ids,
            key="ticket_management_selector",
        )

        selected_ticket = get_ticket(selected_id)

        if selected_ticket:
            st.divider()
            st.subheader(f"Ticket Details — {selected_id}")

            left, right = st.columns(2)

            with left:
                st.markdown("#### Customer Complaint")
                st.write(
                    selected_ticket["original_complaint"]
                )

                st.markdown("#### Classification")
                st.write(
                    "**Category:**",
                    selected_ticket["category"],
                )
                st.write(
                    "**Urgency:**",
                    selected_ticket["urgency"],
                )
                st.write(
                    "**Sentiment:**",
                    selected_ticket["sentiment"],
                )
                st.write(
                    "**Language:**",
                    selected_ticket["language"],
                )

            with right:
                st.markdown("#### Workflow Status")
                st.write(
                    "**Ticket Status:**",
                    selected_ticket["ticket_status"],
                )
                st.write(
                    "**Review Status:**",
                    selected_ticket["review_status"],
                )
                st.write(
                    "**Escalation Reason:**",
                    selected_ticket.get("escalation_reason")
                    or "None",
                )

                st.markdown("#### AI Proposed Response")
                st.text_area(
                    "Customer Response",
                    value=selected_ticket["proposed_response"],
                    height=220,
                    disabled=True,
                    key=f"ticket_response_{selected_id}",
                )

            st.markdown("#### Knowledge Base Evidence")

            sources = selected_ticket.get(
                "policy_sources"
            ) or []

            if sources:
                for source in sources:
                    st.write(f"- {source}")
            else:
                st.warning(
                    "No supporting policy sources found."
                )

            st.info(
                "Ticket status and human review status "
                "are tracked separately."
            )
            st.divider()
            st.subheader("Ticket Lifecycle Management")

            current_status = selected_ticket["ticket_status"]

            allowed_statuses = sorted(
                ALLOWED_TRANSITIONS.get(current_status, set())
            )

            st.write("**Current Status:**", current_status)

            if not allowed_statuses:
                st.info(
                    "No further status transitions are available."
                )
            else:
                with st.form(
                    key=f"status_form_{selected_id}"
                ):
                    new_status = st.selectbox(
                        "New Ticket Status",
                        options=allowed_statuses,
                    )

                    operator = st.text_input(
                        "Operator Name",
                        placeholder="Enter reviewer or operator name",
                    )

                    reason = st.text_area(
                        "Reason for Status Change",
                        placeholder="Explain the status change",
                    )

                    st.warning(
                        "Only mark a ticket Resolved when the "
                        "customer's issue has actually been resolved. "
                        "Human approval or simulated delivery alone "
                        "does not establish resolution."
                    )

                    update_clicked = st.form_submit_button(
                        "Update Ticket Status",
                        type="primary",
                    )

                if update_clicked:
                    if not operator.strip():
                        st.error("Operator name is required.")
                    elif not reason.strip():
                        st.error("Reason is required.")
                    else:
                        try:
                            result = update_ticket_status(
                                ticket_id=selected_id,
                                new_status=new_status,
                                performed_by=operator.strip(),
                                reason=reason.strip(),
                            )

                            st.session_state["lifecycle_notice"] = (
                                f"Ticket {selected_id}: "
                                f"{result['previous_status']} → "
                                f"{result['new_status']}"
                            )
                            st.rerun()

                        except TicketLifecycleError as exc:
                            st.error(str(exc))
                        except Exception:
                            st.error(
                                "Status update failed. "
                                "Check application logs."
                            )

            if "lifecycle_notice" in st.session_state:
                st.success(
                    st.session_state.pop("lifecycle_notice")
            )
            st.divider()
            st.subheader("Customer Response Delivery")

            if "delivery_notice" in st.session_state:
                st.success(
                    st.session_state.pop("delivery_notice")
                )

            if selected_ticket["review_status"] == "Approved":
                st.success(
                    "Human review completed. "
                    "Customer response is approved."
                )

                if st.button(
                    "Simulate Customer Response Delivery",
                    key=f"deliver_{selected_id}",
                    type="primary",
                ):
                    try:
                        receipt = save_simulated_delivery(
                            selected_id
                        )

                        st.session_state["delivery_notice"] = (
                            "Delivery simulated successfully. "
                            f"Receipt: {receipt['delivery_id']}"
                        )
                        st.rerun()

                    except DuplicateDeliveryError as exc:
                        st.warning(str(exc))

                    except ValueError as exc:
                        st.error(str(exc))

                    except Exception:
                        st.error(
                            "Delivery simulation failed. "
                            "Check application logs."
                        )

            else:
                st.warning(
                    "Human approval is required "
                    "before delivery."
                )

            st.caption(
                "Simulation only. No actual customer "
                "message is sent."
            )



    else:
        st.info("No matching tickets found.")



with tab_review:
    st.subheader("Human Review & AI Revision")
    st.caption(
        "Review AI-generated responses before customer delivery."
    )

    st.metric("Awaiting Human Review", len(pending_reviews))

    if not pending_reviews:
        st.info(
            "No tickets are currently awaiting human review."
        )

    else:
        review_options = {
            t["ticket_id"]: t
            for t in pending_reviews
        }

        # Preserve the current queue order.
        current_review_ids = list(review_options.keys())

        # Detect tickets newly added to the pending review queue.
        previous_review_ids = st.session_state.get(
            "previous_review_ids"
        )

        if previous_review_ids is not None:
            new_review_ids = [
                ticket_id
                for ticket_id in current_review_ids
                if ticket_id not in previous_review_ids
            ]

            if new_review_ids:
                # Select the newest newly detected ticket.
                st.session_state["human_review_selector"] = new_review_ids[-1]

        # Save the queue snapshot for the next rerun.
        st.session_state["previous_review_ids"] = current_review_ids

        # Ensure the current selection is still valid.
        if (
            st.session_state.get("human_review_selector")
            not in current_review_ids
        ):
            st.session_state["human_review_selector"] = (
                current_review_ids[0]
            )

        review_id = st.selectbox(
            "Select Ticket for Review",
            options=current_review_ids,
            format_func=lambda ticket_id: (
                f"{ticket_id} | "
                f"{review_options[ticket_id]['category']} | "
                f"{review_options[ticket_id]['urgency']}"
            ),
            key="human_review_selector",
        )

        review_ticket_data = review_options[review_id]

        left, right = st.columns(2)

        with left:
            st.markdown("#### Customer Complaint")
            st.write(
                review_ticket_data["original_complaint"]
            )

            st.markdown("#### Ticket Classification")
            st.write(
                "**Category:**",
                review_ticket_data["category"],
            )
            st.write(
                "**Urgency:**",
                review_ticket_data["urgency"],
            )
            st.write(
                "**Sentiment:**",
                review_ticket_data["sentiment"],
            )
            st.write(
                "**Ticket Status:**",
                review_ticket_data["ticket_status"],
            )

        with right:
            st.markdown("#### AI Proposed Response")

            st.text_area(
                "AI-generated draft",
                value=review_ticket_data["proposed_response"],
                height=240,
                disabled=True,
                key=f"review_response_{review_id}",
            )

            st.markdown("#### Knowledge Base Evidence")

            sources = (
                review_ticket_data.get("policy_sources") or []
            )

            if sources:
                for source in sources:
                    st.write(f"- {source}")
            else:
                st.warning(
                    "No supporting policy sources recorded."
                )

        st.divider()
        st.markdown("#### Human Review Decision")

        with st.form(
            key=f"human_review_form_{review_id}"
        ):
            reviewer = st.text_input(
                "Reviewer Name",
                placeholder="Enter reviewer name",
            )

            action = st.radio(
                "Review Action",
                ["Approve", "Revise", "Reject"],
                horizontal=True,
            )

            notes = st.text_area(
                "Review Notes",
                placeholder=(
                    "Explain your decision or "
                    "requested improvements."
                ),
            )

            submit_review = st.form_submit_button(
                "Submit Review Decision",
                type="primary",
            )

        
        if submit_review:
            if not reviewer.strip():
                st.error("Reviewer name is required.")

            elif action in ("Revise", "Reject") and not notes.strip():
                st.error(
                    "Review notes are required for revision or rejection."
                )

            else:
                try:
                    with st.spinner(
                        "UserProxyAgent is processing the human review..."
                    ):
                        agent_decision = asyncio.run(
                            collect_human_review(
                                reviewer=reviewer.strip(),
                                action=action,
                                notes=notes.strip(),
                            )
                        )

                    result = review_ticket(
                        ticket_id=review_id,
                        action=agent_decision["action"],
                        reviewer=agent_decision["reviewer"],
                        notes=agent_decision["notes"],
                    )

                    st.session_state["review_notice"] = (
                        f"Ticket {review_id}: "
                        f"{result['review_status']} "
                        f"(via UserProxyAgent)"
                    )

                    st.rerun()

                except ValueError as exc:
                    st.error(str(exc))

                except Exception as exc:
                    st.error(
                        f"Human review processing failed: {exc}"
                    )


    if "review_notice" in st.session_state:
        st.success(
            st.session_state.pop("review_notice")
        )


    st.divider()
    st.subheader("AI-Assisted Response Revision")

    revision_requests = list_revision_requested_tickets()

    st.metric(
        "Awaiting AI Revision",
        len(revision_requests),
    )

    if revision_requests:
        revision_options = {
            t["ticket_id"]: t
            for t in revision_requests
        }

        revision_id = st.selectbox(
            "Select Ticket for AI Revision",
            options=list(revision_options.keys()),
            key="ai_revision_selector",
        )

        revision_ticket = revision_options[revision_id]

        st.markdown("#### Original Complaint")
        st.write(revision_ticket["original_complaint"])

        st.markdown("#### Current AI Response")
        st.text_area(
            "Existing AI Response",
            value=revision_ticket["proposed_response"],
            height=200,
            disabled=True,
            key=f"existing_response_{revision_id}",
        )

        reviewer_feedback = st.text_area(
            "Revision Instructions",
            placeholder=(
                "Describe how the AI response "
                "should be improved."
            ),
            key=f"revision_feedback_{revision_id}",
        )

        if st.button(
            "Generate Revised AI Response",
            type="primary",
            key=f"generate_revision_{revision_id}",
        ):
            if not reviewer_feedback.strip():
                st.warning(
                    "Revision instructions are required."
                )

            elif not os.getenv("OPENAI_API_KEY"):
                st.error("OPENAI_API_KEY is missing.")

            else:
                async def execute_revision():
                    client = OpenAIChatCompletionClient(
                        model="gpt-4o-mini",
                        api_key=os.environ["OPENAI_API_KEY"],
                    )
                    try:
                        return await run_revision_workflow(
                            ticket_id=revision_id,
                            reviewer_notes=reviewer_feedback.strip(),
                            model_client=client,
                        )
                    finally:
                        await client.close()

                try:
                    with st.spinner(
                        "Generating revised AI response..."
                    ):
                        result = asyncio.run(
                            execute_revision()
                        )

                    st.session_state["revision_notice"] = (
                        f"Revised response saved for {revision_id}. "
                        "Ticket returned to Pending Human Review."
                    )

                    st.rerun()

                except Exception as exc:
                    st.error(
                        f"AI revision failed: {exc}"
                    )

    else:
        st.info(
            "No tickets currently require AI revision."
        )

    if "revision_notice" in st.session_state:
        st.success(
            st.session_state.pop("revision_notice")
        )


with tab_audit:
    st.subheader("Audit & Reports")
    st.caption(
        "Ticket history, human review decisions, "
        "AI revisions, and simulated delivery records."
    )

    st.download_button(
        label="Download All Tickets (CSV)",
        data=export_tickets_csv().encode("utf-8-sig"),
        file_name="customer_support_tickets.csv",
        mime="text/csv",
        key="dashboard_csv_export",
    )

    st.divider()

    if not tickets:
        st.info("No tickets available.")
    else:
        audit_id = st.selectbox(
            "Select Ticket for Audit",
            options=[t["ticket_id"] for t in tickets],
            key="audit_ticket_selector",
        )

        audit_events = list_ticket_audit_history(audit_id)
        deliveries = list_delivery_history(audit_id)

        col1, col2 = st.columns(2)
        col1.metric("Audit Events", len(audit_events))
        col2.metric("Delivery Records", len(deliveries))

        st.markdown("#### Ticket Audit Trail")

        action_labels = {
            "REVIEW_APPROVE": "Human Review - Approved",
            "REVIEW_REVISE": "Human Review - Revision Requested",
            "REVIEW_REJECT": "Human Review - Rejected",
            "AI_RESPONSE_REVISED": "AI Response Revised",
            "DELIVERY_SIMULATED": "Delivery Simulated",
            "TICKET_STATUS_CHANGED": "Ticket Status Changed",
        }

        if audit_events:
            for index, event in enumerate(audit_events):
                action = event["action"]
                label = action_labels.get(
                    action,
                    action.replace("_", " ").title(),
                )

                with st.expander(
                    f"{label} | {event['created_at']}",
                    expanded=False,
                ):
                    st.write(
                        "**Performed By:**",
                        event.get("performed_by") or "Not recorded",
                    )
                    st.write(
                        "**Previous Value:**",
                        event.get("previous_value") or "N/A",
                    )
                    st.write(
                        "**New Value / Details:**",
                        event.get("new_value") or "N/A",
                    )

            st.download_button(
                label="Export Audit History (JSON)",
                data=json.dumps(
                    audit_events,
                    indent=2,
                    default=str,
                ),
                file_name=f"{audit_id}_audit_history.json",
                mime="application/json",
                key=f"audit_export_{audit_id}",
            )
        else:
            st.info("No audit events recorded.")

        st.divider()
        st.markdown("#### Customer Response Delivery History")

        if deliveries:
            for delivery in deliveries:
                with st.expander(
                    f"{delivery['delivery_id']} | "
                    f"{delivery['delivery_status']}"
                ):
                    st.write(
                        "**Delivery Mode:**",
                        delivery["delivery_mode"],
                    )
                    st.write(
                        "**Channel:**",
                        delivery["channel"],
                    )
                    st.write(
                        "**Timestamp:**",
                        delivery["delivered_at"],
                    )
                    st.write(
                        "**Actual Message Sent:**",
                        "Yes" if delivery["actual_message_sent"]
                        else "No",
                    )

                    st.text_area(
                        "Recorded Customer Response",
                        value=delivery["response"],
                        height=180,
                        disabled=True,
                        key=f"delivery_response_{delivery['delivery_id']}",
                    )
        else:
            st.info(
                "No simulated delivery records for this ticket."
            )

        st.caption(
            "Delivery records may be simulated. "
            "A simulated delivery does not mean "
            "an actual customer message was sent."
        )
