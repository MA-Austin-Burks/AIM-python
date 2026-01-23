"""Frequently Asked Questions page - common questions and answers about the platform."""

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
    "If you have questions not covered here, please contact the platform administrator."
)

# Footer
render_footer()
