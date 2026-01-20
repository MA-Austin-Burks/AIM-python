import polars as pl
import streamlit as st

from utils.core.constants import (
    ABBREVIATIONS_UPDATE_DATE,
    EQUIVALENTS_UPDATE_DATE,
    STRATEGY_TYPE_TO_SERIES,
    STRATEGY_TYPES,
    TLH_UPDATE_DATE,
    UNDER_DEVELOPMENT_UPDATE_DATE,
)
from utils.security import MAX_SEARCH_INPUT_LENGTH, validate_search_input

# Series options derived from strategy type mapping
SERIES_OPTIONS: list[str] = [
    series for series_list in STRATEGY_TYPE_TO_SERIES.values() for series in series_list
]



def _render_yes_no_filter(label: str, key: str, disabled: bool, default: str | None = None) -> str | None:
    """Render a boolean filter segmented control with Yes/No options.
    
    Args:
        label: Label for the filter control
        key: Session state key for the filter
        disabled: Whether the filter is disabled
        default: Default selection ("Yes", "No", or None)
    """
    return st.segmented_control(
        label,
        options=["Yes", "No"],
        selection_mode="single",
        default=default,
        disabled=disabled,
        key=key,
    )


def render_search_bar() -> tuple[bool, str | None]:
    """Render search bar UI and return (search_active, strategy_search)."""
    # Check if we need to clear search (must be done before any widgets are created)
    if st.session_state["_clear_search_flag"]:
        st.session_state["strategy_search_input"] = ""
        st.session_state["_clear_search_flag"] = False
    
    col_search, col_clear = st.columns([10, 2])
    with col_search:
        strategy_search_text = st.text_input(
            "Strategy Name:",
            value="",
            placeholder="Type to filter by strategy name...",
            key="strategy_search_input",
            max_chars=MAX_SEARCH_INPUT_LENGTH,
        )
    with col_clear:
        st.space()
        if st.button(":material/close: Clear", key="clear_search_btn", use_container_width=True):
            st.session_state["_clear_search_flag"] = True
            st.rerun()
    
    # Search mode disables filters to prevent confusion (search is OR, filters are AND)
    # Validate and sanitize search input
    try:
        strategy_search = validate_search_input(strategy_search_text)
        search_active = bool(strategy_search)
    except ValueError as e:
        # If validation fails, show error and reset search
        st.error(str(e))
        st.session_state["strategy_search_input"] = ""
        strategy_search = None
        search_active = False
    
    return search_active, strategy_search


def render_filters_inline(search_active: bool) -> None:
    """Render filter controls inline in two rows above Order By.
    
    Args:
        search_active: Whether search is currently active (disables filters)
    """
    # Change expander label when search is active
    expander_label = "Filters (Clear search to enable)" if search_active else "Filters"
    
    with st.expander(expander_label, expanded=False, icon=":material/feature_search:"):
        # Row 1: IC Status, Yes/No filters, Account Value
        col_ic, col_tax, col_sma, col_private, col_min = st.columns([1, 1, 1, 1, 2])
        
        with col_ic:
            # IC Status: Recommended / All
            current_ic_status = st.session_state.get("filter_recommended_only", "Recommended")
            st.segmented_control(
                "IC Status",
                options=["Recommended", "All"],
                selection_mode="single",
                default=current_ic_status if current_ic_status in ["Recommended", "All"] else "Recommended",
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
            from utils.core.constants import DEFAULT_MIN_STRATEGY
            
            st.number_input(
                "Account Value ($)",
                min_value=0,
                value=DEFAULT_MIN_STRATEGY,
                step=10000,
                key="min_strategy",
                disabled=search_active,
            )
        
        # Row 2: Strategy Type (multi-select), Series, Equity Allocation (always visible, disabled when Risk-Based not selected)
        selected_type = st.session_state.get("filter_strategy_type", STRATEGY_TYPES[0])
        if not isinstance(selected_type, list):
            selected_type = [selected_type] if selected_type else STRATEGY_TYPES
        
        is_risk_based = "Risk-Based" in selected_type
        
        # Always show equity allocation column
        col_type, col_series, col_equity = st.columns([2, 2, 2])
        
        with col_type:
            # Strategy Type: multi-select
            current_selections = st.session_state.get("filter_strategy_type", STRATEGY_TYPES)
            if not isinstance(current_selections, list):
                current_selections = [current_selections] if current_selections else STRATEGY_TYPES
            
            st.segmented_control(
                "Strategy Type",
                options=STRATEGY_TYPES,
                selection_mode="multi",
                default=current_selections,
                disabled=search_active,
                key="filter_strategy_type",
            )
        
        with col_series:
            # Session state is initialized, so we can access directly
            selected_type = st.session_state.get("filter_strategy_type", STRATEGY_TYPES[0])
            if not isinstance(selected_type, list):
                selected_type = [selected_type] if selected_type else STRATEGY_TYPES
            
            previous_type_key = "_previous_strategy_type"
            previous_type = st.session_state.get(previous_type_key, STRATEGY_TYPES[0])
            if not isinstance(previous_type, list):
                previous_type = [previous_type] if previous_type else []
            
            # Get all series options for selected strategy types
            type_options: list[str] = []
            for st_type in selected_type:
                if st_type in STRATEGY_TYPE_TO_SERIES:
                    type_options.extend(STRATEGY_TYPE_TO_SERIES[st_type])
            
            # Remove duplicates while preserving order
            type_options = list(dict.fromkeys(type_options))
            
            if not type_options:
                type_options = SERIES_OPTIONS

            # Determine default selections based on strategy types
            default_selections = []
            for st_type in selected_type:
                if st_type in STRATEGY_TYPE_TO_SERIES:
                    default_selections.extend(STRATEGY_TYPE_TO_SERIES[st_type])
            default_selections = list(dict.fromkeys(default_selections))

            # Handle strategy type changes by clearing invalid selections
            if set(selected_type) != set(previous_type):
                st.session_state.pop("filter_series", None)
                st.session_state[previous_type_key] = selected_type
                valid_selections = default_selections
            else:
                # Session state is initialized, so we can access directly
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
        
        # Equity Allocation slider (disabled when Risk-Based is not selected)
        with col_equity:
            equity_value = st.session_state.get("equity_allocation", 60)
            st.slider(
                "Equity Allocation (%)",
                min_value=0,
                max_value=100,
                value=equity_value,
                step=10,
                key="equity_allocation",
                disabled=search_active or not is_risk_based,
            )


def _build_search_filter(strategy_search: str | None) -> pl.Expr:
    """Build search filter expression.
    
    Args:
        strategy_search: Sanitized search text
        
    Returns:
        Polars expression for search filter
    """
    if not strategy_search:
        return pl.lit(True)
    
    return (
        pl.col("Strategy")
        .str.to_lowercase()
        .str.contains(strategy_search.lower(), literal=True)
    )


def _build_recommended_filter(recommended_selection: str | None) -> pl.Expr | None:
    """Build recommended filter expression.
    
    Args:
        recommended_selection: "Recommended", "All", or None
        
    Returns:
        Polars expression or None if no filter needed
    """
    if recommended_selection == "Recommended":
        return pl.col("Recommended")
    return None


def _build_account_value_filter(min_strategy: int | float) -> pl.Expr:
    """Build account value filter expression.
    
    Args:
        min_strategy: Minimum account value
        
    Returns:
        Polars expression for account value filter
    """
    return pl.col("Minimum") <= min_strategy


def _build_equity_allocation_filter(equity_allocation: int | None) -> pl.Expr | None:
    """Build equity allocation filter expression.
    
    Args:
        equity_allocation: Single equity percentage value or None
        
    Returns:
        Polars expression for equity allocation filter or None if not filtering
    """
    if equity_allocation is None:
        return None
    # Filter within ±5% of the selected value
    return (
        (pl.col("Equity %").is_not_null())
        & (pl.col("Equity %") >= equity_allocation - 5)
        & (pl.col("Equity %") <= equity_allocation + 5)
    )


def _build_boolean_filter(column_name: str, selection: str | None) -> pl.Expr | None:
    """Build boolean filter expression for Yes/No filters.
    
    Args:
        column_name: Column name to filter on
        selection: "Yes", "No", or None
        
    Returns:
        Polars expression or None if no filter needed
    """
    if not selection:
        return None
    return pl.col(column_name) == (selection == "Yes")


def _build_private_markets_filter(selection: str | None) -> pl.Expr | None:
    """Build private markets filter expression.
    
    Args:
        selection: "Yes", "No", or None
        
    Returns:
        Polars expression or None if no filter needed
    """
    if not selection:
        return None
    if selection == "Yes":
        return pl.col("Private Markets")
    elif selection == "No":
        return ~pl.col("Private Markets")
    return None


def _build_strategy_type_filter(selected_types: list[str] | str | None) -> pl.Expr | None:
    """Build strategy type filter expression.
    
    Args:
        selected_types: List of strategy types, single strategy type, or None
        
    Returns:
        Polars expression or None if no filter needed
    """
    if not selected_types:
        return None
    if isinstance(selected_types, str):
        selected_types = [selected_types]
    if not selected_types:
        return None
    return pl.col("Strategy Type").is_in(selected_types)


def _build_series_filter(selected_subtypes: list[str] | str | None) -> pl.Expr | None:
    """Build series filter expression.
    
    Args:
        selected_subtypes: List of series, single series, or None
        
    Returns:
        Polars expression or None if no filter needed
    """
    if selected_subtypes is None:
        return None
    if not isinstance(selected_subtypes, list):
        selected_subtypes = [selected_subtypes]
    if not selected_subtypes:
        return None
    return pl.col("Type").is_in(selected_subtypes)


def _combine_filter_expressions(expressions: list[pl.Expr]) -> pl.Expr:
    """Combine filter expressions with AND logic.
    
    Args:
        expressions: List of Polars expressions
        
    Returns:
        Combined expression
    """
    if not expressions:
        return pl.lit(True)
    
    combined_expr = expressions[0]
    for expr in expressions[1:]:
        combined_expr = combined_expr & expr
    return combined_expr


def render_filters(search_active: bool) -> pl.Expr:
    """Build filter expression from session state (filters are rendered inline via render_filters_inline).
    
    Args:
        search_active: Whether search is currently active (disables filters)
    """
    # If search is active, return search-only expression (filters are disabled)
    if search_active:
        strategy_search_text = st.session_state["strategy_search_input"]
        try:
            strategy_search = validate_search_input(strategy_search_text)
        except ValueError:
            return pl.lit(True)
        return _build_search_filter(strategy_search)
    
    # Build filter expressions from session state
    expressions: list[pl.Expr] = []
    
    # Investment Committee Recommended
    recommended_expr = _build_recommended_filter(st.session_state["filter_recommended_only"])
    if recommended_expr is not None:
        expressions.append(recommended_expr)
    
    # Account Value
    expressions.append(_build_account_value_filter(st.session_state["min_strategy"]))
    
    # Equity Allocation (only if Risk-Based is selected and equity_allocation is set)
    selected_type = st.session_state.get("filter_strategy_type", STRATEGY_TYPES[0])
    if isinstance(selected_type, list):
        is_risk_based = "Risk-Based" in selected_type
    else:
        is_risk_based = selected_type == "Risk-Based"
    
    if is_risk_based:
        equity_allocation = st.session_state.get("equity_allocation")
        equity_expr = _build_equity_allocation_filter(equity_allocation)
        if equity_expr is not None:
            expressions.append(equity_expr)
    
    # Tax-Managed
    tax_managed_expr = _build_boolean_filter("Tax-Managed", st.session_state["filter_tax_managed"])
    if tax_managed_expr is not None:
        expressions.append(tax_managed_expr)
    
    # Has SMA Manager
    sma_expr = _build_boolean_filter("Has SMA Manager", st.session_state["filter_sma_manager"])
    if sma_expr is not None:
        expressions.append(sma_expr)
    
    # Private Markets
    private_markets_expr = _build_private_markets_filter(st.session_state["filter_private_markets"])
    if private_markets_expr is not None:
        expressions.append(private_markets_expr)
    
    # Strategy Type (multi-select)
    strategy_type_value = st.session_state.get("filter_strategy_type", STRATEGY_TYPES)
    if not isinstance(strategy_type_value, list):
        strategy_type_value = [strategy_type_value] if strategy_type_value else STRATEGY_TYPES
    strategy_type_expr = _build_strategy_type_filter(strategy_type_value)
    if strategy_type_expr is not None:
        expressions.append(strategy_type_expr)
    
    # Series
    series_expr = _build_series_filter(st.session_state["filter_series"])
    if series_expr is not None:
        expressions.append(series_expr)
    
    # Combine all filter expressions with AND logic
    return _combine_filter_expressions(expressions)


@st.cache_data(ttl=3600)
def _load_abbreviations() -> pl.DataFrame:
    """Load abbreviations CSV file (cached for 1 hour)."""
    return pl.read_csv("data/abbreviations.csv")


@st.cache_data(ttl=3600)
def _load_tlh() -> pl.DataFrame:
    """Load TLH CSV file (cached for 1 hour)."""
    return pl.read_csv("data/tlh.csv")


@st.cache_data(ttl=3600)
def _load_equivalents() -> pl.DataFrame:
    """Load equivalents CSV file (cached for 1 hour)."""
    return pl.read_csv("data/equivalents.csv")


@st.cache_data(ttl=3600)
def _load_explanation_card() -> str:
    """Load explanation card text file (cached for 1 hour)."""
    with open("data/explanation_card.txt", "r", encoding="utf-8") as f:
        return f.read()


@st.cache_data(ttl=3600)
def _load_under_development() -> str:
    """Load under development text file (cached for 1 hour)."""
    with open("data/under_development.txt", "r", encoding="utf-8") as f:
        return f.read()


def render_reference_data() -> None:
    """Render reference data sections in the main content area."""
    # ============================================================================
    # Render abbreviations section
    # ============================================================================
    with st.expander("Abbreviations", icon=":material/menu_book:"):
        st.caption(f"last updated: {ABBREVIATIONS_UPDATE_DATE}")
        abbreviations_df: pl.DataFrame = _load_abbreviations()
        st.dataframe(
            abbreviations_df,
            height="content",
        )
    
    # ============================================================================
    # Render TLH section
    # ============================================================================
    with st.expander("Tax-Loss Harvesting (TLH)", icon=":material/money_off:"):
        st.caption(f"last updated: {TLH_UPDATE_DATE}")
        tlh_df: pl.DataFrame = _load_tlh()
        st.dataframe(
            tlh_df,
            height="content",
        )
    
    # ============================================================================
    # Render equivalents section
    # ============================================================================
    with st.expander("Equivalents", icon=":material/equal:"):
        st.caption(f"last updated: {EQUIVALENTS_UPDATE_DATE}")
        equivalents_df: pl.DataFrame = _load_equivalents()
        st.dataframe(
            equivalents_df,
            height="content",
        )
    
    # ============================================================================
    # Render under development expander
    # ============================================================================
    with st.expander("Under Development", icon=":material/construction:"):
        st.caption(f"last updated: {UNDER_DEVELOPMENT_UPDATE_DATE}")
        under_development_text: str = _load_under_development()
        st.markdown(under_development_text)
