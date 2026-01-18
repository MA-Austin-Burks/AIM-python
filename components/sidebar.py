import polars as pl
import streamlit as st

from components.constants import (
    ABBREVIATIONS_UPDATE_DATE,
    ACCOUNT_VALUE_STEP,
    DEFAULT_EQUITY_RANGE,
    DEFAULT_MIN_ACCOUNT_VALUE,
    DEFAULT_RECOMMENDED_ONLY,
    DEFAULT_SERIES_SUBTYPES,
    DEFAULT_STRATEGY_TYPE,
    EQUIVALENTS_UPDATE_DATE,
    EQUITY_MAX_VALUE,
    EQUITY_MIN_VALUE,
    EQUITY_STEP,
    MIN_ACCOUNT_VALUE,
    SERIES_OPTIONS,
    STRATEGY_TYPES,
    STRATEGY_TYPE_TO_SERIES,
    TLH_UPDATE_DATE,
    UNDER_DEVELOPMENT_UPDATE_DATE,
)



def _render_yes_no_filter(label: str, key: str, disabled: bool) -> str | None:
    """Render a boolean filter pill widget with Yes/No options."""
    return st.pills(
        label,
        options=["Yes", "No"],
        selection_mode="single",
        default=None,
        disabled=disabled,
        key=key,
    )


def render_sidebar() -> pl.Expr:
    """Render sidebar filters and return a Polars filter expression."""
    # Check if we need to clear search (must be done before any widgets are created)
    if st.session_state.get("_clear_search_flag", False):
        st.session_state["strategy_search_input"] = ""
        st.session_state["_clear_search_flag"] = False
    
    # Initialize filter expression list - build incrementally as filters are rendered
    expressions: list[pl.Expr] = []

    with st.sidebar:
        # ============================================================================
        # STEP 2: Render search input and filters toggle
        # ============================================================================
        st.header("Search")
        
        col_search, col_clear = st.columns([9, 1])
        with col_search:
            strategy_search_text = st.text_input(
                "Strategy Name",
                value="",
                placeholder="Type to filter by strategy name...",
                key="strategy_search_input",
                label_visibility="collapsed",
            )
        with col_clear:
            if st.button("✕", key="clear_search_btn"):
                st.session_state["_clear_search_flag"] = True
                st.rerun()
        
        # Search mode disables filters to prevent confusion (search is OR, filters are AND)
        search_active = bool(strategy_search_text and strategy_search_text.strip())
        strategy_search = strategy_search_text.strip() if strategy_search_text else None
        
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
        if search_active:
            st.warning("Clear search to re-enable filters.", icon=":material/data_alert:")
        
        # ============================================================================
        # STEP 3: Render filter controls (recommended, account value, equity range)
        # ============================================================================
        recommended_only = st.toggle(
            "Investment Committee Recommended Only",
            value=DEFAULT_RECOMMENDED_ONLY,
            disabled=search_active,
        )
        if not search_active and recommended_only:
            expressions.append(pl.col("Recommended"))

        strategy_types: list[str] = STRATEGY_TYPES
        default_type: str = DEFAULT_STRATEGY_TYPE
        
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
        if not search_active:
            expressions.append(pl.col("Minimum") <= min_strategy)
        
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
        if not search_active:
            expressions.append(
                (pl.col("Equity %").is_not_null())
                & (pl.col("Equity %") >= equity_range[0])
                & (pl.col("Equity %") <= equity_range[1])
            )

        # ============================================================================
        # STEP 4: Render boolean filters (tax-managed, SMA manager, private markets)
        # ============================================================================
        col_tax, col_sma, col_private = st.columns(3)
        with col_tax:
            tax_managed_selection: str | None = _render_yes_no_filter(
                label="Tax-Managed (TM)", key="sidebar_tax_managed", disabled=search_active
            )
        if not search_active and tax_managed_selection:
            expressions.append(pl.col("Tax-Managed") == (tax_managed_selection == "Yes"))
        
        with col_sma:
            has_sma_manager_selection: str | None = _render_yes_no_filter(
                label="Has SMA Manager", key="sidebar_sma_manager", disabled=search_active
            )
        if not search_active and has_sma_manager_selection:
            expressions.append(pl.col("Has SMA Manager") == (has_sma_manager_selection == "Yes"))
        
        with col_private:
            private_markets_selection: str | None = _render_yes_no_filter(
                label="Private Markets", key="sidebar_private_markets", disabled=search_active
            )
        if not search_active:
            if private_markets_selection == "Yes":
                expressions.append(pl.col("Private Markets"))
            elif private_markets_selection == "No":
                expressions.append(~pl.col("Private Markets"))

        # ============================================================================
        # STEP 5: Render type and series filters
        # ============================================================================
        selected_type = st.pills(
            "Strategy Type",
            options=strategy_types,
            selection_mode="single",
            default=default_type,
            disabled=search_active,
            key="sidebar_strategy_type",
        )
        selected_types = [selected_type] if selected_type else []

        # Track previous strategy type to detect changes
        previous_type_key = "_previous_strategy_type"
        previous_type = st.session_state.get(previous_type_key, default_type)
        
        # Dynamically filter series options based on selected strategy type
        if selected_type and selected_type in STRATEGY_TYPE_TO_SERIES:
            type_options: list[str] = STRATEGY_TYPE_TO_SERIES[selected_type]
        else:
            type_options: list[str] = SERIES_OPTIONS

        # Determine default selections based on strategy type
        if selected_type == "Risk-Based":
            default_selections = DEFAULT_SERIES_SUBTYPES  # ["Multifactor Series"]
        elif selected_type == "Asset-Class":
            default_selections = []
        elif selected_type == "Special Situation":
            default_selections = ["Special Situation Strategies"]
        else:
            default_selections = []

        # Handle strategy type changes by clearing invalid selections
        if selected_type != previous_type:
            # Strategy type changed - clear the session state so widget can initialize with new defaults
            st.session_state.pop("sidebar_series", None)
            st.session_state[previous_type_key] = selected_type
            valid_selections = default_selections
        else:
            # Strategy type hasn't changed - get current selections and filter invalid ones
            current_selections = st.session_state.get("sidebar_series", default_selections)
            if isinstance(current_selections, list):
                # Filter to only include valid options for the current strategy type
                valid_selections = [s for s in current_selections if s in type_options]
                # If no valid selections remain, use defaults
                if not valid_selections:
                    valid_selections = default_selections
            else:
                valid_selections = default_selections
            st.session_state[previous_type_key] = selected_type

        selected_subtypes = st.pills(
            "Series",
            options=type_options,
            selection_mode="multi",
            default=valid_selections,
            disabled=search_active,
            key="sidebar_series",
        )
        # Only add filter expressions when search is not active
        # When search is active, filters are disabled and we'll return search-only expression
        if not search_active:
            if selected_types:
                expressions.append(pl.col("Strategy Type").is_in(selected_types))
            if selected_subtypes:
                expressions.append(pl.col("Type").is_in(selected_subtypes))

        # ============================================================================
        # STEP 6: Render abbreviations section
        # ============================================================================
        st.divider()
        with st.expander("**Abbreviations**", icon=":material/menu_book:"):
            st.caption(f"last updated: {ABBREVIATIONS_UPDATE_DATE}")
            abbreviations_df = pl.read_csv("data/abbreviations.csv")
            st.dataframe(
                abbreviations_df,
                height="content",
            )
        
        # ============================================================================
        # STEP 7: Render TLH section
        # ============================================================================
        with st.expander("**Tax-Loss Harvesting (TLH)**", icon=":material/money_off:"):
            st.caption(f"last updated: {TLH_UPDATE_DATE}")
            tlh_df = pl.read_csv("data/tlh.csv")
            st.dataframe(
                tlh_df,
                height="content",
            )
        
        # ============================================================================
        # STEP 8: Render equivalents section
        # ============================================================================
        with st.expander("**Equivalents**", icon=":material/equal:"):
            st.caption(f"last updated: {EQUIVALENTS_UPDATE_DATE}")
            equivalents_df = pl.read_csv("data/equivalents.csv")
            st.dataframe(
                equivalents_df,
                height="content",
            )
        
        # ============================================================================
        # STEP 9: Render under development expander
        # ============================================================================
        with st.expander("**Under Development**", icon=":material/construction:"):
            st.caption(f"last updated: {UNDER_DEVELOPMENT_UPDATE_DATE}")
            with open("data/under_development.txt", "r", encoding="utf-8") as f:
                st.markdown(f.read())

    # ============================================================================
    # STEP 10: Return appropriate filter expression
    # ============================================================================
    # If search is active, return search-only expression (filters are disabled)
    if search_active and strategy_search:
        return (
            pl.col("Strategy")
            .str.to_lowercase()
            .str.contains(strategy_search.lower(), literal=True)
        )
    
    # Otherwise, combine all filter expressions with AND logic
    if not expressions:
        return pl.lit(True)
    
    combined_expr = expressions[0]
    for expr in expressions[1:]:
        combined_expr = combined_expr & expr
    return combined_expr
