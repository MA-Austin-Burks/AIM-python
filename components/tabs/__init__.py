from typing import Any, Optional

import polars as pl
import streamlit as st

from components.tabs.allocation import render_allocation_tab
from components.tabs.description import render_description_tab

__all__ = [
    "render_tabs",
    "render_description_tab",
    "render_allocation_tab",
]


def _get_tab_names() -> list[str]:
    """Get tab names - Description first, then Allocation."""
    return ["Description", "Allocation"]


def render_tabs(
    strategy_name: Optional[str],
    strategy_data: Optional[dict[str, Any]],
    filters: dict[str, Any],
    cleaned_data: pl.LazyFrame,
) -> None:
    """Render tabs for table view (below selected strategy)."""
    tab_names = _get_tab_names()
    tabs = st.tabs(tab_names)

    if strategy_name:
        for tab, tab_name in zip(tabs, tab_names):
            with tab:
                if tab_name == "Description":
                    render_description_tab(strategy_name, strategy_data, cleaned_data)
                elif tab_name == "Allocation":
                    render_allocation_tab(strategy_name, cleaned_data)
    else:
        for tab, tab_name in zip(tabs, tab_names):
            with tab:
                st.info(
                    f"Select a strategy from the table above to view {tab_name.lower()}."
                )
