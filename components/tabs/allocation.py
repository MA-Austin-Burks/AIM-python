from typing import Any

import polars as pl
import streamlit as st
from great_tables import GT, loc, style

from styles.branding import (
    PRIMARY,
    SECONDARY,
    TERTIARY,
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
from utils.core.data import get_model_agg_sort_order, hash_lazyframe
from utils.core.formatting import clean_product_name, format_currency_compact, get_strategy_color

CATEGORY_COLORS: dict[str, str] = {
    "Equity": PRIMARY["raspberry"],
    "Bonds": TERTIARY["azure"],
    "Alternative": SECONDARY["iris"],
    "Cash": TERTIARY["spring"],
    "Other": PRIMARY["charcoal"],
    "Fixed Income": TERTIARY["azure"],
}




def _get_color_for_group(group_name: str, grouping_option: str) -> str:
    """Get color for a group based on grouping option."""
    if grouping_option == "Asset Category":
        return CATEGORY_COLORS.get(group_name, PRIMARY["charcoal"])
    
    # Hash-based assignment ensures same group name always gets same color
    # Important for consistency when switching between grouping options
    import hashlib
    hash_val = int(hashlib.md5(group_name.encode()).hexdigest()[:6], 16)
    colors = [
        PRIMARY["raspberry"],
        TERTIARY["azure"],
        SECONDARY["iris"],
        TERTIARY["spring"],
        PRIMARY["charcoal"],
        TERTIARY["gold"],
    ]
    return colors[hash_val % len(colors)]


@st.cache_data(hash_funcs={pl.LazyFrame: hash_lazyframe})
def get_grouped_allocations_for_chart(
    cleaned_data: pl.LazyFrame,
    strategy_name: str,
    grouping_option: str,
    total_assets: float,
) -> list[dict[str, Any]]:
    """Get grouped allocation data for pie chart only."""
    strategy_data = cleaned_data.filter(pl.col("strategy") == strategy_name)
    
    # Ensure grouping_option is valid, default to "Asset Type" if None
    if grouping_option is None:
        grouping_option = "Asset Type"
    
    group_column_map = {
        "Asset Category": "asset_category",
        "Asset Type": "asset_type",
        "Asset Class": "asset_class",
        "Product": "product",
    }
    
    if grouping_option not in group_column_map:
        grouping_option = "Asset Type"
    
    group_column = group_column_map[grouping_option]
    
    grouped = (
        strategy_data
        .group_by(group_column)
        .agg([
            pl.sum("weight").alias("total_weight"),
        ])
        .filter(
            pl.col(group_column).is_not_null() &
            (pl.col(group_column) != "")
        )
        .sort("total_weight", descending=True)
        .collect()
    )
    
    data = []
    for row in grouped.iter_rows(named=True):
        group_name_raw = str(row[group_column])
        # Product names cleaned for readability (removes redundant "ETF" suffix)
        group_name = clean_product_name(group_name_raw) if grouping_option == "Product" else group_name_raw
        # weight is stored as decimal (0-1), convert to percentage
        allocation_pct = float(row["total_weight"]) * 100
        color = _get_color_for_group(group_name, grouping_option)
        
        data.append({
            "name": group_name,
            "allocation": allocation_pct,
            "market_value": total_assets * allocation_pct / 100,
            "color": color,
        })
    
    # If more than 15 items, combine the rest into "Others"
    if len(data) > 15:
        top_15 = data[:15]
        others_allocation = sum(item["allocation"] for item in data[15:])
        others_market_value = sum(item["market_value"] for item in data[15:])
        
        # Use a neutral color for "Others"
        others_color = PRIMARY["charcoal"]
        
        top_15.append({
            "name": "Others",
            "allocation": others_allocation,
            "market_value": others_market_value,
            "color": others_color,
        })
        
        return top_15
    
    return data


@st.cache_data(hash_funcs={pl.LazyFrame: hash_lazyframe})
def _get_equity_matrix_data(
    cleaned_data: pl.LazyFrame,
    strategy_name: str,
    strategy_equity_pct: float,
    collapse_sma: bool = DEFAULT_COLLAPSE_SMA,
) -> tuple[pl.DataFrame, int, list[dict[str, Any]], dict[int, str]]:
    """Get allocation data in matrix format with equity % columns.
    
    Returns:
        DataFrame with model_agg and products as rows, equity percentages as columns
        Index of the highlighted column (selected strategy's equity %)
        List of row metadata (is_category, name) for styling
    """
    # Get the strategy's model to find related strategies
    strategy_row = cleaned_data.filter(pl.col("strategy") == strategy_name).first().collect()
    if strategy_row.height == 0:
        return pl.DataFrame(), 0, [], {}
    
    strategy_model = strategy_row["model"][0]
    strategy_type = strategy_row["type"][0]
    strategy_color = get_strategy_color(strategy_type)
    
    # TM models don't have 100% equity allocation (replaced with muni bonds)
    is_tax_managed = strategy_row["tax_managed"][0] if "tax_managed" in strategy_row.columns else False
    
    # Collect all model data upfront to avoid repeated LazyFrame filtering in loops
    # Performance optimization: single collect vs many filter operations
    all_model_data = (
        cleaned_data
        .filter(pl.col("model") == strategy_model)
        .select(["strategy", "portfolio", "model_agg", "product", "ticker", "target", "agg_target", "weight", "fee", "yield", "minimum"])
        .collect()
    )
    
    selected_strategy_data = all_model_data.filter(pl.col("strategy") == strategy_name)
    
    all_strategies = (
        all_model_data
        .select(["strategy", "portfolio"])
        .unique()
        .sort("portfolio", descending=True)
    )
    
    # Map equity percentage to strategy name for O(1) lookup
    equity_to_strategy = {}
    for row in all_strategies.iter_rows(named=True):
        equity_to_strategy[int(row["portfolio"])] = row["strategy"]
    
    # Only show columns for equity levels that exist for this model
    # Some models may not have all standard allocations (e.g., missing 10% or 20%)
    equity_levels = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]
    available_equity_levels = [eq for eq in equity_levels if eq in equity_to_strategy]
    
    # TM models use muni bonds instead of taxable bonds at 100% equity
    if is_tax_managed and 100 in available_equity_levels:
        available_equity_levels.remove(100)
    
    # Sort model aggregations to match R spreadsheet ordering
    # Ensures consistent display order across different strategies in same model
    model_aggs = selected_strategy_data["model_agg"].unique().to_list()
    has_none = None in model_aggs
    model_aggs_filtered = [ma for ma in model_aggs if ma is not None]
    
    model_aggs_sorted = sorted(model_aggs_filtered, key=get_model_agg_sort_order)
    if has_none:
        model_aggs_sorted.append(None)
    model_aggs = model_aggs_sorted
    
    # Pre-compute totals to avoid repeated calculations when scaling product allocations
    model_agg_totals = {}
    for strategy in equity_to_strategy.values():
        strategy_data = all_model_data.filter(pl.col("strategy") == strategy)
        for model_agg in strategy_data["model_agg"].unique().to_list():
            if model_agg is not None:
                key = (strategy, model_agg)
                # agg_target is consistent across all products in a model_agg
                agg_target_data = strategy_data.filter(pl.col("model_agg") == model_agg)
                if agg_target_data.height > 0:
                    total = agg_target_data["agg_target"].first()
                    model_agg_totals[key] = float(total) if total else 0.0
                else:
                    model_agg_totals[key] = 0.0
    
    matrix_data = []
    row_metadata = []
    
    # Track which model_agg is the last one (excluding None values)
    valid_model_aggs = [ma for ma in model_aggs if ma is not None]
    last_model_agg = valid_model_aggs[-1] if valid_model_aggs else None
    
    for model_agg in model_aggs:
        if model_agg is None:
            continue
        
        # Remove redundant "Portfolio" suffix from display names
        model_agg_name = str(model_agg).replace(" Portfolio", "").replace("Portfolio", "")
        row_data = {"asset": model_agg_name, "ticker": ""}
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
                strategy_name_at_equity = equity_to_strategy[equity_pct]
                # Use pre-collected data instead of filtering
                strategy_data = all_model_data.filter(
                    (pl.col("strategy") == strategy_name_at_equity) &
                    (pl.col("model_agg") == model_agg)
                )
                
                if strategy_data.height > 0:
                    # agg_target stored as decimal (0-1), not percentage
                    agg_target = strategy_data["agg_target"].first()
                    row_data[str(int(equity_pct))] = float(agg_target) if agg_target else 0.0
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
    strategy_row = cleaned_data.filter(pl.col("strategy") == strategy_name).first().collect()
    strategy_equity_pct = None
    model_name = None
    if strategy_row.height > 0:
        strategy_equity_pct = strategy_row["portfolio"][0]
        # Model name preferred over strategy name for header (more general)
        if "model" in strategy_row.columns:
            model_name = strategy_row["model"][0]
        elif "model_name" in strategy_row.columns:
            model_name = strategy_row["model_name"][0]
    
    collapse_sma = st.session_state.get(ALLOCATION_COLLAPSE_SMA_KEY, DEFAULT_COLLAPSE_SMA)
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
    all_strategies_data = (
        cleaned_data
        .filter(pl.col("strategy").is_in(list(equity_to_strategy.values())))
        .select(["strategy", "portfolio", "target", "fee", "yield", "minimum"])
        .collect()
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
    
    # Add toggle for SMA settings at the bottom of the page
    st.divider()
    st.checkbox(
        f"Collapse SMAs (>{SMA_COLLAPSE_THRESHOLD} holdings)",
        value=st.session_state.get(ALLOCATION_COLLAPSE_SMA_KEY, DEFAULT_COLLAPSE_SMA),
        help=f"When enabled, model aggregations with more than {SMA_COLLAPSE_THRESHOLD} products will show only the summary row",
        key=ALLOCATION_COLLAPSE_SMA_KEY
    )
    