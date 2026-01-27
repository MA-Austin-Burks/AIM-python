"""Modal registry for managing and rendering different modal types."""

from collections.abc import Callable

import polars as pl
import streamlit as st

from utils.models import StrategySummary

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
