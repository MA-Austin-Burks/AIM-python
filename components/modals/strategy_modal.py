"""Strategy modal for displaying regular strategy details."""

from typing import Any

import polars as pl
import streamlit as st

from components.tab_overview import render_allocation_tab
from utils.branding import generate_badges
from utils.models import StrategySummary


@st.dialog("Strategy Details", width="large", icon=":material/process_chart:")
def render_strategy_modal(
    strategy_name: str,
    strategy_data: StrategySummary,
    strategy_color: str,
    cleaned_data: pl.LazyFrame,
) -> None:
    """Render strategy details in a modal dialog."""
    st.markdown(
        f'<h1 style="color: {strategy_color}">{strategy_name}</h1>',
        unsafe_allow_html=True,
    )

    # Get allocation percentages from _allo columns in the data
    normalized_strategy: str = strategy_name.strip().lower()
    allocation_row: pl.DataFrame = (
        cleaned_data.filter(
            pl.col("strategy").str.strip_chars().str.to_lowercase()
            == normalized_strategy
        )
        .select(["equity_allo", "fixed_allo", "private_allo", "cash_allo"])
        .first()
        .collect()
    )

    # Extract allocation values and build display text
    if allocation_row.height > 0:
        allocations: dict[str, float] = {
            "Equity": allocation_row["equity_allo"][0] or 0.0,
            "Fixed Income": allocation_row["fixed_allo"][0] or 0.0,
            "Alternative": allocation_row["private_allo"][0] or 0.0,
            "Cash": allocation_row["cash_allo"][0] or 0.0,
        }
    else:
        allocations = {}

    # Build parts list for allocations > 0
    parts: list[str] = [
        f"{int(value)}% {name}" for name, value in allocations.items() if value > 0
    ]

    if parts:
        exposure_display_text: str = " - ".join(parts)
        st.markdown(f"### {exposure_display_text}")

    badges: list[str] = generate_badges(strategy_data)
    if badges:
        st.markdown(" &nbsp; ".join(badges) + " &nbsp;")

    tab_names: list[str] = ["Overview"]
    tabs: list[Any] = st.tabs(tab_names)

    with tabs[0]:  # Overview tab
        render_allocation_tab(strategy_name, cleaned_data)
