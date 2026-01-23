"""Tax-Loss Harvesting page - displays TLH replacement strategies reference."""

import polars as pl
import streamlit as st

from components import render_footer

TLH_UPDATE_DATE = "2026-01-17"

st.set_page_config(page_title="Tax-Loss Harvesting", layout="wide")


@st.cache_data(ttl=3600)
def _load_tlh() -> pl.DataFrame:
    """Load TLH CSV file (cached for 1 hour)."""
    return pl.read_csv("pages/about/data/tlh.csv")


st.markdown("# :material/money_off: Tax-Loss Harvesting (TLH)")
st.caption(f"last updated: {TLH_UPDATE_DATE}")

tlh_df: pl.DataFrame = _load_tlh()
st.dataframe(
    tlh_df,
    height="content",
    width="stretch",
)

# Footer
render_footer()
