import polars as pl
import streamlit as st

from components import (
    render_dataframe_section,
    render_page_header,
    render_sidebar,
    render_tabs,
)


@st.cache_data(ttl=3600)
def load_strats(path: str = "data/strategies.csv") -> pl.LazyFrame:
    return pl.scan_csv(path, null_values=["NA"])


render_page_header()

strategies_lazy = load_strats()
filters = render_sidebar(strats=strategies_lazy)
selected_strategy, strategy_data = render_dataframe_section(strategies_lazy, filters)

st.divider()
render_tabs(
    selected_strategy=selected_strategy, strategy_data=strategy_data, filters=filters
)
