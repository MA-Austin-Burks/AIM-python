"""Tax-Loss Harvesting page - displays TLH replacement strategies reference."""

import polars as pl
import streamlit as st

from components import render_footer

TLH_UPDATE_DATE = "2026-01-17"


@st.cache_data(ttl=3600)
def _load_tlh() -> pl.DataFrame:
    """Load TLH CSV file (cached for 1 hour)."""
    return pl.read_csv("app_pages/data/tlh.csv")


st.markdown("# :material/money_off: Tax-Loss Harvesting (TLH)")
st.caption(f"last updated: {TLH_UPDATE_DATE}")

st.markdown(
    """
    Tax-loss harvesting (TLH) is a strategy that involves selling securities at a loss to offset capital gains taxes. 
    This reference table shows recommended replacement strategies for TLH purposes. When a strategy is sold at a loss, 
    these equivalent strategies can be used as replacements to maintain similar market exposure while realizing the tax benefit.
    """
)

tlh_df: pl.DataFrame = _load_tlh()
st.dataframe(
    tlh_df,
    height="content",
    width="stretch",
)

# Footer
render_footer()
