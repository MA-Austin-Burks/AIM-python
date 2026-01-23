"""Frequently Asked Questions page - common questions and answers about the platform."""

from datetime import datetime

import streamlit as st

from components import render_footer
from utils.question_submission import submit_question_to_s3

FAQ_UPDATE_DATE = "2026-01-23"


@st.cache_data  # Cache static FAQ data (never changes during runtime)
def _get_faq_questions():
    """Get FAQ questions list (cached for performance)."""
    return [
    {
        "question": "What is the Aspen Investing Menu?",
        "answer": "The Aspen Investing Menu is a comprehensive platform that provides detailed information about investment strategies, including performance metrics, expense ratios, minimum investments, and allocation details. It helps investment professionals and clients make informed decisions about strategy selection.",
    },
    {
        "question": "How often is the data updated?",
        "answer": "The platform data is updated regularly to ensure accuracy. Specific update frequencies may vary by data type. Please refer to the individual page captions for the most recent update dates.",
    },
    {
        "question": "What do the different series types mean?",
        "answer": "The platform includes several series types: Market Series for broad market exposure, Multifactor Series for factor-tilted portfolios, and Income Series for income-focused strategies. Each series is designed for different investment objectives and risk tolerances. See the 'About the Platform' page for detailed comparisons.",
    },
    {
        "question": "How do I filter strategies?",
        "answer": "Use the filters in the sidebar on the Search page to narrow down strategies by type, series, recommended status, and other criteria. You can combine multiple filters to find strategies that match your specific requirements.",
    },
    {
        "question": "What is the difference between an approved strategy and a recommended strategy?",
        "answer": "Recommended strategies represent the Investment Committee's best thinking. They adhere to Mercer's investment philosophy and asset allocation framework for a given set of investment objectives.\n\nIn some situations, because of a client's specific goals or preferences, our recommended strategies may not be a good fit, and approved strategies may be more appropriate. Approved strategies deviate from our investment philosophy in some way. For example, approved strategies may target a single asset class (Asset Class strategies) or specifically exclude an asset class (US Only strategies) or otherwise stray from our asset allocation framework. Of course, all approved strategies are subject to the same rigorous due diligence and monitoring as recommended strategies.\n\nBy default, Aspen Investing Menu search results will only include recommended strategies. However, any search can be expanded to also include approved strategies.",
    },
    {
        "question": "How are sleeve strategy minimums set?",
        "answer": "Our sleeve strategy minimums provide the minimum investment required to fully invest in a strategy. The calculation of a sleeve strategy minimum considers our minimum trade size, the prices of any market-traded securities targeted in the strategy, and the investment minimums of any targeted SMA strategies. Sleeve strategy minimums also include a small buffer to prevent frequent changes in a strategy's minimum due to market movement.",
    },
    ]


# Demo Q&A data structure (replace with actual content when ready)
DEMO_QUESTIONS = _get_faq_questions()


st.markdown("# :material/help: Aspen Investing Menu – FAQs")
st.caption(f"last updated: {FAQ_UPDATE_DATE}")

st.markdown(
    """
    Find answers to common questions about the Aspen Investing Menu platform. 
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
            # Prepare question data with status field
            question_data = {
                "name": submitter_name.strip(),
                "email": submitter_email.strip(),
                "question": question_text.strip(),
                "timestamp": datetime.now().isoformat(),
                "status": "unanswered",  # Default status for easier tracking
            }
            
            # Submit to S3
            if submit_question_to_s3(question_data):
                # Store in session state for display (optional)
                if "submitted_questions" not in st.session_state:
                    st.session_state.submitted_questions = []
                
                st.session_state.submitted_questions.append(question_data)
                st.session_state.last_submitted_question = question_data
                
                # Show success message
                st.success(
                    ":material/check_circle: **Thank you!** Your question has been submitted. "
                    "We'll review it and get back to you soon."
                )
            else:
                st.error(
                    ":material/error: **Submission failed.** Please try again later or contact support."
                )

# Footer
render_footer()
