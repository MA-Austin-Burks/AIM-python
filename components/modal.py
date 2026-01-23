from typing import Any

import polars as pl
import streamlit as st

from components.tab_overview import render_allocation_tab
from utils.models import StrategySummary
from utils.branding import generate_badges
from utils.column_names import STRATEGY


@st.dialog("Strategy Details", width="large", icon=":material/process_chart:")
def render_strategy_modal(
    strategy_name: str,
    strategy_data: StrategySummary,
    strategy_color: str,
    cleaned_data: pl.LazyFrame,
) -> None:
    """Render strategy details in a modal dialog."""
    st.markdown(f'<h1 style="color: {strategy_color}">{strategy_name}</h1>', unsafe_allow_html=True)

    # Get allocation percentages from _allo columns in the data
    normalized_strategy = strategy_name.strip().lower()
    allocation_row = (
        cleaned_data
        .filter(pl.col(STRATEGY).str.strip_chars().str.to_lowercase() == normalized_strategy)
        .select(["equity_allo", "fixed_allo", "private_allo", "cash_allo"])
        .first()
        .collect()
    )
    
    # Extract allocation values (default to 0 if None or empty)
    equity_pct = float(allocation_row["equity_allo"][0] or 0.0) if allocation_row.height > 0 else 0.0
    fixed_pct = float(allocation_row["fixed_allo"][0] or 0.0) if allocation_row.height > 0 else 0.0
    private_pct = float(allocation_row["private_allo"][0] or 0.0) if allocation_row.height > 0 else 0.0
    cash_pct = float(allocation_row["cash_allo"][0] or 0.0) if allocation_row.height > 0 else 0.0
    
    # Only show allocations with value > 0
    parts = []
    if equity_pct > 0:
        parts.append(f"{int(equity_pct)}% Equity")
    if fixed_pct > 0:
        parts.append(f"{int(fixed_pct)}% Fixed Income")
    if private_pct > 0:
        parts.append(f"{int(private_pct)}% Alternative")
    if cash_pct > 0:
        parts.append(f"{int(cash_pct)}% Cash")
    
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