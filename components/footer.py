"""Footer component for the Aspen Investing Menu app."""

import streamlit as st
from streamlit_extras.bottom_container import bottom


def render_footer() -> None:
    """Render the footer at the bottom of the page."""
    with bottom():
        st.divider()
        st.markdown(
            """
            <div style="text-align: center; color: #747583; font-family: 'IBM Plex Sans', sans-serif;">
                <p><strong style="color: #454759;">Aspen Investing Menu</strong></p>
                <p>© 2025 Mercer Advisors.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
