"""Equivalents page - displays equivalent securities reference."""

import polars as pl
import streamlit as st

from components import render_footer
from utils.core.constants import EQUIVALENTS_UPDATE_DATE

st.set_page_config(page_title="Equivalents", layout="wide")


@st.cache_data(ttl=3600)
def _load_equivalents() -> pl.DataFrame:
    """Load equivalents CSV file (cached for 1 hour)."""
    return pl.read_csv("pages/about/data/equivalents.csv")


st.markdown("# Equivalents")
st.caption(f"last updated: {EQUIVALENTS_UPDATE_DATE}")

equivalents_df: pl.DataFrame = _load_equivalents()
st.dataframe(
    equivalents_df,
    height="content",
    use_container_width=True,
)

# Footer
render_footer()
