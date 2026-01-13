import polars as pl
import streamlit as st

from components import (
    render_dataframe_section,
    render_page_header,
    render_sidebar,
    render_tabs,
)

# from utils import clean_orion_platform, get_platform, get_strategy_list

@st.cache_data(ttl=3600)
def load_strats(path: str = "data/strategies.csv") -> pl.LazyFrame:
    return pl.scan_csv(path, null_values=["NA"])


render_page_header()

strats: pl.LazyFrame = load_strats()
filters: dict = render_sidebar(strats)
selected_strategy, strategy_data = render_dataframe_section(strats, filters)

st.divider()
render_tabs(selected_strategy, strategy_data, filters)

# st.write("Local OrionPlatform Data")
# st.dataframe(strats.collect())

# st.write("Azure Hosted OrionPlatform Data")
# df = get_platform()
# df_cleaned = clean_orion_platform(df)
# st.dataframe(df_cleaned)

# st.write("Strategy List")
# strategy_list = get_strategy_list(df_cleaned)
# st.dataframe(strategy_list)