"""Filtering logic for strategies."""

from typing import Any

import polars as pl


def build_filter_expression(
    filters: dict[str, Any], strats: pl.DataFrame | None = None
) -> pl.Expr:
    """
    Build a combined filter expression from filter dictionary.
    """
    # Get equity_range with safe defaults
    equity_range = filters.get("equity_range", (0, 100))
    if not isinstance(equity_range, tuple) or len(equity_range) != 2:
        equity_range = (0, 100)

    # Build base filter expression - Equity % is stored as percentage (0-100)
    equity_col = pl.col("Equity %")
    filter_expr = (equity_col >= equity_range[0]) & (equity_col <= equity_range[1])

    # Minimum strategy filter
    min_strategy = filters.get("min_strategy", 0)
    if min_strategy > 0:
        filter_expr = filter_expr & (pl.col("Minimum") >= min_strategy)

    # Tax-managed filter - use "Tax Managed" boolean column
    tax_managed_filter = filters.get("tax_managed_filter", "All")
    if tax_managed_filter != "All":
        # Convert filter value to boolean: "Yes" -> True, "No" -> False
        tax_managed_bool = tax_managed_filter == "Yes"
        filter_expr = filter_expr & (pl.col("Tax Managed") == tax_managed_bool)

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
    # Note: Status values are in "IC Status" column, not "Status" column
    status_filters = []
    if filters.get("show_recommended", False):
        status_filters.append("Recommended")
    if filters.get("show_approved", False):
        status_filters.append("Approved")
    if status_filters:
        # Use "IC Status" column which contains the actual status values
        status_col_name = (
            "IC Status"
            if strats is not None and "IC Status" in strats.columns
            else "Status"
        )
        filter_expr = filter_expr & pl.col(status_col_name).is_in(status_filters)

    # Strategy type filter
    selected_types = filters.get("selected_types", [])
    if selected_types:
        filter_expr = filter_expr & pl.col("Strategy Type").is_in(selected_types)

    # Strategy subtype filter
    selected_subtypes = filters.get("selected_subtypes", [])
    if selected_subtypes:
        filter_expr = filter_expr & pl.col("Strategy Subtype").is_in(selected_subtypes)

    # Strategy name search filter - case-insensitive contains filter
    strategy_search = filters.get("strategy_search")
    if strategy_search and (search_term := strategy_search.strip()):
        filter_expr = filter_expr & (
            pl.col("Strategy")
            .str.to_lowercase()
            .str.contains(search_term.lower(), literal=True)
        )

    # Manager filter - supports multiple selections (only if column exists)
    selected_managers = filters.get("selected_managers", [])
    if selected_managers and strats is not None and "Manager" in strats.columns:
        filter_expr = filter_expr & pl.col("Manager").is_in(selected_managers)

    return filter_expr
