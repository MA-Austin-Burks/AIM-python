"""Tab components module."""

from typing import Any

import streamlit as st

from components.tabs.allocation import render_allocation_tab
from components.tabs.description import render_description_tab
from components.tabs.performance import render_performance_tab

__all__ = [
    "render_tabs",
    "render_description_tab",
    "render_allocation_tab",
    "render_performance_tab",
]

BASE_TAB_NAMES = ["Description", "Performance", "Allocation", "Minimum"]


def render_tabs(
    selected_strategy: str | None,
    strategy_data: dict[str, Any] | None,
    filters: dict,
) -> None:
    """Render tabs for strategy details."""
    tab_names = BASE_TAB_NAMES.copy()
    tab_names.insert(tab_names.index("Minimum") + 1, "Private Markets")

    tabs = st.tabs(tab_names)

    if selected_strategy and strategy_data:
        has_private_markets = strategy_data.get("Private Markets", False)

        for tab, tab_name in zip(tabs, tab_names):
            with tab:
                if tab_name == "Description":
                    render_description_tab(selected_strategy, strategy_data)
                elif tab_name == "Allocation":
                    render_allocation_tab(selected_strategy, strategy_data, filters)
                elif tab_name == "Performance":
                    render_performance_tab(selected_strategy, strategy_data)
                elif tab_name == "Private Markets":
                    if has_private_markets:
                        st.write(f"**Private Markets** - {selected_strategy}")
                    else:
                        st.warning(
                            "Private Markets is not available for this strategy."
                        )
                else:
                    st.write(f"**{tab_name}** - {selected_strategy}")
    else:
        for tab, tab_name in zip(tabs, tab_names):
            with tab:
                st.info(
                    f"Select a strategy from the table above to view {tab_name.lower()}."
                )
