from datetime import datetime

import streamlit as st


def render_page_header():
    st.set_page_config(
        page_title="Aspen Investing Menu",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Permanently visible sidebar with fixed min-width (no collapse)
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                min-width: 500px;
                max-width: 500px;
            }
            /* Hide the collapse button */
            [data-testid="stSidebar"] button[kind="headerNoPadding"] {
                display: none;
            }
            [data-testid="collapsedControl"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Aspen Investing Menu")
    st.caption(f"Last updated: {datetime.today().strftime(format='%Y-%m-%d')}")
    st.divider()
