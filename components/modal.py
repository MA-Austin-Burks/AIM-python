from collections.abc import Callable
from typing import Any

import polars as pl
import streamlit as st

from components.tab_overview import render_allocation_tab
from utils.models import StrategySummary
from utils.branding import generate_badges

# Modal registry maps modal type strings to modal functions
MODAL_REGISTRY: dict[str, Callable] = {}


def register_modal(modal_type: str, modal_func: Callable) -> None:
    """Register a modal function for a given modal type."""
    MODAL_REGISTRY[modal_type] = modal_func


def render_modal_by_type(
    modal_type: str,
    strategy_name: str,
    strategy_data: StrategySummary,
    strategy_color: str,
    cleaned_data: pl.LazyFrame,
) -> None:
    """Render a modal based on the modal type identifier.
    
    Args:
        modal_type: String identifier for the modal type (e.g., "strategy")
        strategy_name: Name of the strategy/item
        strategy_data: StrategySummary data object
        strategy_color: Color for the modal header
        cleaned_data: LazyFrame with cleaned data
    """
    modal_func = MODAL_REGISTRY.get(modal_type)
    if modal_func is None:
        st.error(f"Unknown modal type: {modal_type}")
        return
    
    # Call the registered modal function with the provided arguments
    modal_func(strategy_name, strategy_data, strategy_color, cleaned_data)


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
        .filter(pl.col("strategy").str.strip_chars().str.to_lowercase() == normalized_strategy)
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


# Register the strategy modal
register_modal("strategy", render_strategy_modal)