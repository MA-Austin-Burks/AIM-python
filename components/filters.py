import polars as pl
import streamlit as st

# Filter options lists
STRATEGY_TYPES: list[str] = ["Risk-Based", "Asset-Class", "Special Situation"]

# Mapping of strategy types to their available series options
STRATEGY_TYPE_TO_SERIES: dict[str, list[str]] = {
    "Risk-Based": [
        "Multifactor Series",
        "Market Series",
        "Income Series",
    ],
    "Asset-Class": [
        "Equity Strategies",
        "Fixed Income Strategies",
        "Cash Strategies",
        "Alternative Strategies",
    ],
    "Special Situation": [
        "Special Situation Strategies",
    ],
}

SERIES_OPTIONS: list[str] = [
    series for series_list in STRATEGY_TYPE_TO_SERIES.values() for series in series_list
]

# Update dates
ABBREVIATIONS_UPDATE_DATE: str = "2026-01-17"
EQUIVALENTS_UPDATE_DATE: str = "2026-01-17"
TLH_UPDATE_DATE: str = "2026-01-17"
UNDER_DEVELOPMENT_UPDATE_DATE: str = "2026-01-17"



def _migrate_filter_keys() -> None:
    """Migrate old sidebar filter keys to new filter keys (one-time migration)."""
    key_migrations = {
        "sidebar_tax_managed": "filter_tax_managed",
        "sidebar_sma_manager": "filter_sma_manager",
        "sidebar_private_markets": "filter_private_markets",
        "sidebar_strategy_type": "filter_strategy_type",
        "sidebar_series": "filter_series",
    }
    
    for old_key, new_key in key_migrations.items():
        if old_key in st.session_state and new_key not in st.session_state:
            st.session_state[new_key] = st.session_state[old_key]
    
    # Migrate boolean filter_recommended_only to string format
    if "filter_recommended_only" in st.session_state:
        current_value = st.session_state["filter_recommended_only"]
        if isinstance(current_value, bool):
            st.session_state["filter_recommended_only"] = "Yes" if current_value else "No"


def _render_yes_no_filter(label: str, key: str, disabled: bool) -> str | None:
    """Render a boolean filter segmented control with Yes/No options."""
    return st.segmented_control(
        label,
        options=["Yes", "No"],
        selection_mode="single",
        default=None,
        disabled=disabled,
        key=key,
    )


def render_search_bar() -> tuple[bool, str | None]:
    """Render search bar UI and return (search_active, strategy_search)."""
    # Check if we need to clear search (must be done before any widgets are created)
    if st.session_state.get("_clear_search_flag", False):
        st.session_state["strategy_search_input"] = ""
        st.session_state["_clear_search_flag"] = False
    
    col_search, col_clear = st.columns([10, 2])
    with col_search:
        strategy_search_text = st.text_input(
            "Strategy Name:",
            value="",
            placeholder="Type to filter by strategy name...",
            key="strategy_search_input",
        )
    with col_clear:
        st.space()
        if st.button(":material/close: Clear", key="clear_search_btn", use_container_width=True):
            st.session_state["_clear_search_flag"] = True
            st.rerun()
    
    # Search mode disables filters to prevent confusion (search is OR, filters are AND)
    search_active = bool(strategy_search_text and strategy_search_text.strip())
    strategy_search = strategy_search_text.strip() if strategy_search_text else None
    
    return search_active, strategy_search


def render_filters_inline(search_active: bool) -> None:
    """Render filter controls inline in two rows above Order By.
    
    Args:
        search_active: Whether search is currently active (disables filters)
    """
    # Migrate old sidebar filter keys to new filter keys (one-time migration)
    _migrate_filter_keys()
    
    # Change expander label when search is active
    expander_label = "Filters (Clear search to enable)" if search_active else "Filters"
    
    with st.expander(expander_label, expanded=False, icon=":material/feature_search:"):
        # Row 1: Yes/No filters, then Account Value and Equity Allocation at the end
        col_rec, col_tax, col_sma, col_private, col_min, col_equity = st.columns([1, 1, 1, 1, 2, 2])
        
        with col_rec:
            # Get current selection or use default "Yes"
            current_selection = st.session_state.get("filter_recommended_only", "Yes")
            st.segmented_control(
                "IC Recommended",
                options=["Yes", "No"],
                selection_mode="single",
                default=current_selection if current_selection in ["Yes", "No"] else "Yes",
                disabled=search_active,
                key="filter_recommended_only",
            )
        
        with col_tax:
            _render_yes_no_filter(
                label="Tax-Managed (TM)", key="filter_tax_managed", disabled=search_active
            )
        
        with col_sma:
            _render_yes_no_filter(
                label="Has SMA Manager", key="filter_sma_manager", disabled=search_active
            )
        
        with col_private:
            _render_yes_no_filter(
                label="Private Markets", key="filter_private_markets", disabled=search_active
            )
        
        with col_min:
            st.number_input(
                "Account Value ($)",
                min_value=0,
                value=50000,
                step=10000,
                key="min_strategy",
                disabled=search_active,
            )
        
        with col_equity:
            st.slider(
                "Equity Allocation Range",
                min_value=0,
                max_value=100,
                value=(0, 100),
                step=10,
                key="equity_range",
                disabled=search_active,
            )
        
        # Row 2: Strategy Type, Series
        strategy_types: list[str] = ["Risk-Based", "Asset-Class", "Special Situation"]
        default_type: str = "Risk-Based"
        
        col_type, col_series = st.columns([3, 3])
        
        with col_type:
            # Get current selection or use default
            current_selection = st.session_state.get("filter_strategy_type", default_type)
            st.segmented_control(
                "Strategy Type",
                options=strategy_types,
                selection_mode="single",
                default=current_selection if current_selection in strategy_types else default_type,
                disabled=search_active,
                key="filter_strategy_type",
            )
        
        with col_series:
            # Get current strategy type to determine series options
            selected_type = st.session_state.get("filter_strategy_type", default_type)
            previous_type_key = "_previous_strategy_type"
            previous_type = st.session_state.get(previous_type_key, default_type)
            
            # Dynamically filter series options based on selected strategy type
            if selected_type and selected_type in STRATEGY_TYPE_TO_SERIES:
                type_options: list[str] = STRATEGY_TYPE_TO_SERIES[selected_type]
            else:
                type_options: list[str] = SERIES_OPTIONS

            # Determine default selections based on strategy type
            if selected_type == "Risk-Based":
                default_selections = ["Multifactor Series", "Market Series", "Income Series"]
            elif selected_type == "Asset-Class":
                default_selections = []
            elif selected_type == "Special Situation":
                default_selections = ["Special Situation Strategies"]
            else:
                default_selections = []

            # Handle strategy type changes by clearing invalid selections
            if selected_type != previous_type:
                st.session_state.pop("filter_series", None)
                st.session_state[previous_type_key] = selected_type
                valid_selections = default_selections
            else:
                current_selections = st.session_state.get("filter_series", default_selections)
                if isinstance(current_selections, list):
                    valid_selections = [s for s in current_selections if s in type_options]
                    if not valid_selections:
                        valid_selections = default_selections
                else:
                    valid_selections = default_selections
                st.session_state[previous_type_key] = selected_type

            # Use segmented control for multi-select Series
            st.segmented_control(
                "Series",
                options=type_options,
                selection_mode="multi",
                default=valid_selections,
                disabled=search_active,
                key="filter_series",
            )


def render_filters(search_active: bool) -> pl.Expr:
    """Build filter expression from session state (filters are rendered inline via render_filters_inline).
    
    Args:
        search_active: Whether search is currently active (disables filters)
    """
    # Initialize filter expression list
    expressions: list[pl.Expr] = []

    # If search is active, return search-only expression (filters are disabled)
    if search_active:
        strategy_search_text = st.session_state.get("strategy_search_input", "")
        strategy_search = strategy_search_text.strip() if strategy_search_text else None
        if strategy_search:
            return (
                pl.col("Strategy")
                .str.to_lowercase()
                .str.contains(strategy_search.lower(), literal=True)
            )
        return pl.lit(True)
    
    # Build filter expressions from session state
    # Investment Committee Recommended
    recommended_selection = st.session_state.get("filter_recommended_only", "Yes")
    if recommended_selection == "Yes":
        expressions.append(pl.col("Recommended"))
    # If "No" or None, show all strategies (don't filter by Recommended)
    
    # Account Value
    min_strategy = st.session_state.get("min_strategy", 50000)
    expressions.append(pl.col("Minimum") <= min_strategy)
    
    # Equity Allocation Range
    equity_range = st.session_state.get("equity_range", (0, 100))
    expressions.append(
        (pl.col("Equity %").is_not_null())
        & (pl.col("Equity %") >= equity_range[0])
        & (pl.col("Equity %") <= equity_range[1])
    )
    
    # Tax-Managed
    tax_managed_selection = st.session_state.get("filter_tax_managed")
    if tax_managed_selection:
        expressions.append(pl.col("Tax-Managed") == (tax_managed_selection == "Yes"))
    
    # Has SMA Manager
    has_sma_manager_selection = st.session_state.get("filter_sma_manager")
    if has_sma_manager_selection:
        expressions.append(pl.col("Has SMA Manager") == (has_sma_manager_selection == "Yes"))
    
    # Private Markets
    private_markets_selection = st.session_state.get("filter_private_markets")
    if private_markets_selection:
        if private_markets_selection == "Yes":
            expressions.append(pl.col("Private Markets"))
        elif private_markets_selection == "No":
            expressions.append(~pl.col("Private Markets"))
    
    # Strategy Type
    selected_type = st.session_state.get("filter_strategy_type", "Risk-Based")
    if selected_type:
        expressions.append(pl.col("Strategy Type").is_in([selected_type]))
    
    # Series
    selected_subtypes = st.session_state.get("filter_series", [])
    # Ensure it's always a list (segmented_control with multi-select returns a list)
    if selected_subtypes is None:
        selected_subtypes = []
    elif not isinstance(selected_subtypes, list):
        selected_subtypes = [selected_subtypes]
    if selected_subtypes:
        expressions.append(pl.col("Type").is_in(selected_subtypes))

    # Combine all filter expressions with AND logic
    if not expressions:
        return pl.lit(True)
    
    combined_expr = expressions[0]
    for expr in expressions[1:]:
        combined_expr = combined_expr & expr
    return combined_expr


def render_reference_data() -> None:
    """Render reference data sections in the main content area."""
    # ============================================================================
    # Render abbreviations section
    # ============================================================================
    with st.expander("Abbreviations", icon=":material/menu_book:"):
        st.caption(f"last updated: {ABBREVIATIONS_UPDATE_DATE}")
        abbreviations_df = pl.read_csv("data/abbreviations.csv")
        st.dataframe(
            abbreviations_df,
            height="content",
        )
    
    # ============================================================================
    # Render TLH section
    # ============================================================================
    with st.expander("Tax-Loss Harvesting (TLH)", icon=":material/money_off:"):
        st.caption(f"last updated: {TLH_UPDATE_DATE}")
        tlh_df = pl.read_csv("data/tlh.csv")
        st.dataframe(
            tlh_df,
            height="content",
        )
    
    # ============================================================================
    # Render equivalents section
    # ============================================================================
    with st.expander("Equivalents", icon=":material/equal:"):
        st.caption(f"last updated: {EQUIVALENTS_UPDATE_DATE}")
        equivalents_df = pl.read_csv("data/equivalents.csv")
        st.dataframe(
            equivalents_df,
            height="content",
        )
    
    # ============================================================================
    # Render under development expander
    # ============================================================================
    with st.expander("Under Development", icon=":material/construction:"):
        st.caption(f"last updated: {UNDER_DEVELOPMENT_UPDATE_DATE}")
        with open("data/under_development.txt", "r", encoding="utf-8") as f:
            st.markdown(f.read())


def render_sidebar() -> None:
    """Render sidebar content (currently empty, kept for future use)."""
    pass
