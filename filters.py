"""Filtering logic for strategies."""

from typing import Any

import polars as pl


def adjust_filters_for_strategy(
    strats: pl.DataFrame, strategy_name: str
) -> dict[str, Any]:
    """
    Adjust filter values to match the selected strategy's attributes.

    Args:
        strats: The strategies dataframe
        strategy_name: Name of the selected strategy

    Returns:
        Dictionary with adjusted filter values. Returns empty dict if strategy not found.

    Example:
        >>> filters = adjust_filters_for_strategy(df, "My Strategy")
        >>> filters.get("strategy_type")
        ["Risk-Based"]
    """
    if strats.is_empty() or "strategy" not in strats.columns:
        return {}

    strategy_row = strats.filter(pl.col("strategy") == strategy_name).head(1)

    if len(strategy_row) == 0:
        return {}

    row = strategy_row.to_dicts()[0]

    return {
        "strategy_type": [row.get("strategy_type")]
        if row.get("strategy_type")
        else None,
        "strategy_subtype": [row.get("strategy_subtype")]
        if row.get("strategy_subtype")
        else None,
        "tax_managed": "Yes" if row.get("tax_managed") else "No",
        "status": [row.get("Status")] if row.get("Status") else None,
    }


def build_filter_expression(
    filters: dict[str, Any], strats: pl.DataFrame | None = None
) -> pl.Expr:
    """
    Build a combined filter expression from filter dictionary.

    Args:
        filters: Dictionary containing filter values with keys:
            - equity_range: Tuple[int, int] - (min, max) equity allocation
            - min_strategy: int - Minimum strategy value
            - tax_managed_filter: str - "All", "Yes", or "No"
            - show_recommended: bool - Include recommended strategies
            - show_approved: bool - Include approved strategies
            - selected_types: list[str] - Selected strategy types
            - selected_subtypes: list[str] - Selected strategy subtypes
            - strategy_search: str | None - Search term for strategy name
            - selected_managers: list[str] - Selected managers

    Returns:
        Combined Polars filter expression

    Example:
        >>> filters = {
        ...     "equity_range": (0, 100),
        ...     "min_strategy": 20000,
        ...     "tax_managed_filter": "All",
        ...     "show_recommended": True,
        ...     "show_approved": True,
        ...     "selected_types": [],
        ...     "selected_subtypes": [],
        ... }
        >>> expr = build_filter_expression(df, filters)
    """
    # Get equity_range with safe defaults
    equity_range = filters.get("equity_range", (0, 100))
    if not isinstance(equity_range, tuple) or len(equity_range) != 2:
        equity_range = (0, 100)  # Default to no filtering

    # Build base filter expression
    # Equity % is stored as percentage (0-100), divide by 100 for comparison
    filter_expr = ((pl.col("Equity %") / 100) >= (equity_range[0] / 100)) & (
        (pl.col("Equity %") / 100) <= (equity_range[1] / 100)
    )

    # Minimum strategy filter
    min_strategy = filters.get("min_strategy", 0)
    if min_strategy > 0:
        filter_expr = filter_expr & (pl.col("minimum") >= min_strategy)

    # Tax-managed filter
    tax_managed_filter = filters.get("tax_managed_filter", "All")
    if tax_managed_filter != "All":
        filter_expr = filter_expr & (pl.col("Tax-Managed") == tax_managed_filter)

    # Has SMA Manager filter (only if column exists)
    has_sma_manager_filter = filters.get("has_sma_manager_filter", "All")
    if (
        has_sma_manager_filter != "All"
        and strats is not None
        and "Has SMA Manager" in strats.columns
    ):
        filter_expr = filter_expr & (
            pl.col("Has SMA Manager") == has_sma_manager_filter
        )

    # Status filters - build list only if needed
    status_filters = []
    if filters.get("show_recommended", False):
        status_filters.append("Recommended")
    if filters.get("show_approved", False):
        status_filters.append("Approved")
    if status_filters:
        filter_expr = filter_expr & pl.col("Status").is_in(status_filters)

    # Strategy type filter
    selected_types = filters.get("selected_types", [])
    if selected_types:
        filter_expr = filter_expr & pl.col("strategy_type").is_in(selected_types)

    # Strategy subtype filter
    selected_subtypes = filters.get("selected_subtypes", [])
    if selected_subtypes:
        filter_expr = filter_expr & pl.col("strategy_subtype").is_in(selected_subtypes)

    # Strategy name search filter - case-insensitive contains filter
    strategy_search = filters.get("strategy_search")
    if strategy_search:
        search_term = strategy_search.strip()
        if search_term:
            filter_expr = filter_expr & (
                pl.col("strategy")
                .str.to_lowercase()
                .str.contains(search_term.lower(), literal=True)
            )

    # Manager filter - supports multiple selections (only if column exists)
    selected_managers = filters.get("selected_managers", [])
    if selected_managers and strats is not None and "Manager" in strats.columns:
        filter_expr = filter_expr & pl.col("Manager").is_in(selected_managers)

    return filter_expr
