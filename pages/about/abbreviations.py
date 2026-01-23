"""Abbreviations page - displays strategy abbreviations reference."""

import polars as pl
import streamlit as st

from components import render_footer

ABBREVIATIONS_UPDATE_DATE = "2026-01-17"

st.set_page_config(page_title="Abbreviations", layout="wide")


@st.cache_data(ttl=3600)
def _load_abbreviations() -> pl.DataFrame:
    """Load abbreviations CSV file (cached for 1 hour)."""
    return pl.read_csv("pages/about/data/abbreviations.csv")


st.markdown("# :material/menu_book: Abbreviations")
st.caption(f"last updated: {ABBREVIATIONS_UPDATE_DATE}")

abbreviations_df: pl.DataFrame = _load_abbreviations()
st.dataframe(
    abbreviations_df,
    height="content",
    width="stretch",
)

# Footer
render_footer()
