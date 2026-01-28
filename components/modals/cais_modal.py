"""CAIS modal for displaying CAIS strategy details."""

from typing import Any

import polars as pl
import streamlit as st

from utils.data import load_cais_data


@st.dialog("CAIS Strategy Details", width="large", icon=":material/process_chart:")
def render_cais_modal(
    strategy_name: str,
    strategy_row: dict[str, Any],
    strategy_color: str,
    cleaned_data: pl.LazyFrame,
) -> None:
    """Render CAIS strategy details in a modal dialog with all CAIS metrics."""
    st.markdown(
        f'<h1 style="color: {strategy_color}">{strategy_name}</h1>',
        unsafe_allow_html=True,
    )

    # Load CAIS data and find the selected strategy
    cais_data = load_cais_data()
    cais_row_df = cais_data.filter(pl.col("strategy") == strategy_name)

    if cais_row_df.height == 0:
        st.error(f"CAIS data not found for strategy: {strategy_name}")
        return

    # Use row dict directly - no intermediate object needed
    row = cais_row_df.row(0, named=True)

    # Create a table of all CAIS metrics
    st.markdown("### CAIS Strategy Details")

    # Helper for formatting minimum
    minimum = float(row.get("minimum", 0) or 0)
    ma_rank = row.get("ma_rank")

    # Define display labels for each field - read directly from row dict
    metric_labels = {
        "CAIS Type": row.get("cais_type", ""),
        "CAIS Subtype": row.get("cais_subtype", ""),
        "Sub-Strategy": row.get("sub_strategy", ""),
        "Client Type": row.get("client_type", ""),
        "Available on Schwab": row.get("avail_schwab", ""),
        "Available on Fidelity": row.get("avail_fidelity", ""),
        "Core/Niche": row.get("core_niche", ""),
        "MA Rank": str(ma_rank) if ma_rank is not None else "N/A",
        "Mercer Rating": row.get("mercer_rating", ""),
        "Mercer ORA": row.get("mercer_ora", ""),
        "Minimum Investment": f"${minimum:,.0f}",
        "Reporting Type": row.get("reporting_type", ""),
        "Lockup": row.get("lockup", ""),
        "Notes": row.get("notes", ""),
    }

    # Display metrics in a two-column layout
    col1, col2 = st.columns(2)

    with col1:
        for i, (label, value) in enumerate(metric_labels.items()):
            if i < len(metric_labels) // 2 + len(metric_labels) % 2:
                st.markdown(f"**{label}:** {value}")

    with col2:
        for i, (label, value) in enumerate(metric_labels.items()):
            if i >= len(metric_labels) // 2 + len(metric_labels) % 2:
                st.markdown(f"**{label}:** {value}")
