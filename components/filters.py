"""Filtering logic for strategies."""

from typing import Any

import polars as pl


def build_filter_expression(
    filters: dict[str, Any], strats: pl.DataFrame | None = None
) -> pl.Expr:
    """
    Build a combined filter expression from filter dictionary.
    """
    equity_range: tuple[int, int] = filters.get("equity_range", (0, 100))
    if not isinstance(equity_range, tuple) or len(equity_range) != 2:
        equity_range: tuple[int, int] = (0, 100)

    equity_col: pl.Expr = pl.col("Equity %")
    filter_expr: pl.Expr = (equity_col >= equity_range[0]) & (
        equity_col <= equity_range[1]
    )

    min_strategy: int = filters.get("min_strategy", 0)
    if min_strategy > 0:
        filter_expr: pl.Expr = filter_expr & (pl.col(name="Minimum") >= min_strategy)

    tax_managed_filter: str = filters.get("tax_managed_filter", "All")
    if tax_managed_filter != "All":
        tax_managed_bool: bool = tax_managed_filter == "Yes"
        filter_expr: pl.Expr = filter_expr & (
            pl.col(name="Tax Managed") == tax_managed_bool
        )

    has_sma_manager_filter: str = filters.get("has_sma_manager_filter", "All")
    if (
        has_sma_manager_filter != "All"
        and strats is not None
        and "Has SMA Manager" in strats.columns
    ):
        filter_expr: pl.Expr = filter_expr & (
            pl.col(name="Has SMA Manager") == has_sma_manager_filter
        )

    status_filters: list[str] = []
    if filters.get("show_recommended", False):
        status_filters: list[str] = ["Recommended"]
    if filters.get("show_approved", False):
        status_filters: list[str] = ["Approved"]
    if status_filters:
        status_col_name: str = (
            "IC Status"
            if strats is not None and "IC Status" in strats.columns
            else "Status"
        )
        filter_expr: pl.Expr = filter_expr & pl.col(name=status_col_name).is_in(
            status_filters
        )

    selected_types: list[str] = filters.get("selected_types", [])
    if selected_types:
        filter_expr: pl.Expr = filter_expr & pl.col(name="Strategy Type").is_in(
            selected_types
        )

    selected_subtypes: list[str] = filters.get("selected_subtypes", [])
    if selected_subtypes:
        filter_expr: pl.Expr = filter_expr & pl.col(name="Strategy Subtype").is_in(
            selected_subtypes
        )

    strategy_search: str | None = filters.get("strategy_search")
    if strategy_search and (search_term := strategy_search.strip()):
        filter_expr: pl.Expr = filter_expr & (
            pl.col(name="Strategy")
            .str.to_lowercase()
            .str.contains(search_term.lower(), literal=True)
        )

    selected_managers: list[str] = filters.get("selected_managers", [])
    if selected_managers and strats is not None and "Manager" in strats.columns:
        filter_expr: pl.Expr = filter_expr & pl.col(name="Manager").is_in(
            selected_managers
        )

    return filter_expr
