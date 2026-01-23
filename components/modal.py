import polars as pl
import streamlit as st

from components.tab_overview import render_allocation_tab
from utils.models import StrategySummary
from utils.branding import generate_badges


@st.dialog("Strategy Details", width="large", icon=":material/process_chart:")
def render_strategy_modal(
    strategy_name: str,
    strategy_data: StrategySummary,
    strategy_color: str,
    cleaned_data: pl.LazyFrame,
) -> None:
    """Render strategy details in a modal dialog."""
    st.markdown(f'<h1 style="color: {strategy_color}">{strategy_name}</h1>', unsafe_allow_html=True)

    # Private Markets allocation reduces equity allocation by 15%
    has_private = strategy_data.private_markets
    alt_pct = 15 if has_private else 0
    equity_pct = strategy_data.equity_pct - alt_pct
    fixed_pct = 100 - equity_pct - alt_pct
    
    # Only show allocations with value > 0
    parts = []
    if equity_pct > 0:
        parts.append(f"{int(equity_pct)}% Equity")
    if fixed_pct > 0:
        parts.append(f"{int(fixed_pct)}% Fixed Income")
    if alt_pct > 0:
        parts.append(f"{alt_pct}% Alternative")
    
    if parts:
        exposure_display_text = " - ".join(parts)
        st.markdown(f"### {exposure_display_text}")
    
    badges: list[str] = generate_badges(strategy_data)
    if badges:
        st.markdown(" &nbsp; ".join(badges) + " &nbsp;")

    tab_names: list[str] = ["Overview"]
    tabs: list[Any] = st.tabs(tab_names)
    
    with tabs[0]:  # Overview tab
        render_allocation_tab(strategy_name, cleaned_data)