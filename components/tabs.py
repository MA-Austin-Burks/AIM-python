"""Tab components for displaying strategy details."""

from typing import Any

import streamlit as st

TAB_NAMES = [
    "Description",
    "Performance",
    "Allocations",
    "Blended",
    "Private Markets",
    "Minimum",
    "Fact Sheet",
]


def render_tabs(selected_strategy: str | None = None) -> None:
    """
    Render tabs for strategy details.
    """
    tabs = st.tabs(TAB_NAMES)

    if selected_strategy:
        for tab, tab_name in zip(tabs[:-1], TAB_NAMES[:-1]):
            _render_tab_content(tab, tab_name, selected_strategy)
        _render_fact_sheet_tab(tabs[-1], selected_strategy)
    else:
        for tab, tab_name in zip(tabs, TAB_NAMES):
            with tab:
                st.info(
                    f"Please select a strategy from the table above to view its {tab_name.lower()}."
                )


def _render_tab_content(tab: Any, tab_name: str, strategy_name: str) -> None:
    """
    Render content for a standard tab.
    """
    with tab:
        st.write(f"**{tab_name}** - {strategy_name}")


def _render_fact_sheet_tab(tab: Any, strategy_name: str) -> None:
    """
    Render content for the Fact Sheet tab with SharePoint link.
    """
    with tab:
        st.write(f"**Fact Sheet** - {strategy_name}")

        strategy_info_url = (
            "https://merceradvisors.sharepoint.com/sites/InvestmentStrategy/"
            "_layouts/15/guestaccess.aspx?share=ERK1A-aV9QZAszzG23zqFIcBxcx27KT80xZhP33zl-1S1A&e=Pm9Nbr"
        )
        st.markdown(
            f'<a href="{strategy_info_url}" target="_blank" '
            f'style="display: inline-block; padding: 10px 20px; background-color: #C00686; '
            f"color: white; text-decoration: none; border-radius: 5px; margin-top: 10px; "
            f"font-family: 'IBM Plex Sans', sans-serif; font-weight: 500; transition: background-color 0.2s;\">"
            f"Strategy Info</a>",
            unsafe_allow_html=True,
        )
