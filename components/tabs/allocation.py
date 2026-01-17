from typing import Any

import polars as pl
import streamlit as st
from great_tables import GT, loc, style

from styles.branding import (
    PRIMARY,
    hex_to_rgba,
)
from styles import (
    get_allocation_table_main_css,
    get_allocation_table_summary_css,
)
from components.constants import (
    ALLOCATION_COLLAPSE_SMA_KEY,
    DEFAULT_COLLAPSE_SMA,
    SMA_COLLAPSE_THRESHOLD,
)
from utils.core.data import get_model_agg_sort_order, get_strategy_by_name, hash_lazyframe
from utils.core.formatting import clean_product_name, format_currency_compact, get_strategy_color


def _is_not_none(value: str | None) -> bool:
    """Type guard to filter out None values."""
    return value is not None


@st.cache_data(hash_funcs={pl.LazyFrame: hash_lazyframe})
def _get_model_data(cleaned_data: pl.LazyFrame, strategy_model: str) -> pl.DataFrame:
    """Get and cache all data for a specific model.
    """
    return (
        cleaned_data
        .filter(pl.col("model") == strategy_model)
        .select(["strategy", "portfolio", "model_agg", "product", "ticker", "target", "agg_target", "weight", "fee", "yield", "minimum"])
        .collect()
    )


@st.cache_data(hash_funcs={pl.LazyFrame: hash_lazyframe})
def _get_equity_matrix_data(
    cleaned_data: pl.LazyFrame,
    strategy_name: str,
    strategy_equity_pct: float,
    collapse_sma: bool = DEFAULT_COLLAPSE_SMA,
) -> tuple[pl.DataFrame, int, list[dict[str, Any]], dict[int, str]]:
    """Get allocation data in matrix format with equity % columns.
    """
    # Get the strategy's model to find related strategies
    strategy_data: dict[str, Any] | None = get_strategy_by_name(cleaned_data, strategy_name)
    strategy_model: str = strategy_data["model"]
    strategy_type: str = strategy_data["type"]
    strategy_color: str = get_strategy_color(strategy_type)
    
    all_model_data: pl.DataFrame = _get_model_data(cleaned_data, strategy_model)
    
    selected_strategy_data: pl.DataFrame = all_model_data.filter(pl.col("strategy") == strategy_name)
    
    all_strategies: pl.DataFrame = (
        all_model_data
        .select(["strategy", "portfolio"])
        .unique()
        .sort("portfolio", descending=True)
    )
    
    equity_to_strategy: dict[int, str] = {}
    for row in all_strategies.iter_rows(named=True):
        equity_to_strategy[int(row["portfolio"])] = row["strategy"]
    
    # Only show columns for equity levels that exist
    available_equity_levels: list[int] = [
        eq for eq in [100, 90, 80, 70, 60, 50, 40, 30, 20, 10] 
        if eq in equity_to_strategy
    ]
    
    model_aggs: list[str | None] = sorted(
        [ma for ma in selected_strategy_data["model_agg"].unique().to_list() if ma is not None],
        key=get_model_agg_sort_order
    )
    
    matrix_data: list[dict[str, Any]] = []
    row_metadata: list[dict[str, Any]] = []
    
    # Track which model_agg is the last one for the spacer row
    last_model_agg: str | None = model_aggs[-1] if model_aggs else None
    
    # Pre-process model agg names: remove "Portfolio" suffix
    model_agg_names: dict[str | None, str] = {
        ma: str(ma).replace(" Portfolio", "").replace("Portfolio", "")
        for ma in model_aggs
    }
    
    # Iterate over model aggs to build the matrix data
    for model_agg in model_aggs:
        model_agg_name: str = model_agg_names[model_agg]
        row_data: dict[str, Any] = {"asset": model_agg_name, "ticker": ""}
        row_metadata.append({
            "is_category": True, 
            "name": model_agg_name,
            "ticker": "",
            "color": strategy_color
        })
        
        # Model agg rows show total allocation percentage (agg_target)
        # Product rows below show individual product allocations (weight)
        for equity_pct in available_equity_levels:
            if equity_pct in equity_to_strategy:
                strategy_name_at_equity: str = equity_to_strategy[equity_pct]
                strategy_data: pl.DataFrame = all_model_data.filter(
                    (pl.col("strategy") == strategy_name_at_equity) &
                    (pl.col("model_agg") == model_agg)
                )
                
                if strategy_data.height > 0:
                    agg_target: float = strategy_data["agg_target"].first()
                    row_data[str(int(equity_pct))] = float(agg_target)
                else:
                    row_data[str(int(equity_pct))] = 0.0
            else:
                row_data[str(int(equity_pct))] = None
        
        matrix_data.append(row_data)
        
        products = (
            selected_strategy_data
            .filter(pl.col("model_agg") == model_agg)
            .select(["product", "ticker", "weight"])
            .sort("weight", descending=True)
        )
        
        # Collapse SMAs with many holdings to reduce visual clutter
        # Threshold prevents overwhelming users with long product lists
        num_products = products.height
        should_collapse = collapse_sma and num_products > SMA_COLLAPSE_THRESHOLD
        
        if not should_collapse:
            for product_row in products.iter_rows(named=True):
                product_name_raw = product_row["product"]
                product_name = clean_product_name(product_name_raw)
                ticker = product_row["ticker"]
                
                product_row_data = {"asset": product_name, "ticker": ticker if ticker else ""}
                row_metadata.append({
                    "is_category": False, 
                    "name": product_name,
                    "ticker": ticker if ticker else "",
                    "color": strategy_color
                })
                
                # Product allocations shown across all equity levels for comparison
                for equity_pct in available_equity_levels:
                    if equity_pct in equity_to_strategy:
                        strategy_name_at_equity = equity_to_strategy[equity_pct]
                        
                        # Use pre-collected data for performance
                        if strategy_name_at_equity == strategy_name:
                            strategy_data = selected_strategy_data.filter(
                                (pl.col("model_agg") == model_agg) &
                                (pl.col("ticker") == ticker)
                            )
                            if strategy_data.height > 0:
                                # weight stored as decimal (0-1), represents final portfolio allocation
                                weight_val = strategy_data["weight"][0]
                                prod_weight = float(weight_val) if weight_val is not None else 0.0
                                product_row_data[str(int(equity_pct))] = prod_weight
                            else:
                                product_row_data[str(int(equity_pct))] = 0.0
                        else:
                            strategy_data = all_model_data.filter(
                                (pl.col("strategy") == strategy_name_at_equity) &
                                (pl.col("model_agg") == model_agg) &
                                (pl.col("ticker") == ticker)
                            )
                            
                            if strategy_data.height > 0:
                                weight_val = strategy_data["weight"][0]
                                prod_weight = float(weight_val) if weight_val is not None else 0.0
                                product_row_data[str(int(equity_pct))] = prod_weight
                            else:
                                product_row_data[str(int(equity_pct))] = 0.0
                    else:
                        product_row_data[str(int(equity_pct))] = None
                
                matrix_data.append(product_row_data)
        
        # Visual spacing between model aggregations improves readability
        # Spacer only added if products exist (even if collapsed) and not last model_agg
        if products.height > 0 and model_agg != last_model_agg:
            spacer_row = {"asset": "", "ticker": ""}
            for equity_pct in available_equity_levels:
                spacer_row[str(int(equity_pct))] = None
            matrix_data.append(spacer_row)
            row_metadata.append({
                "is_category": False,
                "is_spacer": True,
                "name": "",
                "ticker": "",
                "color": strategy_color
            })
    
    df = pl.DataFrame(matrix_data)
    
    # Highlight the column corresponding to the selected strategy's equity percentage
    # Helps users quickly identify their strategy's allocation column
    highlighted_col_idx = 0
    if strategy_equity_pct is not None:
        try:
            equity_int = int(strategy_equity_pct)
            if equity_int in available_equity_levels:
                highlighted_col_idx = available_equity_levels.index(equity_int) + 2
        except (ValueError, TypeError):
            pass
    
    return df, highlighted_col_idx, row_metadata, equity_to_strategy


def render_allocation_tab(strategy_name: str, filters: dict[str, Any], cleaned_data: pl.LazyFrame) -> None:
    """Render allocation tab with matrix table showing allocations across equity percentages."""
    # Use cached strategy data instead of repeated filter/collect
    strategy_data = get_strategy_by_name(cleaned_data, strategy_name)
    strategy_equity_pct = None
    model_name = None
    if strategy_data:
        strategy_equity_pct = strategy_data.get("portfolio")
        # Model name preferred over strategy name for header (more general)
        model_name = strategy_data.get("model")
    
    collapse_sma = st.session_state.get(ALLOCATION_COLLAPSE_SMA_KEY, DEFAULT_COLLAPSE_SMA)
    
    # Get model data for summary table (cached)
    if strategy_data and strategy_data.get("model"):
        all_model_data = _get_model_data(cleaned_data, strategy_data["model"])
    else:
        all_model_data = pl.DataFrame()
    
    matrix_df, highlighted_col_idx, row_metadata, equity_to_strategy = _get_equity_matrix_data(
        cleaned_data, strategy_name, strategy_equity_pct, collapse_sma=collapse_sma
    )
    
    if matrix_df.height == 0:
        st.info("No allocation data available for this strategy.")
        return
    
    equity_cols = [col for col in matrix_df.columns if col not in ["asset", "ticker"]]
    
    # Prepare metadata for styling: category rows get background color, products get indentation
    is_category_list = [meta["is_category"] for meta in row_metadata]
    row_colors = [meta.get("color", PRIMARY["raspberry"]) for meta in row_metadata]
    
    # Indent product names to show hierarchy (model_agg -> products)
    asset_names = []
    ticker_values = []
    for meta in row_metadata:
        name = meta["name"]
        ticker = meta.get("ticker", "")
        is_spacer = meta.get("is_spacer", False)
        if is_spacer:
            name = '<span style="display: block; height: 4px;"></span>'
        elif not meta["is_category"]:
            name = f'<span style="padding-left: 20px;">{name}</span>'
        asset_names.append(name)
        ticker_values.append(ticker if ticker else "")
    
    matrix_df = matrix_df.with_columns([
        pl.Series("is_category", is_category_list),
        pl.Series("asset_formatted", asset_names),
        pl.Series("ticker_formatted", ticker_values),
        pl.Series("row_color", row_colors),
    ])
    
    # Hidden columns used for styling logic, formatted columns for display
    column_order = ["asset_formatted", "ticker_formatted"] + equity_cols + ["is_category", "asset", "ticker", "row_color"]
    matrix_df = matrix_df.select(column_order)

    strategy_color = row_metadata[0]["color"] if row_metadata else PRIMARY["raspberry"]
    
    if model_name:
        header_name = str(model_name)
    else:
        header_name = strategy_name.replace(" Portfolio", "").replace("Portfolio", "")
    table = (
        GT(matrix_df)
        .cols_hide(["is_category", "asset", "ticker", "row_color"])
        .cols_label(asset_formatted=header_name, ticker_formatted="")
        .fmt_percent(columns=equity_cols, decimals=2)
        .sub_missing(columns=equity_cols, missing_text="")
        .cols_align(columns=equity_cols, align="center")
        .cols_align(columns=["asset_formatted"], align="left")
        .cols_align(columns=["ticker_formatted"], align="center")
    )
    
    # Header uses strategy color for brand consistency
    table = table.tab_style(
        style=[
            style.fill(color=strategy_color),
            style.text(color="white", weight="bold", size="1.0rem"),
        ],
        locations=loc.column_labels(),
    )
    
    # Category rows use pastel background to visually group products underneath
    for idx, meta in enumerate(row_metadata):
        if meta["is_category"]:
            row_color = meta["color"]
            rgba_color = hex_to_rgba(row_color, alpha=0.15)
            table = table.tab_style(
                style=[
                    style.fill(color=rgba_color),
                    style.text(color="black", weight="bold"),
                ],
                locations=loc.body(columns=pl.all(), rows=[idx]),
            )
    
    table = table.tab_options(
        table_font_size="0.875rem",
        table_font_names=[
            "IBM Plex Sans",
            "-apple-system",
            "BlinkMacSystemFont",
            "Segoe UI",
            "sans-serif",
        ]
    )
    
    # Highlight selected strategy's equity column for quick identification
    if highlighted_col_idx >= 2 and highlighted_col_idx - 2 < len(equity_cols):
        highlighted_col = equity_cols[highlighted_col_idx - 2]
        table = table.tab_style(
            style=[
                style.fill(color="#fff3cd"),
            ],
            locations=loc.body(columns=[highlighted_col]),
        )

    # Fixed widths for asset/ticker ensure consistent layout
    # Equity columns share remaining space equally for balanced comparison
    num_equity_cols = len(equity_cols)
    asset_col_width = "30%"
    ticker_col_width = "10%"
    equity_col_width = f"{(60 / num_equity_cols):.2f}%" if num_equity_cols > 0 else "0%"
    
    # Render table using Great Tables with fixed column widths
    st.html(f"""
    <div style="width: 100%; margin: 0 !important; padding: 0 !important;">
        <style>
            {get_allocation_table_main_css(asset_col_width, ticker_col_width, equity_col_width)}
        </style>
        <div id="allocation-table-main">
            {table.as_raw_html(inline_css=True)}
        </div>
    </div>
    """)
    
    # Summary table shows key metrics across all equity levels for quick comparison
    # Use already-collected model data instead of filtering again
    all_strategies_data = (
        all_model_data
        .filter(pl.col("strategy").is_in(list(equity_to_strategy.values())))
        .select(["strategy", "portfolio", "target", "fee", "yield", "minimum"])
    )
    
    summary_rows = {
        "Weighted Expense Ratio": {"Metric": "Weighted Expense Ratio"},
        "Weighted Indicated Yield": {"Metric": "Weighted Indicated Yield"},
        "Account Minimum": {"Metric": "Account Minimum"}
    }
    
    # Calculate metrics for each equity level that exists in the model
    for equity_col in equity_cols:
        try:
            equity_pct = int(equity_col)
        except ValueError:
            continue
        
        if equity_pct not in equity_to_strategy:
            continue
        
        strategy_at_equity = equity_to_strategy[equity_pct]
        strategy_data = all_strategies_data.filter(pl.col("strategy") == strategy_at_equity)
        
        if strategy_data.height == 0:
            continue
        
        # Weighted averages account for different allocation sizes across products
        total_target = strategy_data["target"].sum()
        if total_target > 0:
            weighted_expense = (strategy_data["target"] * strategy_data["fee"]).sum() / total_target
            weighted_yield = (strategy_data["target"] * strategy_data["yield"]).sum() / total_target
        else:
            weighted_expense = 0.0
            weighted_yield = 0.0
        
        account_min = strategy_data["minimum"].first()
        
        summary_rows["Weighted Expense Ratio"][str(equity_pct)] = f"{float(weighted_expense) * 100:.2f}%" if weighted_expense else "0.00%"
        summary_rows["Weighted Indicated Yield"][str(equity_pct)] = f"{float(weighted_yield) * 100:.2f}%" if weighted_yield else "0.00%"
        summary_rows["Account Minimum"][str(equity_pct)] = format_currency_compact(float(account_min)) if account_min else "$0"
    
    # Build summary table
    summary_table_data = [
        summary_rows["Weighted Expense Ratio"],
        summary_rows["Weighted Indicated Yield"],
        summary_rows["Account Minimum"]
    ]
    
    summary_df = pl.DataFrame(summary_table_data)
    
    # Column alignment critical for visual comparison between main and summary tables
    for col in equity_cols:
        if col not in summary_df.columns:
            summary_df = summary_df.with_columns(pl.lit(None).alias(col))
    
    summary_column_order = ["Metric"] + equity_cols
    summary_df = summary_df.select([col for col in summary_column_order if col in summary_df.columns])
    summary_equity_cols = [col for col in equity_cols if col in summary_df.columns]
    
    # Render summary table with aligned columns
    summary_table = (
        GT(summary_df)
        .cols_label(**{col: col for col in summary_equity_cols})
        .cols_align(columns=summary_equity_cols, align="center")
        .cols_align(columns=["Metric"], align="left")
        .tab_style(
            style=[
                style.fill(color=strategy_color),
                style.text(color="white", weight="bold", size="1.0rem"),
            ],
            locations=loc.column_labels(),
        )
        .tab_options(
            table_font_size="0.875rem",
            table_font_names=[
                "IBM Plex Sans",
                "-apple-system",
                "BlinkMacSystemFont",
                "Segoe UI",
                "sans-serif",
            ],
            column_labels_hidden=True  # Hide the header row
        )
    )
    
    # Match highlight from main table for consistency
    if highlighted_col_idx >= 2 and highlighted_col_idx - 2 < len(summary_equity_cols):
        highlighted_col = summary_equity_cols[highlighted_col_idx - 2]
        summary_table = summary_table.tab_style(
            style=[
                style.fill(color="#fff3cd"),
            ],
            locations=loc.body(columns=[highlighted_col]),
        )
    
    # Metric column width matches asset+ticker combined width for perfect alignment
    summary_metric_col_width = f"{(float(asset_col_width.rstrip('%')) + float(ticker_col_width.rstrip('%'))):.2f}%"
    
    st.html(f"""
    <div style="width: 100%; margin-top: 4px;">
        <style>
            {get_allocation_table_summary_css(summary_metric_col_width, equity_col_width)}
        </style>
        <div id="allocation-table-summary">
            {summary_table.as_raw_html(inline_css=True)}
        </div>
    </div>
    """)
    
    st.checkbox(
        "Collapse SMAs",
        value=st.session_state.get(ALLOCATION_COLLAPSE_SMA_KEY, DEFAULT_COLLAPSE_SMA),
        key=ALLOCATION_COLLAPSE_SMA_KEY
    )
    