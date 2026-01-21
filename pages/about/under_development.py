"""Under Development page - displays features currently under development."""

import streamlit as st

from components import render_footer
from utils.core.constants import UNDER_DEVELOPMENT_UPDATE_DATE

st.set_page_config(page_title="Under Development", layout="wide")


@st.cache_data(ttl=3600)
def _load_under_development() -> str:
    """Load under development text file (cached for 1 hour)."""
    with open("pages/about/data/under_development.txt", "r", encoding="utf-8") as f:
        return f.read()


st.markdown("# Under Development")
st.caption(f"last updated: {UNDER_DEVELOPMENT_UPDATE_DATE}")

under_development_text: str = _load_under_development()
st.markdown(under_development_text)

# Footer
render_footer()
