from typing import Any

import polars as pl
import streamlit as st

from components import (
    load_strats,
    render_dataframe_section,
    render_footer,
    render_page_header,
    render_sidebar,
    render_tabs,
)

render_page_header()

strategies_lazy: pl.LazyFrame = load_strats()
strategies_df: pl.DataFrame = strategies_lazy.collect()

filters: dict[str, Any] = render_sidebar(strats=strategies_df)
selected_strategy: str | None = render_dataframe_section(strategies_lazy, filters)

st.divider()
render_tabs(selected_strategy=selected_strategy)
render_footer()
