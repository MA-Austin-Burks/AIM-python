import polars as pl


def build_filter_expression(filters):
    expressions = []

    equity_range = filters["equity_range"]
    expressions.append(
        (pl.col("Equity %") >= equity_range[0])
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

    strategy_search = filters["strategy_search"]
    if strategy_search:
        search_term = strategy_search.strip()
        if search_term:
            expressions.append(
                pl.col("Strategy")
                .str.to_lowercase()
                .str.contains(search_term.lower(), literal=True)
            )

    selected_managers = filters["selected_managers"]
    if selected_managers:
        expressions.append(pl.col("Manager").is_in(selected_managers))

    if not expressions:
        return pl.lit(True)

    combined_expr = expressions[0]
    for expr in expressions[1:]:
        combined_expr = combined_expr & expr
    return combined_expr
