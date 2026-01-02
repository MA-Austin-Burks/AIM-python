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


def render_tabs(selected_strategy, strategy_data, filters):
    tab_names = [
        "Description",
        "Performance",
        "Allocation",
        "Minimum",
    ]

    # Only add Private Markets tab if a strategy is selected and it has private markets
    if selected_strategy and strategy_data and strategy_data.get("Private Markets"):
        tab_names.append("Private Markets")

    tabs = st.tabs(tab_names)

    if selected_strategy:
        for tab, tab_name in zip(tabs, tab_names):
            with tab:
                if tab_name == "Description":
                    render_description_tab(selected_strategy, strategy_data)
                elif tab_name == "Allocation":
                    render_allocation_tab(selected_strategy, filters)
                elif tab_name == "Performance":
                    render_performance_tab(selected_strategy, strategy_data)
                elif tab_name == "Private Markets":
                    st.write(f"**Private Markets** - {selected_strategy}")
                else:
                    st.write(f"**{tab_name}** - {selected_strategy}")
    else:
        for tab, tab_name in zip(tabs, tab_names):
            with tab:
                st.info(
                    f"Select a strategy from the table above to view {tab_name.lower()}."
                )
