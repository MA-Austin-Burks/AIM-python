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

strategies_df: pl.DataFrame = load_strats()

filters: dict[str, Any] = render_sidebar(strats=strategies_df)
selected_strategy: str | None = render_dataframe_section(strategies_df, filters)

st.divider()
render_tabs(selected_strategy=selected_strategy)
render_footer()
