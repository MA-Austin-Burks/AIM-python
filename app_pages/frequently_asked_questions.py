"""Frequently Asked Questions page - common questions and answers about the platform."""

from datetime import datetime

import streamlit as st

from components import render_footer

FAQ_UPDATE_DATE = "2026-01-23"


# Demo Q&A data structure (replace with actual content when ready)
DEMO_QUESTIONS = [
    {
        "question": "What is the Aspen Investment Menu?",
        "answer": "The Aspen Investment Menu is a comprehensive platform that provides detailed information about investment strategies, including performance metrics, expense ratios, minimum investments, and allocation details. It helps investment professionals and clients make informed decisions about strategy selection.",
    },
    {
        "question": "How often is the data updated?",
        "answer": "The platform data is updated regularly to ensure accuracy. Specific update frequencies may vary by data type. Please refer to the individual page captions for the most recent update dates.",
    },
    {
        "question": "What do the different series types mean?",
        "answer": "The platform includes several series types: **Market Series** for broad market exposure, **Multifactor Series** for factor-tilted portfolios, and **Income Series** for income-focused strategies. Each series is designed for different investment objectives and risk tolerances. See the 'About the Platform' page for detailed comparisons.",
    },
    {
        "question": "How do I filter strategies?",
        "answer": "Use the filters in the sidebar on the Search page to narrow down strategies by type, series, recommended status, and other criteria. You can combine multiple filters to find strategies that match your specific requirements.",
    },
    {
        "question": "What is the difference between 'Recommended' and 'Recommended & Approved'?",
        "answer": "**Recommended** strategies are those that have been reviewed and recommended by the Investment Committee for consideration. **Recommended & Approved** strategies are a subset of recommended strategies that have received additional approval for specific use cases or client types. When filtering strategies, you can select either option to see strategies matching that status. Currently, the platform shows all recommended strategies when 'Recommended' is selected, and the 'Recommended & Approved' filter option is available for future implementation.",
    },
    {
        "question": "What are strategy minimums and how do they work?",
        "answer": "Strategy minimums refer to the **minimum investment amount** required to invest in a particular strategy. This is displayed as the 'Minimum' value on strategy cards and in search results. When filtering strategies, you can use the 'Current Account Value' filter to show only strategies where your account value meets or exceeds the strategy's minimum investment requirement. This helps ensure you're only viewing strategies that are accessible based on your account size.",
    },
]


st.markdown("# :material/help: Frequently Asked Questions")
st.caption(f"last updated: {FAQ_UPDATE_DATE}")

st.markdown(
    """
    Find answers to common questions about the Aspen Investment Menu platform. 
    Click on any question below to expand and view the answer.
    """
)

# Use bordered container for visual grouping
with st.container(border=True, gap="small"):
    # Render each Q&A as an expander
    for idx, qa in enumerate(DEMO_QUESTIONS):
        with st.expander(
            f"**{qa['question']}**",
            expanded=False,
        ):
            st.markdown(qa["answer"])

# Add a note that content is being drafted
st.info(
    ":material/info: **Note:** This FAQ section is currently being populated with additional questions and answers. "
    "If you have questions not covered here, please use the form below to submit your question."
)

st.markdown("---")

# Submit a Question Section
st.markdown("## :material/question_answer: Submit a Question")

st.markdown(
    """
    Have a question that's not answered above? Submit it here and we'll get back to you 
    or add it to our FAQ section.
    """
)

# Form for submitting questions
with st.form("submit_question_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        submitter_name = st.text_input(
            ":material/person: Your Name",
            placeholder="Enter your name",
            key="submitter_name",
        )
    
    with col2:
        submitter_email = st.text_input(
            ":material/email: Your Email",
            placeholder="your.email@example.com",
            key="submitter_email",
        )
    
    question_text = st.text_area(
        ":material/help_outline: Your Question",
        placeholder="Type your question here...",
        height=150,
        key="question_text",
        help="Please provide as much detail as possible to help us provide a thorough answer.",
    )
    
    submitted = st.form_submit_button(
        ":material/send: Submit Question",
        type="primary",
        use_container_width=True,
    )
    
    if submitted:
        # Validate form inputs
        if not submitter_name or not submitter_name.strip():
            st.error(":material/error: Please enter your name.")
        elif not submitter_email or not submitter_email.strip():
            st.error(":material/error: Please enter your email address.")
        elif "@" not in submitter_email:
            st.error(":material/error: Please enter a valid email address.")
        elif not question_text or not question_text.strip():
            st.error(":material/error: Please enter your question.")
        else:
            # Store question data in session state (for now)
            # In production, this would be sent to a backend service
            if "submitted_questions" not in st.session_state:
                st.session_state.submitted_questions = []
            
            question_data = {
                "name": submitter_name.strip(),
                "email": submitter_email.strip(),
                "question": question_text.strip(),
                "timestamp": datetime.now().isoformat(),
            }
            
            st.session_state.submitted_questions.append(question_data)
            # Store the most recent submission for display
            st.session_state.last_submitted_question = question_data
            
            # Show success message
            st.success(
                ":material/check_circle: **Thank you!** Your question has been submitted. "
                "We'll review it and get back to you soon."
            )
            
            # Note: In production, this data would be sent to AWS/backend here
            # See implementation options below

# Display submitted question JSON if available
if "last_submitted_question" in st.session_state:
    st.markdown("---")
    st.markdown("### :material/code: Submitted Question Data")
    st.json(st.session_state.last_submitted_question)

# Footer
render_footer()
