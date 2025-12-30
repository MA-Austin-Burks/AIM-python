"""Tab components for displaying strategy details."""

from typing import Any

import streamlit as st


def render_tabs(selected_strategy: str | None = None) -> None:
    """
    Render tabs for strategy details.

    Args:
        selected_strategy: Name of the selected strategy, or None if no selection
    """
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Description", "Performance", "Allocations", "Holdings", "Fact Sheet"]
    )

    if selected_strategy:
        _render_tab_content(tab1, "Description", selected_strategy)
        _render_tab_content(tab2, "Performance", selected_strategy)
        _render_tab_content(tab3, "Allocations", selected_strategy)
        _render_tab_content(tab4, "Holdings", selected_strategy)
        _render_fact_sheet_tab(tab5, selected_strategy)
    else:
        _render_empty_tabs(tab1, tab2, tab3, tab4, tab5)


def _render_tab_content(tab: Any, tab_name: str, strategy_name: str) -> None:
    """
    Render content for a standard tab.

    Args:
        tab: Streamlit tab object
        tab_name: Display name of the tab
        strategy_name: Name of the selected strategy
    """
    with tab:
        st.write(f"**{tab_name}** - {strategy_name}")


def _render_fact_sheet_tab(tab: Any, strategy_name: str) -> None:
    """
    Render content for the Fact Sheet tab with SharePoint link.

    Args:
        tab: Streamlit tab object
        strategy_name: Name of the selected strategy
    """
    with tab:
        st.write(f"**Fact Sheet** - {strategy_name}")

        # Strategy Info Link (SharePoint)
        strategy_info_url = (
            "https://merceradvisors.sharepoint.com/sites/InvestmentStrategy/"
            "_layouts/15/guestaccess.aspx?share=ERK1A-aV9QZAszzG23zqFIcBxcx27KT80xZhP33zl-1S1A&e=Pm9Nbr"
        )
        st.markdown(
            f'<a href="{strategy_info_url}" target="_blank" '
            f'style="display: inline-block; padding: 10px 20px; background-color: #C00686; '
            f'color: white; text-decoration: none; border-radius: 5px; margin-top: 10px; '
            f'font-family: \'IBM Plex Sans\', sans-serif; font-weight: 500; transition: background-color 0.2s;">'
            f'Strategy Info</a>',
            unsafe_allow_html=True,
        )


def _render_empty_tabs(
    tab1: Any, tab2: Any, tab3: Any, tab4: Any, tab5: Any
) -> None:
    """
    Render empty state messages for tabs when no strategy is selected.

    Args:
        tab1: First Streamlit tab object
        tab2: Second Streamlit tab object
        tab3: Third Streamlit tab object
        tab4: Fourth Streamlit tab object
        tab5: Fifth Streamlit tab object
    """
    tab_messages = {
        tab1: "description",
        tab2: "performance",
        tab3: "allocations",
        tab4: "holdings",
        tab5: "fact sheet",
    }

    for tab, tab_name in tab_messages.items():
        with tab:
            st.info(
                f"Please select a strategy from the table above to view its {tab_name}."
            )
