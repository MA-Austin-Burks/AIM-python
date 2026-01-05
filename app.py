import polars as pl
import streamlit as st

from components import (
    render_dataframe_section,
    render_page_header,
    render_sidebar,
    render_tabs,
)


@st.cache_data(ttl=3600)
def load_strats(path="data/strategies.csv"):
    return pl.scan_csv(path, null_values=["NA"])


render_page_header()

strats = load_strats()
filters = render_sidebar(strats)
selected_strategy, strategy_data = render_dataframe_section(strats, filters)

st.divider()
render_tabs(selected_strategy, strategy_data, filters)
