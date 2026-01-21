from typing import Any

import polars as pl
import streamlit as st

from components.tab_overview import render_allocation_tab
from utils.styles.branding import generate_badges


@st.dialog("Details", width="large", icon=":material/strategy:")
def render_strategy_modal(strategy_name: str, strategy_data: dict[str, Any], strategy_color: str, cleaned_data: pl.LazyFrame) -> None:
    """Render strategy details in a modal dialog."""
    st.markdown(f'<h1 style="color: {strategy_color}">{strategy_name}</h1>', unsafe_allow_html=True)

    # Private Markets allocation reduces equity allocation by 15%
    has_private = strategy_data.get("Private Markets", False)
    alt_pct = 15 if has_private else 0
    equity_pct = strategy_data.get("Equity %", 0) - alt_pct
    fixed_pct = 100 - equity_pct - alt_pct
    
    parts = [f"{int(equity_pct)}% Equity", f"{int(fixed_pct)}% Fixed Income"]
    if alt_pct:
        parts.append(f"{alt_pct}% Alternative")
    exposure_display_text = " - ".join(parts)
    
    st.markdown(f"### {exposure_display_text}")
    
    badges: list[str] = generate_badges(strategy_data)
    if badges:
        st.markdown(" &nbsp; ".join(badges) + " &nbsp;")

    tab_names: list[str] = ["Overview"]
    tabs: list[Any] = st.tabs(tab_names)
    
    with tabs[0]:  # Overview tab
        render_allocation_tab(strategy_name, cleaned_data)