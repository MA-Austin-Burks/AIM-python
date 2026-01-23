"""Equivalents page - displays equivalent securities reference."""

import polars as pl
import streamlit as st

from components import render_footer

EQUIVALENTS_UPDATE_DATE = "2026-01-17"


@st.cache_data(ttl=3600)
def _load_equivalents() -> pl.DataFrame:
    """Load equivalents CSV file (cached for 1 hour)."""
    return pl.read_csv("app_pages/data/equivalents.csv")


st.markdown("# :material/equal: Equivalents")
st.caption(f"last updated: {EQUIVALENTS_UPDATE_DATE}")

st.markdown(
    """
    This reference table provides equivalent securities and strategies that can be used as alternatives or replacements. 
    Equivalents are strategies with similar investment characteristics, risk profiles, or market exposure that may be used 
    interchangeably based on availability, tax considerations, or other investment objectives.
    """
)

equivalents_df: pl.DataFrame = _load_equivalents()
st.dataframe(
    equivalents_df,
    height="content",
    width="stretch",
)

# Footer
render_footer()
