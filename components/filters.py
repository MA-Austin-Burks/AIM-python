import polars as pl
import streamlit as st

# Type to subtype mapping
# Note: Keys must match ss_type values in the data ("Asset Class" not "Asset-Class")
TYPE_TO_SUBTYPE: dict[str, list[str]] = {
    "Risk-Based": [
        "Multifactor Series",
        "Market Series",
        "Income Series",
    ],
    "Asset Class": [
        "Equity Strategies",
        "Fixed Income Strategies",
        "Cash Strategies",
        "Alternative Strategies",
    ],
}


def _clear_search_state() -> None:
    """Clear search state."""
    st.session_state["_clear_search_flag"] = True


def _clear_search_flag_if_needed() -> None:
    """Clear search flag if needed."""
    if st.session_state.get("_clear_search_flag", False):
        st.session_state["strategy_search_input"] = ""
        st.session_state["_clear_search_flag"] = False


def _reset_filter_state() -> None:
    """Reset filter state."""
    st.session_state["filter_ic"] = "Recommended"
    st.session_state["filter_tm"] = None
    st.session_state["filter_sma"] = None
    st.session_state["filter_pm"] = None
    st.session_state["filter_vbi"] = None
    st.session_state["min_strategy"] = None
    st.session_state["equity_allocation_segmented"] = []
    st.session_state["filter_type"] = []
    st.session_state["filter_subtype"] = []
    st.session_state["_previous_type"] = []
    st.session_state["_previous_subtype"] = []
    st.session_state["equity_allocation_segmented"] = []


def _reset_all_state() -> None:
    """Reset all filter state."""
    _reset_filter_state()
    st.session_state["_clear_search_flag"] = True


def render_filters() -> None:
    """Render the filters UI."""
    _clear_search_flag_if_needed()

    with st.expander("Filters", expanded=True, icon=":material/feature_search:"):
        # Row 1
        search, clear_search, clear_filters, reset_all = st.columns([10, 3, 3, 3])

        with search:
            st.text_input(
                "Strategy Name:",
                value="",
                placeholder="Type to filter by strategy name...",
                key="strategy_search_input",
                max_chars=250,
                label_visibility="collapsed",
            )

        with clear_search:
            st.button(
                ":material/close: Clear search",
                key="clear_search_btn",
                width="stretch",
                on_click=_clear_search_state,
            )

        with clear_filters:
            st.button(
                ":material/filter_alt_off: Clear filters",
                key="clear_filters_btn",
                width="stretch",
                on_click=_reset_filter_state,
            )

        with reset_all:
            st.button(
                ":material/restart_alt: Reset all",
                key="reset_all_btn",
                width="stretch",
                on_click=_reset_all_state,
            )

        # Row 2
        st.space(1)
        ic, tm, sma, pm, vbi, min = st.columns([6, 3, 3, 3, 3, 4])

        with ic:
            st.segmented_control(
                label=":material/star: IC Status",
                options=["Recommended", "Recommended & Approved"],
                selection_mode="single",
                key="filter_ic",
                help=(
                    "Recommended strategies reflect the Investment Committee’s best thinking and adhere to our philosophy, while approved strategies may differ in asset allocation but remain rigorously reviewed; see FAQ for more information."
                ),
            )

        with tm:
            st.segmented_control(
                label=":material/savings: Tax-Managed (TM)",
                options=["Yes", "No"],
                selection_mode="single",
                key="filter_tm",
            )

        with sma:
            st.segmented_control(
                label=":material/tune: SMA Manager",
                options=["Yes", "No"],
                selection_mode="single",
                key="filter_sma",
            )

        with pm:
            st.segmented_control(
                label=":material/key: Private Markets",
                options=["Yes", "No"],
                selection_mode="single",
                key="filter_pm",
            )

        with vbi:
            st.segmented_control(
                label=":material/eco: Values-Based",
                options=["Yes", "No"],
                selection_mode="single",
                key="filter_vbi",
            )

        with min:
            st.number_input(
                ":material/attach_money: Current Account Value",
                min_value=0,
                value=None,
                step=10000,
                key="min_strategy",
                help="Input your current account value to show only strategies it qualifies for.",
            )

        # Row 3
        type, equity = st.columns([1.75, 3])

        with type:
            st.segmented_control(
                ":material/stat_minus_1: Type",
                options=["Risk-Based", "Asset Class", "Special Situation"],
                selection_mode="multi",
                key="filter_type",
            )

        # Equity Allocation segmented control (visible when Risk-Based is selected OR when Multifactor/Market/Income Series subtypes are selected)
        with equity:
            filter_type = st.session_state.get("filter_type", [])
            filter_subtype = st.session_state.get("filter_subtype", [])
            risk_based_subtypes = [
                "Multifactor Series",
                "Market Series",
                "Income Series",
            ]

            if "Risk-Based" in filter_type or any(
                subtype in filter_subtype for subtype in risk_based_subtypes
            ):
                equity_options = [f"{i}%" for i in range(0, 101, 10)]
                st.segmented_control(
                    "Equity Allocation (%)",
                    options=equity_options,
                    selection_mode="multi",
                    key="equity_allocation_segmented",
                )
            else:
                st.empty()

        # Row 4
        selected_type: list[str] = st.session_state.get("filter_type", [])
        previous_type: list[str] = st.session_state.get("_previous_type", [])
        current_subtype: list[str] = st.session_state.get("filter_subtype", [])
        previous_subtype: list[str] = st.session_state.get("_previous_subtype", [])

        if not selected_type:
            # Show all subtypes when no types are selected
            all_subtypes: list[str] = [
                subtype
                for subtype_list in TYPE_TO_SUBTYPE.values()
                for subtype in subtype_list
            ]
            type_options: list[str] = all_subtypes
        else:
            type_options: list[str] = []
            for st_type in selected_type:
                if st_type in TYPE_TO_SUBTYPE:
                    type_options.extend(TYPE_TO_SUBTYPE[st_type])

        # Always sort with Multifactor Series, Market Series, Income Series first
        priority_subtypes = ["Multifactor Series", "Market Series", "Income Series"]
        type_options = [
            subtype for subtype in priority_subtypes if subtype in type_options
        ] + [subtype for subtype in type_options if subtype not in priority_subtypes]

        # When types change, preserve eligible subtypes from previous selection
        if set(selected_type) != set(previous_type):
            # Combine current and previous subtypes to check (handles both first change and subsequent changes)
            # This ensures we preserve subtypes that were selected before type changes
            all_previous_subtypes = list(set(current_subtype + previous_subtype))

            # Find which previously selected subtypes are still eligible with new type selection
            eligible_subtypes = [
                subtype for subtype in all_previous_subtypes if subtype in type_options
            ]

            # Save current subtype selection before updating (for next type change)
            st.session_state["_previous_subtype"] = current_subtype.copy()

            # Restore eligible subtypes, or clear if none are eligible
            st.session_state["filter_subtype"] = eligible_subtypes
            st.session_state["_previous_type"] = selected_type.copy()

        st.segmented_control(
            ":material/stat_minus_2: Subtype",
            options=type_options,
            selection_mode="multi",
            key="filter_subtype",
        )


def build_filter_expression() -> pl.Expr:
    """Build filter expression from session state."""

    expressions: list[pl.Expr] = []

    # Search filter
    strategy_search_text: str = st.session_state.get("strategy_search_input", "")
    if strategy_search_text:
        sanitized: str = strategy_search_text.strip()
        if sanitized:
            expressions.append(
                pl.col("strategy")
                .str.to_lowercase()
                .str.contains(pattern=sanitized.lower(), literal=True)
            )

    # IC Status filter
    recommended_selection: str = st.session_state["filter_ic"]
    if recommended_selection == "Recommended":
        expressions.append(pl.col("ic_recommend"))

    # Tax-Managed filter
    tax_managed_selection: str | None = st.session_state["filter_tm"]
    if tax_managed_selection:
        if tax_managed_selection == "Yes":
            expressions.append(pl.col("has_tm"))
        elif tax_managed_selection == "No":
            expressions.append(~pl.col("has_tm"))

    # Has SMA Manager filter
    sma_selection: str | None = st.session_state["filter_sma"]
    if sma_selection:
        if sma_selection == "Yes":
            expressions.append(pl.col("has_sma"))
        elif sma_selection == "No":
            expressions.append(~pl.col("has_sma"))

    # Private Markets filter
    private_markets_selection: str | None = st.session_state["filter_pm"]
    if private_markets_selection:
        if private_markets_selection == "Yes":
            expressions.append(pl.col("has_private_market"))
        elif private_markets_selection == "No":
            expressions.append(~pl.col("has_private_market"))

    # VBI filter
    vbi_selection: str | None = st.session_state["filter_vbi"]
    if vbi_selection:
        if vbi_selection == "Yes":
            expressions.append(pl.col("has_VBI"))
        elif vbi_selection == "No":
            expressions.append(~pl.col("has_VBI"))

    # Account Value filter
    min_strategy: int | float | None = st.session_state["min_strategy"]
    if min_strategy is not None:
        expressions.append(pl.col("minimum").le(min_strategy))

    # Equity Allocation filter (only if Risk-Based is selected OR Multifactor/Market/Income Series subtypes are selected)
    # Combines equity allocation + alternative allocation (e.g., 65% equity + 15% alt = 80%)
    filter_type = st.session_state.get("filter_type", [])
    filter_subtype = st.session_state.get("filter_subtype", [])
    risk_based_subtypes = ["Multifactor Series", "Market Series", "Income Series"]

    if "Risk-Based" in filter_type or any(
        subtype in filter_subtype for subtype in risk_based_subtypes
    ):
        equity_selections: list[str] = st.session_state.get(
            "equity_allocation_segmented", []
        )
        if equity_selections:
            # Convert selected percentages (e.g., "0%", "10%", "20%") to numeric values
            equity_values = [int(val.rstrip("%")) for val in equity_selections]
            combined_allocation: pl.Expr = pl.col("equity_allo").fill_null(0) + pl.col(
                "private_allo"
            ).fill_null(0)
            expressions.append(combined_allocation.is_in(equity_values))

    # Type (multi-select) - Empty list means show all (none selected)
    type_value: list[str] = st.session_state.get("filter_type", [])
    if type_value:
        # Case-insensitive comparison to handle any capitalization differences
        type_value_lower = [v.lower() for v in type_value]
        expressions.append(pl.col("ss_type").str.to_lowercase().is_in(type_value_lower))

    # Subtype - Empty list means show all (none selected)
    subtype_value: list[str] = st.session_state.get("filter_subtype", [])
    if subtype_value:
        expressions.append(
            pl.col("ss_subtype").is_in(subtype_value)
        )  # TODO: check when database is updated

    # Combine all filter expressions with AND logic
    if not expressions:
        return pl.lit(True)

    combined_expr = expressions[0]
    for expr in expressions[1:]:
        combined_expr = combined_expr & expr
    return combined_expr
