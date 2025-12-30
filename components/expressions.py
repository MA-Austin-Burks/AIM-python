"""Polars expressions for data formatting."""

import polars as pl


def fmt_pct(col: str) -> pl.Expr:
    """Format a percentage column."""
    return (
        pl.when(pl.col(col).is_not_null())
        .then((pl.col(col) * 100).round(2).cast(pl.String) + "%")
        .otherwise(pl.lit(""))
    )


def fmt_cur(col: str) -> pl.Expr:
    """Format a currency column with comma separators."""
    return (
        pl.when(pl.col(col).is_not_null())
        .then(
            pl.col(col)
            .cast(pl.Int64)
            .map_elements(lambda x: f"${x:,}", return_dtype=pl.String)
        )
        .otherwise(pl.lit(""))
    )


def fmt_dec(col: str) -> pl.Expr:
    """Format a decimal column as percentage with two decimals."""
    return (
        pl.when(pl.col(col).is_not_null())
        .then((pl.col(col) * 100).round(2).cast(pl.String))
        .otherwise(pl.lit(""))
    )


def fmt_equity_pct(col: str = "Equity %") -> pl.Expr:
    """Format equity percentage column."""
    return (
        pl.when(pl.col(col).is_not_null())
        .then(pl.col(col).round(2).cast(pl.String) + "%")
        .otherwise(pl.lit(""))
        .alias(col)
    )


def fmt_tax_managed(col: str = "Tax Managed") -> pl.Expr:
    """Format tax managed boolean column."""
    return (
        pl.when(pl.col(col).is_not_null())
        .then(pl.col(col).cast(pl.String).replace({"true": "Yes", "false": "No"}))
        .otherwise(pl.lit(""))
        .alias("Tax-Managed")
    )