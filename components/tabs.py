"""Tab components for displaying strategy details."""

import streamlit as st

BASE_TAB_NAMES: list[str] = [
    "Description",
    "Performance",
    "Allocations",
    "Minimum",
]


def _has_all_weather(strategy_name: str | None) -> bool:
    """Check if strategy name contains 'All Weather'."""
    if not strategy_name:
        return False
    return "All Weather" in strategy_name


def _has_blended(strategy_name: str | None) -> bool:
    """Check if strategy name contains 'Blended'."""
    if not strategy_name:
        return False
    return "Blended" in strategy_name


def render_tabs(selected_strategy: str | None = None) -> None:
    """Render tabs for strategy details."""
    # Build tab names conditionally
    tab_names = BASE_TAB_NAMES.copy()
    
    # Add Private Markets tab only if strategy has "All Weather" in name
    if selected_strategy and _has_all_weather(selected_strategy):
        # Insert Private Markets before Minimum
        private_markets_index = tab_names.index("Minimum")
        tab_names.insert(private_markets_index, "Private Markets")
    
    # Add Blended tab only if strategy has "Blended" in name
    if selected_strategy and _has_blended(selected_strategy):
        # Insert Blended before Minimum
        blended_index = tab_names.index("Minimum")
        tab_names.insert(blended_index, "Blended")
    
    tabs = st.tabs(tab_names)

    if selected_strategy:
        for tab, tab_name in zip(tabs, tab_names):
            with tab:
                if tab_name == "Description":
                    st.write(f"**{tab_name}** - {selected_strategy}")
                    _render_download_button(selected_strategy)
                else:
                    st.write(f"**{tab_name}** - {selected_strategy}")
    else:
        for tab, tab_name in zip(tabs, tab_names):
            with tab:
                st.info(
                    f"Please select a strategy from the table above to view its {tab_name.lower()}."
                )


def _render_download_button(strategy_name: str) -> None:
    """Render the Strategy Info download button."""
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
