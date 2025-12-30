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

# Page configuration
render_page_header()

# Load data
strategies_df: pl.DataFrame = load_strats()

# Render sidebar and get filters
filters = render_sidebar(strats=strategies_df)

# Render dataframe section (handles filtering, formatting, and display)
selected_strategy: str | None = render_dataframe_section(strategies_df, filters)

# Display strategy details
st.divider()
render_tabs(selected_strategy=selected_strategy)
render_footer()
