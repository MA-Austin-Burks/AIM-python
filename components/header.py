"""Page header component."""

from datetime import datetime

import streamlit as st


def render_page_header() -> None:
    """Render the page header with title and last updated caption."""
    st.set_page_config(page_title="Aspen Investing Menu", layout="wide")
    st.title("Aspen Investing Menu")
    st.caption(f"Last updated: {datetime.today().strftime(format='%Y-%m-%d')}")
    st.divider()
