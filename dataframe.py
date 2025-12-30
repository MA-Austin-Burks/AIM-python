"""Dataframe display component."""

import streamlit as st

DISPLAY_COLUMNS = [
    "Recommended",
    "Strategy",
    "Yield",
    "Expense Ratio",
    "Minimum",
    "Equity %",
    "Subtype",
    "Tax-Managed",
    "Status",
]


def render_dataframe(df, filtered_strategies):
    """
    Render the strategies dataframe and return selected strategy name.
    
    Args:
        df: Formatted dataframe to display
        filtered_strategies: Original filtered dataframe (for getting selected strategy)
    
    Returns:
        Selected strategy name or None
    """
    selected_rows = st.dataframe(
        df.select(DISPLAY_COLUMNS),
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Recommended": "⭐",
            "Strategy": "Strategy",
            "Yield": "Yield",
            "Expense Ratio": "Expense Ratio",
            "Minimum": "Minimum",
            "Equity %": "Equity %",
            "Subtype": "Subtype",
            "Tax-Managed": "Tax-Managed",
            "Status": "Status",
        },
    )
    
    return (
        filtered_strategies.select("Strategy")
        .row(selected_rows.selection.rows[0], named=True)["Strategy"]
        if selected_rows.selection.rows
        else None
    )
