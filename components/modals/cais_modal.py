"""CAIS modal for displaying CAIS strategy details."""

import polars as pl
import streamlit as st

from utils.data import load_cais_data
from utils.models import CAISSummary, StrategySummary


@st.dialog("CAIS Strategy Details", width="large", icon=":material/process_chart:")
def render_cais_modal(
    strategy_name: str,
    strategy_data: StrategySummary,
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
    strategy_row = cais_data.filter(pl.col("strategy") == strategy_name)

    if strategy_row.height == 0:
        st.error(f"CAIS data not found for strategy: {strategy_name}")
        return

    # Convert to CAISSummary for easier access
    cais_summary = CAISSummary.from_row(strategy_row.row(0, named=True))

    # Create a table of all CAIS metrics
    st.markdown("### CAIS Strategy Details")

    # Define display labels for each field
    metric_labels = {
        "CAIS Type": cais_summary.cais_type,
        "CAIS Subtype": cais_summary.cais_subtype,
        "Sub-Strategy": cais_summary.sub_strategy,
        "Client Type": cais_summary.client_type,
        "Available on Schwab": cais_summary.avail_schwab,
        "Available on Fidelity": cais_summary.avail_fidelity,
        "Core/Niche": cais_summary.core_niche,
        "MA Rank": str(cais_summary.ma_rank)
        if cais_summary.ma_rank is not None
        else "N/A",
        "Mercer Rating": cais_summary.mercer_rating,
        "Mercer ORA": cais_summary.mercer_ora,
        "Minimum Investment": f"${cais_summary.minimum:,.0f}",
        "Reporting Type": cais_summary.reporting_type,
        "Lockup": cais_summary.lockup,
        "Notes": cais_summary.notes,
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
