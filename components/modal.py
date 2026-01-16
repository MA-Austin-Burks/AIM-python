from typing import Any

import polars as pl
import streamlit as st

from components.constants import SELECTED_STRATEGY_MODAL_KEY
from components.tabs.allocation import render_allocation_tab
from components.tabs.description import render_description_tab
from utils.core.formatting import generate_badges


def _clear_modal_state() -> None:
    """Clear modal-related session state."""
    if SELECTED_STRATEGY_MODAL_KEY in st.session_state:
        del st.session_state[SELECTED_STRATEGY_MODAL_KEY]


@st.dialog("Strategy Details", width="large", dismissible=True)
def render_strategy_modal(strategy_name: str, strategy_data: dict[str, Any], filters: dict[str, Any], cleaned_data: pl.LazyFrame) -> None:
    """Render strategy details in a modal dialog."""
    from styles.branding import PRIMARY
    
    # Large header provides visual hierarchy over dialog title
    st.markdown(
        f'<h1 style="color: {PRIMARY["raspberry"]}; margin-top: -8px; margin-bottom: 8px;">{strategy_name}</h1>',
        unsafe_allow_html=True,
    )
    
    # Private Markets allocation reduces equity allocation by 15%
    has_private = strategy_data.get("Private Markets", False)
    alt_pct = 15 if has_private else 0
    equity_pct = strategy_data.get("Equity %", 0) - alt_pct
    fixed_pct = 100 - equity_pct - alt_pct
    
    parts = [f"{int(equity_pct)}% Equity", f"{int(fixed_pct)}% Fixed Income"]
    if alt_pct:
        parts.append(f"{alt_pct}% Alternative")
    exposure_display_text = " - ".join(parts)
    
    st.markdown(f"### {exposure_display_text}")
    
    badges = generate_badges(strategy_data)
    if badges:
        st.markdown(" &nbsp; ".join(badges) + " &nbsp;")
    
    st.space("small")
    
    tab_names = ["Description", "Allocation"]
    tabs = st.tabs(tab_names)
    
    for tab, tab_name in zip(tabs, tab_names):
        with tab:
            if tab_name == "Description":
                render_description_tab(strategy_name, strategy_data, cleaned_data)
            elif tab_name == "Allocation":
                render_allocation_tab(strategy_name, filters, cleaned_data)
    
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Close", use_container_width=True, type="primary"):
            _clear_modal_state()
            st.rerun()
