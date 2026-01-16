from typing import Any

import polars as pl


def build_filter_expression(filters: dict[str, Any]) -> pl.Expr:
    """Build a Polars filter expression from the filters dictionary.
    
    When search_only_mode is True, only the strategy search filter is applied
    and all other filters are ignored.
    """
    strategy_search = filters.get("strategy_search")
    search_only_mode = filters.get("search_only_mode", False)
    
    # Search mode takes precedence - disables all other filters for focused lookup
    if search_only_mode and strategy_search:
        search_term = strategy_search.strip()
        if search_term:
            return (
                pl.col("Strategy")
                .str.to_lowercase()
                .str.contains(search_term.lower(), literal=True)
            )
        return pl.lit(True)
    
    expressions: list[pl.Expr] = []

    equity_range = filters["equity_range"]
    expressions.append(
        (pl.col("Equity %").is_not_null())
        & (pl.col("Equity %") >= equity_range[0])
        & (pl.col("Equity %") <= equity_range[1])
    )

    expressions.append(pl.col("Minimum") <= filters["min_strategy"])

    tax_managed = filters["tax_managed_filter"]
    if tax_managed != "All":
        expressions.append(pl.col("Tax-Managed") == (tax_managed == "Yes"))

    sma_manager = filters["has_sma_manager_filter"]
    if sma_manager != "All":
        expressions.append(pl.col("Has SMA Manager") == (sma_manager == "Yes"))

    private_markets = filters["private_markets_filter"]
    if private_markets == "Yes":
        expressions.append(pl.col("Private Markets"))
    elif private_markets == "No":
        expressions.append(~pl.col("Private Markets"))

    if filters["show_recommended"]:
        expressions.append(pl.col("Recommended"))

    selected_types = filters["selected_types"]
    if selected_types:
        expressions.append(pl.col("Strategy Type").is_in(selected_types))

    selected_subtypes = filters["selected_subtypes"]
    if selected_subtypes:
        expressions.append(pl.col("Type").is_in(selected_subtypes))

    # Search can be combined with filters in normal mode (though UI typically prevents this)
    if strategy_search:
        search_term = strategy_search.strip()
        if search_term:
            expressions.append(
                pl.col("Strategy")
                .str.to_lowercase()
                .str.contains(search_term.lower(), literal=True)
            )

    if not expressions:
        return pl.lit(True)

    combined_expr = expressions[0]
    for expr in expressions[1:]:
        combined_expr = combined_expr & expr
    return combined_expr
