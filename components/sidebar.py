from typing import Any

import polars as pl
import streamlit as st

from components.constants import (
    ACCOUNT_VALUE_STEP,
    DEFAULT_EQUITY_RANGE,
    DEFAULT_MIN_ACCOUNT_VALUE,
    DEFAULT_RECOMMENDED_ONLY,
    DEFAULT_SERIES_SUBTYPES,
    DEFAULT_STRATEGY_TYPE,
    EQUITY_MAX_VALUE,
    EQUITY_MIN_VALUE,
    EQUITY_STEP,
    MIN_ACCOUNT_VALUE,
    SERIES_OPTIONS,
    STRATEGY_TYPES,
)

# Session state key for pending clear action
_PENDING_CLEAR_KEY = "_pending_clear_search"


def _clear_search() -> None:
    """Callback to clear the search input."""
    st.session_state["strategy_search_input"] = ""


def _schedule_clear_search() -> None:
    """Schedule a clear for the next rerun (used by shortcut button)."""
    st.session_state[_PENDING_CLEAR_KEY] = True


def render_sidebar(strats: pl.DataFrame) -> dict[str, Any]:
    """Render sidebar filters using the strategy table DataFrame."""
    schema: pl.Schema = strats.schema
    
    # Check if we need to clear search from a previous shortcut button press
    if st.session_state.get(_PENDING_CLEAR_KEY, False):
        st.session_state["strategy_search_input"] = ""
        st.session_state[_PENDING_CLEAR_KEY] = False

    with st.sidebar:
        st.header("Search")
        
        col_search, col_clear = st.columns([5, 1])
        with col_search:
            strategy_search_text = st.text_input(
                "Strategy Name",
                value="",
                placeholder="Type to filter by strategy name...",
                key="strategy_search_input",
                label_visibility="collapsed",
            )
        with col_clear:
            st.button("✕", help="Clear search and enable filters", key="clear_search_btn", on_click=_clear_search)
        
        # Search mode disables filters to prevent confusion (search is OR, filters are AND)
        search_active = bool(strategy_search_text and strategy_search_text.strip())
        
        # Visual separator clarifies that search and filters are mutually exclusive modes
        st.markdown(
            """
            <div style="display: flex; align-items: center; margin: 1rem 0;">
                <div style="flex: 1; height: 1px; background-color: rgba(128, 128, 128, 0.3);"></div>
                <span style="padding: 0 0.75rem; color: rgba(128, 128, 128, 0.7); font-size: 1.1rem; font-weight: 500;">OR</span>
                <div style="flex: 1; height: 1px; background-color: rgba(128, 128, 128, 0.3);"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.space("small")
        if search_active:
            if st.button("Enable Filters", key="enable_filters_btn", type="primary", use_container_width=True):
                _schedule_clear_search()
        
        recommended_only = st.toggle(
            "Investment Committee Recommended Only",
            value=DEFAULT_RECOMMENDED_ONLY,
            help="Show only recommended strategies when enabled",
            disabled=search_active,
        )
        show_recommended = recommended_only
        show_approved = False

        strategy_types: list[str] = STRATEGY_TYPES
        default_type: str = DEFAULT_STRATEGY_TYPE

        selected_types: list[str] = [default_type] if default_type else []
        type_options: list[str] = SERIES_OPTIONS

        col_min, col_equity = st.columns(2)
        with col_min:
            min_strategy = st.number_input(
                "Account Value ($)",
                min_value=MIN_ACCOUNT_VALUE,
                value=DEFAULT_MIN_ACCOUNT_VALUE,
                step=ACCOUNT_VALUE_STEP,
                key="min_strategy",
                disabled=search_active,
            )
        with col_equity:
            equity_range = st.slider(
                "Equity Allocation Range",
                min_value=EQUITY_MIN_VALUE,
                max_value=EQUITY_MAX_VALUE,
                value=DEFAULT_EQUITY_RANGE,
                step=EQUITY_STEP,
                key="equity_range",
                disabled=search_active,
            )

        col_tax, col_sma, col_private = st.columns(3)
        with col_tax:
            tax_managed_selection = st.pills(
                "Tax-Managed (TM)",
                options=["Yes", "No"],
                selection_mode="single",
                default=None,
                disabled=search_active,
            )
        with col_sma:
            has_sma_manager_selection = st.pills(
                "Has SMA Manager",
                options=["Yes", "No"],
                selection_mode="single",
                default=None,
                disabled=search_active or "Has SMA Manager" not in schema,
            )
        with col_private:
            private_markets_selection = st.pills(
                "Private Markets",
                options=["Yes", "No"],
                selection_mode="single",
                default=None,
                disabled=search_active,
            )

        selected_type = st.pills(
            "Strategy Type",
            options=strategy_types,
            selection_mode="single",
            default=default_type,
            disabled=search_active,
        )
        selected_types = [selected_type] if selected_type else []

        selected_subtypes = st.pills(
            "Series",
            options=type_options,
            selection_mode="multi",
            default=DEFAULT_SERIES_SUBTYPES
            if all(subtype in type_options for subtype in DEFAULT_SERIES_SUBTYPES)
            else [],
            disabled=search_active,
        )

        st.divider()
        with st.container(border=True):
            st.markdown("**Abbreviations**")
            st.markdown(
                """
                - **5YTRYSMA** - MA 5 Year Treasury Ladder (SMA)
                - **B5YCRP** - BlackRock Corporate 1-5 Year
                - **MA** - Managed Account
                - **MUSLGMKTLM** - MA Market US Large (SMA Low Min)
                - **N7YMUN** - Nuveen Municipal 1-7 Year
                - **QP** - Quantitative Portfolio
                - **QUSALMKT** - QP Market US All Cap
                - **QUSLGVMQ** - QP Factor US Large Cap VMQ
                - **SMA** - Separately Managed Account
                - **VMQ** - Value, Momentum, Quality
                """
            )
        
        st.divider()

    tax_managed_filter = tax_managed_selection if tax_managed_selection else "All"
    has_sma_manager_filter = has_sma_manager_selection if has_sma_manager_selection else "All"
    private_markets_filter = private_markets_selection if private_markets_selection else "All"

    return {
        "strategy_search": strategy_search_text.strip() if strategy_search_text else None,
        "search_only_mode": search_active,
        "min_strategy": min_strategy,
        "tax_managed_filter": tax_managed_filter,
        "has_sma_manager_filter": has_sma_manager_filter,
        "private_markets_filter": private_markets_filter,
        "show_recommended": show_recommended,
        "show_approved": show_approved,
        "selected_types": selected_types,
        "selected_subtypes": selected_subtypes,
        "equity_range": equity_range,
    }
