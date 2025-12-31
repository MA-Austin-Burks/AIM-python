"""Filters component for the Aspen Investing Menu app."""

import polars as pl


def build_filter_expression(filters: dict) -> pl.Expr:
    expressions: list[pl.Expr] = []

    # Equity range filter
    equity_range = filters["equity_range"]
    expressions.append(
        (pl.col("Equity %") >= equity_range[0])
        & (pl.col("Equity %") <= equity_range[1])
    )

    # Account Value filter - show strategies where account value meets minimum threshold
    expressions.append(pl.col("Minimum") <= filters["min_strategy"])

    # Tax managed filter
    tax_managed = filters["tax_managed_filter"]
    if tax_managed != "All":
        expressions.append(pl.col("Tax-Managed") == (tax_managed == "Yes"))

    # SMA manager filter
    sma_manager = filters["has_sma_manager_filter"]
    if sma_manager != "All":
        expressions.append(pl.col("Has SMA Manager") == (sma_manager == "Yes"))

    # Private Markets filter - filter for strategies with "All Weather" in name
    private_markets = filters.get("private_markets_filter")
    if private_markets == "Yes":
        expressions.append(
            pl.col("Strategy")
            .str.to_lowercase()
            .str.contains("all weather", literal=False)
        )
    elif private_markets == "No":
        expressions.append(
            ~pl.col("Strategy")
            .str.to_lowercase()
            .str.contains("all weather", literal=False)
        )

    # Recommended filter
    show_recommended = filters.get("show_recommended")
    if show_recommended:
        expressions.append(pl.col("Recommended"))

    # Strategy type filter
    selected_types = filters.get("selected_types")
    if selected_types:
        expressions.append(pl.col("Strategy Type").is_in(selected_types))

    # Type filter (Series)
    selected_subtypes = filters.get("selected_subtypes")
    if selected_subtypes:
        expressions.append(pl.col("Type").is_in(selected_subtypes))

    # Strategy search filter
    strategy_search = filters.get("strategy_search")
    if strategy_search and (search_term := strategy_search.strip()):
        expressions.append(
            pl.col("Strategy")
            .str.to_lowercase()
            .str.contains(search_term.lower(), literal=True)
        )

    # Manager filter
    selected_managers = filters.get("selected_managers")
    if selected_managers:
        expressions.append(pl.col("Manager").is_in(selected_managers))

    if not expressions:
        return pl.lit(True)

    combined_expr = expressions[0]
    for expr in expressions[1:]:
        combined_expr = combined_expr & expr
    return combined_expr
