"""Equivalents page - displays equivalent securities reference."""

import polars as pl
import streamlit as st

from components import render_footer

EQUIVALENTS_UPDATE_DATE = "2026-01-17"


@st.cache_data(ttl=3600)
def _load_equivalents() -> pl.DataFrame:
    """Load equivalents CSV file (cached for 1 hour)."""
    return pl.read_csv("app_pages/about/data/equivalents.csv")


st.markdown("# :material/equal: Equivalents")
st.caption(f"last updated: {EQUIVALENTS_UPDATE_DATE}")

equivalents_df: pl.DataFrame = _load_equivalents()
st.dataframe(
    equivalents_df,
    height="content",
    width="stretch",
)

# Footer
render_footer()
