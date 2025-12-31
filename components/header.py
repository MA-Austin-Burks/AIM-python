"""Page header component."""

from datetime import datetime

import streamlit as st


def render_page_header() -> None:
    """Render the page header with title and last updated caption."""
    st.set_page_config(page_title="Aspen Investing Menu", layout="wide")

    # Set default sidebar width
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                min-width: 550px;
                max-width: 550px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Aspen Investing Menu")
    st.caption(f"Last updated: {datetime.today().strftime(format='%Y-%m-%d')}")
    st.divider()
