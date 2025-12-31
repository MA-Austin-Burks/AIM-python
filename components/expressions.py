"""Polars expressions for data formatting."""

import polars as pl


def fmt_tax_managed(col: str = "Tax Managed") -> pl.Expr:
    """Format tax managed boolean column."""
    return (
        pl.when(pl.col(col).is_not_null())
        .then(pl.col(col).cast(pl.String).replace({"true": "Yes", "false": "No"}))
        .otherwise(pl.lit(""))
        .alias("Tax-Managed")
    )