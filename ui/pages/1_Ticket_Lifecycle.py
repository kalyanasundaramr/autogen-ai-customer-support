
import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from database.db import initialize_database
from services.ticket_query_service import list_all_tickets
from services.ticket_export_service import export_tickets_csv
from services.delivery_query_service import list_delivery_history
from services.ticket_lifecycle_service import (
    ALLOWED_TRANSITIONS,
    TicketLifecycleError,
    update_ticket_status,
)
from services.ticket_audit_query_service import list_ticket_audit_history


st.set_page_config(
    page_title="Ticket Lifecycle | AI Customer Support",
    page_icon="📊",
    layout="wide",
)

initialize_database()

st.title("Ticket Lifecycle Dashboard")
st.caption("AutoGen AI Customer Support Automation")

tickets = list_all_tickets()

# ------------------------------------------
# Lifecycle statistics
# ------------------------------------------

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

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Tickets", total)
col2.metric("Pending", pending)
col3.metric("Escalated", escalated)
col4.metric("Resolved", resolved)
col5.metric("Closed", closed)

st.divider()

# ------------------------------------------
# Ticket table
# ------------------------------------------

st.subheader("All Support Tickets")

if not tickets:
    st.info("No support tickets found.")
    st.stop()

table_data = []

for ticket in tickets:
    table_data.append({
        "Ticket ID": ticket["ticket_id"],
        "Category": ticket["category"],
        "Urgency": ticket["urgency"],
        "Sentiment": ticket["sentiment"],
        "Ticket Status": ticket["ticket_status"],
        "Review Status": ticket["review_status"],
    })


st.dataframe(
    table_data,
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    label="Download Ticket Log (CSV)",
    data=export_tickets_csv().encode("utf-8-sig"),
    file_name="customer_support_tickets.csv",
    mime="text/csv",
    key="download_ticket_log_csv",
)

st.divider()


# ------------------------------------------
# Ticket details
# ------------------------------------------

st.subheader("Ticket Details")

ticket_options = {
    ticket["ticket_id"]: ticket
    for ticket in tickets
}

selected_id = st.selectbox(
    "Select a ticket",
    options=list(ticket_options.keys()),
)

ticket = ticket_options[selected_id]

left, right = st.columns(2)

with left:
    st.markdown("#### Customer Complaint")
    st.write(ticket["original_complaint"])

    st.markdown("#### Classification")
    st.write("**Category:**", ticket["category"])
    st.write("**Urgency:**", ticket["urgency"])
    st.write("**Sentiment:**", ticket["sentiment"])
    st.write("**Language:**", ticket["language"])

with right:
    st.markdown("#### Workflow Status")
    st.write("**Ticket Status:**", ticket["ticket_status"])
    st.write("**Review Status:**", ticket["review_status"])

    st.markdown("#### AI Response")
    st.text_area(
        "Customer response",
        value=ticket["proposed_response"],
        height=240,
        disabled=True,
    )

st.info(
    "This dashboard is read-only. "
    "Ticket lifecycle changes will be added in a later step."
)

# ------------------------------------------
# Delivery history
# ------------------------------------------

st.divider()
st.subheader("Delivery History")

deliveries = list_delivery_history(selected_id)

if not deliveries:
    st.info("No delivery history found for this ticket.")

else:
    st.caption(
        f"{len(deliveries)} delivery record(s) "
        f"found for {selected_id}"
    )

    for delivery in deliveries:
        with st.expander(
            f"{delivery['delivery_id']} | "
            f"{delivery['delivery_status']}",
            expanded=True,
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    "**Delivery ID:**",
                    delivery["delivery_id"],
                )
                st.write(
                    "**Mode:**",
                    delivery["delivery_mode"],
                )
                st.write(
                    "**Channel:**",
                    delivery["channel"],
                )

            with col2:
                st.write(
                    "**Status:**",
                    delivery["delivery_status"],
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

            if delivery["actual_message_sent"]:
                st.success("Message marked as sent.")
            else:
                st.warning(
                    "Simulation only. No actual "
                    "customer message was sent."
                )

            st.text_area(
                "Recorded Customer Response",
                value=delivery["response"],
                height=200,
                disabled=True,
                key=f"delivery_{delivery['delivery_id']}",
            )

# ------------------------------------------
# Ticket lifecycle management
# ------------------------------------------

st.divider()
st.subheader("Ticket Status Management")

st.caption(
    "Status changes are validated and recorded "
    "in the ticket audit history."
)

current_status = ticket["ticket_status"]

allowed_statuses = sorted(
    ALLOWED_TRANSITIONS.get(current_status, set())
)

st.write("**Current Status:**", current_status)

if not allowed_statuses:
    st.info(
        "No further status transitions are available "
        "for this ticket."
    )

else:
    with st.form(
        key=f"lifecycle_form_{selected_id}"
    ):
        new_status = st.selectbox(
            "New Ticket Status",
            options=allowed_statuses,
        )

        performed_by = st.text_input(
            "Performed By",
            placeholder="Enter operator name",
        )

        reason = st.text_area(
            "Reason for Status Change",
            placeholder=(
                "Describe why this status "
                "change is appropriate."
            ),
        )

        st.warning(
            "Only mark a ticket Resolved when the "
            "customer's issue has actually been "
            "resolved. Approval or simulated delivery "
            "alone does not prove resolution."
        )

        submitted = st.form_submit_button(
            "Update Ticket Status",
            type="primary",
        )

    if submitted:
        if not performed_by.strip():
            st.error("Operator name is required.")

        elif not reason.strip():
            st.error("Reason is required.")

        else:
            try:
                result = update_ticket_status(
                    ticket_id=selected_id,
                    new_status=new_status,
                    performed_by=performed_by,
                    reason=reason,
                )

                st.success(
                    f"Ticket {result['ticket_id']} "
                    f"updated: "
                    f"{result['previous_status']} → "
                    f"{result['new_status']}"
                )

                st.rerun()

            except TicketLifecycleError as error:
                st.error(str(error))

            except Exception:
                st.error(
                    "Ticket status update failed. "
                    "Check the application logs."
                )

# ------------------------------------------
# Ticket audit trail
# ------------------------------------------

st.divider()
st.subheader("Ticket Audit Trail")

st.caption(
    "Chronological record of ticket actions, "
    "human reviews, AI revisions, simulated "
    "deliveries, and lifecycle changes."
)

audit_events = list_ticket_audit_history(selected_id)

if not audit_events:
    st.info("No audit events found for this ticket.")

else:
    st.metric("Total Audit Events", len(audit_events))

    action_labels = {
        "REVIEW_APPROVE": "Human Review - Approved",
        "REVIEW_REVISE": "Human Review - Revision Requested",
        "REVIEW_REJECT": "Human Review - Rejected",
        "AI_RESPONSE_REVISED": "AI Response Revised",
        "DELIVERY_SIMULATED": "Delivery Simulated",
        "TICKET_STATUS_CHANGED": "Ticket Status Changed",
    }

    for event in audit_events:
        action = event["action"]

        label = action_labels.get(
            action,
            action.replace("_", " ").title(),
        )

        with st.expander(
            f"{label} | {event['created_at']}",
            expanded=False,
        ):
            st.write("**Action:**", action)
            st.write(
                "**Performed By:**",
                event["performed_by"] or "Not recorded",
            )
            st.write(
                "**Timestamp:**",
                event["created_at"],
            )

            st.markdown("**Previous Value**")
            st.code(
                str(event["previous_value"] or "N/A"),
                language=None,
            )

            st.markdown("**New Value / Details**")
            st.code(
                str(event["new_value"] or "N/A"),
                language=None,
            )

    st.download_button(
        label="Export Audit History (JSON)",
        data=__import__("json").dumps(
            audit_events,
            indent=2,
            default=str,
        ),
        file_name=f"{selected_id}_audit_history.json",
        mime="application/json",
        key=f"export_audit_{selected_id}",
    )
