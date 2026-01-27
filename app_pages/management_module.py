"""Management Module page - manage and update question submissions."""

from datetime import datetime

import streamlit as st

from components import render_footer
from utils.question_submission import (
    delete_question,
    fetch_all_questions,
    update_question_fields,
)

# Status options for questions
STATUS_OPTIONS = ["unanswered", "in_progress", "answered", "archived"]


def format_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return timestamp_str


def get_status_badge(status: str) -> str:
    """Get status badge with appropriate color."""
    status_colors = {
        "unanswered": "🔴",
        "in_progress": "🟡",
        "answered": "🟢",
        "archived": "⚪",
    }
    return f"{status_colors.get(status, '⚪')} {status.replace('_', ' ').title()}"


st.markdown("# :material/admin_panel_settings: Management Module")
st.caption("Manage and update question submissions")

# Fetch questions from S3 (cached, spinner only shows on cache miss)
try:
    all_questions = fetch_all_questions()
except Exception as e:
    st.error(f":material/error: Error loading questions: {str(e)}")
    all_questions = []

if not all_questions:
    st.info(":material/info: No questions found in the system.")
    render_footer()
    st.stop()

# Filter section
st.markdown("### Filters")
col1, col2 = st.columns([1, 3])

with col1:
    status_filter = st.selectbox(
        "Filter by Status:",
        options=["All"] + STATUS_OPTIONS,
        key="status_filter",
    )

# Filter questions based on status
filtered_questions = (
    all_questions
    if status_filter == "All"
    else [q for q in all_questions if q.get("status", "unanswered") == status_filter]
)

# Display summary stats
st.markdown("### Summary")
col1, col2, col3, col4 = st.columns(4)

with col1:
    unanswered_count = len(
        [q for q in all_questions if q.get("status") == "unanswered"]
    )
    st.metric("Unanswered", unanswered_count)

with col2:
    in_progress_count = len(
        [q for q in all_questions if q.get("status") == "in_progress"]
    )
    st.metric("In Progress", in_progress_count)

with col3:
    answered_count = len([q for q in all_questions if q.get("status") == "answered"])
    st.metric("Answered", answered_count)

with col4:
    total_count = len(all_questions)
    st.metric("Total Questions", total_count)

st.markdown("---")

# Display questions
st.markdown(f"### Questions ({len(filtered_questions)} shown)")

if not filtered_questions:
    st.info(f":material/info: No questions found with status '{status_filter}'.")
else:
    # Display each question in an expandable card
    for idx, question in enumerate(filtered_questions):
        with st.container(border=True):
            # Question header with status badge
            current_status = question.get("status", "unanswered")
            status_badge = get_status_badge(current_status)

            col_header1, col_header2 = st.columns([3, 1])

            with col_header1:
                st.markdown(f"**{status_badge}**")
                st.markdown(
                    f"**From:** {question.get('name', 'Unknown')} ({question.get('email', 'No email')})"
                )
                st.markdown(
                    f"**Submitted:** {format_timestamp(question.get('timestamp', ''))}"
                )

            with col_header2:
                # Show existing response if available
                existing_response = question.get("response", "")
                if existing_response:
                    st.markdown("**Response:**")
                    with st.expander("View Response", expanded=False):
                        st.markdown(existing_response)
                        if question.get("response_timestamp"):
                            st.caption(
                                f"Response added: {format_timestamp(question.get('response_timestamp', ''))}"
                            )

            # Question text in expander
            with st.expander("View Question", expanded=False):
                st.markdown(
                    f"**Question:**\n\n{question.get('question', 'No question text')}"
                )

            st.markdown("---")

            # Response and Status Update Section
            st.markdown("#### :material/edit: Add Response & Update Status")

            col_response, col_status = st.columns([2, 1])

            with col_response:
                # Response text area
                response_key = f"response_{question.get('s3_key', idx)}"
                reset_flag_key = f"reset_response_{question.get('s3_key', idx)}"

                # Check if we should reset the form (after successful submit)
                if st.session_state.get(reset_flag_key, False):
                    # Clear the reset flag
                    st.session_state[reset_flag_key] = False
                    # Remove the widget's session state so it resets (use pop to avoid errors)
                    st.session_state.pop(response_key, None)
                    current_response = ""
                else:
                    current_response = st.session_state.get(
                        response_key, existing_response
                    )

                response_text = st.text_area(
                    "Your Response:",
                    value=current_response,
                    height=150,
                    key=response_key,
                    placeholder="Enter your response to this question...",
                    help="This response will be saved to the question record.",
                )

            with col_status:
                # Status update dropdown
                status_key = f"status_select_{question.get('s3_key', idx)}"
                new_status = st.selectbox(
                    "Status:",
                    options=STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(current_status)
                    if current_status in STATUS_OPTIONS
                    else 0,
                    key=status_key,
                )

            # Submit and Delete buttons
            submit_key = f"submit_btn_{question.get('s3_key', idx)}"
            delete_key = f"delete_btn_{question.get('s3_key', idx)}"
            delete_confirm_key = f"delete_confirm_{question.get('s3_key', idx)}"
            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 1, 1, 1])

            with col_btn1:
                if st.button(
                    "💾 Submit",
                    key=submit_key,
                    type="primary",
                    use_container_width=True,
                ):
                    s3_key = question.get("s3_key")
                    if s3_key:
                        # Check if there are changes
                        has_status_change = new_status != current_status
                        has_response_change = (
                            response_text.strip() != existing_response.strip()
                        )

                        if has_status_change or has_response_change:
                            # Update both status and response
                            if update_question_fields(
                                s3_key,
                                status=new_status if has_status_change else None,
                                response=response_text.strip()
                                if response_text.strip()
                                else None,
                            ):
                                st.success("✅ Question updated successfully!")
                                # Set reset flag to clear form on next rerun
                                reset_flag_key = f"reset_response_{s3_key}"
                                st.session_state[reset_flag_key] = True
                                # Cache is already cleared in update_question_fields, just rerun
                                st.rerun()
                            else:
                                st.error(
                                    "❌ Failed to update question. Please try again."
                                )
                        else:
                            st.info("ℹ️ No changes to save.")
                    else:
                        st.error("❌ Invalid question record. Cannot update.")

            with col_btn2:
                # Reset button to reset the form
                if st.button(
                    "🔄 Reset",
                    key=f"reset_btn_{question.get('s3_key', idx)}",
                    use_container_width=True,
                ):
                    # Reset session state for this question
                    if response_key in st.session_state:
                        del st.session_state[response_key]
                    st.rerun()

            with col_btn3:
                # Delete button with confirmation
                s3_key = question.get("s3_key")
                if s3_key:
                    # Check if delete confirmation is in session state
                    if st.session_state.get(delete_confirm_key, False):
                        # Show confirmation buttons
                        col_confirm1, col_confirm2 = st.columns(2)
                        with col_confirm1:
                            if st.button(
                                "✓ Confirm",
                                key=f"confirm_delete_{question.get('s3_key', idx)}",
                                type="primary",
                                use_container_width=True,
                            ):
                                if delete_question(s3_key):
                                    st.success("🗑️ Question deleted successfully!")
                                    # Clear session state
                                    if response_key in st.session_state:
                                        del st.session_state[response_key]
                                    st.session_state[delete_confirm_key] = False
                                    # Cache is already cleared in delete_question, just rerun
                                    st.rerun()
                                else:
                                    st.error(
                                        "❌ Failed to delete question. Please try again."
                                    )
                        with col_confirm2:
                            if st.button(
                                "✗ Cancel",
                                key=f"cancel_delete_{question.get('s3_key', idx)}",
                                use_container_width=True,
                            ):
                                st.session_state[delete_confirm_key] = False
                                st.rerun()
                    else:
                        # Show delete button
                        if st.button(
                            "🗑️ Delete",
                            key=delete_key,
                            type="secondary",
                            use_container_width=True,
                        ):
                            # Set confirmation flag
                            st.session_state[delete_confirm_key] = True
                            st.rerun()

            st.markdown("---")

# Refresh button
if st.button("🔄 Refresh Questions", use_container_width=True):
    fetch_all_questions.clear()
    st.rerun()

# Footer
render_footer()
