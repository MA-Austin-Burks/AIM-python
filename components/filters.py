from typing import Any

import polars as pl


def build_filter_expression(filters: dict[str, Any]) -> pl.Expr:
    expressions: list[pl.Expr] = []

    # Equity range filter
    equity_range = filters["equity_range"]
    expressions.append(
        (pl.col(name="Equity %") >= equity_range[0])
        & (pl.col("Equity %") <= equity_range[1])
    )

    # Minimum strategy filter
    expressions.append(pl.col(name="Minimum") >= filters["min_strategy"])

    # Tax managed filter
    tax_managed = filters["tax_managed_filter"]
    if tax_managed != "All":
        expressions.append(pl.col(name="Tax Managed") == (tax_managed == "Yes"))

    # SMA manager filter
    sma_manager = filters["has_sma_manager_filter"]
    if sma_manager != "All":
        expressions.append(pl.col(name="Has SMA Manager") == (sma_manager == "Yes"))

    # IC status filter
    show_recommended = filters.get("show_recommended")
    show_approved = filters.get("show_approved")
    status_filters: list = []
    if show_recommended:
        status_filters.append("Recommended")
    if show_approved:
        status_filters.append("Approved")
    if status_filters:
        expressions.append(pl.col(name="IC Status").is_in(status_filters))

    # Strategy type filter
    selected_types = filters.get("selected_types")
    if selected_types:
        expressions.append(pl.col(name="Strategy Type").is_in(selected_types))

    # Strategy subtype filter
    selected_subtypes = filters.get("selected_subtypes")
    if selected_subtypes:
        expressions.append(pl.col(name="Strategy Subtype").is_in(selected_subtypes))

    # Strategy search filter
    strategy_search = filters.get("strategy_search")
    if strategy_search and (search_term := strategy_search.strip()):
        expressions.append(
            pl.col(name="Strategy")
            .str.to_lowercase()
            .str.contains(search_term.lower(), literal=True)
        )

    # Manager filter
    selected_managers = filters.get("selected_managers")
    if selected_managers:
        expressions.append(pl.col(name="Manager").is_in(selected_managers))

    if not expressions:
        return pl.lit(True)

    combined_expr = expressions[0]
    for expr in expressions[1:]:
        combined_expr = combined_expr & expr
    return combined_expr
