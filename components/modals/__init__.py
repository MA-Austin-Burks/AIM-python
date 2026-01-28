"""Modal components for displaying strategy details."""

from typing import Any

import polars as pl
import streamlit as st

from components.modals.cais_modal import render_cais_modal
from components.modals.strategy_modal import render_strategy_modal


def render_modal_by_type(
    modal_type: str,
    strategy_name: str,
    strategy_row: dict[str, Any],
    strategy_color: str,
    cleaned_data: pl.LazyFrame,
) -> None:
    """Render a modal based on the modal type identifier.

    Args:
        modal_type: String identifier for the modal type ("strategy" or "cais")
        strategy_name: Name of the strategy/item
        strategy_row: Row dict from Polars DataFrame
        strategy_color: Color for the modal header
        cleaned_data: LazyFrame with cleaned data
    """
    if modal_type == "strategy":
        render_strategy_modal(strategy_name, strategy_row, strategy_color, cleaned_data)
    elif modal_type == "cais":
        render_cais_modal(strategy_name, strategy_row, strategy_color, cleaned_data)
    else:
        st.error(f"Unknown modal type: {modal_type}")


__all__ = [
    "render_modal_by_type",
]
