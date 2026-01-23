from typing import Any, Optional
from enum import Enum
from dataclasses import dataclass

import polars as pl
import streamlit as st
from great_tables import GT, loc, style

from utils.styles.branding import (
    PRIMARY,
    hex_to_rgba,
    get_allocation_table_main_css,
    format_currency_compact,
    get_subtype_color,
)
from utils.core.session_state import get_or_init
import hashlib

from components.filters import TYPE_TO_SUBTYPE
from utils.core.data import get_model_agg_sort_order, get_strategy_by_name, hash_lazyframe
from utils.core.models import StrategyDetail

# Session state keys
ALLOCATION_COLLAPSE_SMA_KEY = "allocation_collapse_sma"

# Allocation tab constants
DEFAULT_COLLAPSE_SMA = True
SMA_COLLAPSE_THRESHOLD = 10


class RowType(str, Enum):
    """Row type identifiers for styling."""
    CATEGORY = "category"
    PRODUCT = "product"
    SPACER = "spacer"
    SUMMARY = "summary"


@dataclass
class TableStyleConfig:
    """Configuration for table styling."""
    header_font: str = "Merriweather"
    body_font: str = "IBM Plex Sans"
    header_font_size: str = "1.1rem"
    body_font_size: str = "0.875rem"
    header_padding: str = "12px"
    product_indent: str = "20px"
    spacer_height: str = "4px"
    highlight_color: str = "#fff3cd"


@dataclass(frozen=True, slots=True)
class RowMetadata:
    """Metadata for allocation table rows."""

    row_type: RowType
    is_category: bool
    name: str
    color: str
    ticker: str | None = None
    is_spacer: bool = False
    is_summary: bool = False


def _group_rows_by_type(metadata: list[RowMetadata]) -> dict[RowType, list[int]]:
    """Group row indices by their type for batch styling.
    
    Args:
        metadata: List of row metadata dictionaries
        
    Returns:
        Dictionary mapping RowType to list of row indices
    """
    groups: dict[RowType, list[int]] = {
        RowType.CATEGORY: [],
        RowType.PRODUCT: [],
        RowType.SPACER: [],
        RowType.SUMMARY: [],
    }
    
    for idx, meta in enumerate(metadata):
        if meta.row_type:
            groups[meta.row_type].append(idx)
            continue

        if meta.is_summary:
            groups[RowType.SUMMARY].append(idx)
        elif meta.is_category:
            groups[RowType.CATEGORY].append(idx)
        elif meta.is_spacer:
            groups[RowType.SPACER].append(idx)
        else:
            groups[RowType.PRODUCT].append(idx)
    
    return groups


def _apply_row_styling(
    table: GT,
    row_indices: list[int],
    row_type: RowType,
    config: TableStyleConfig,
    row_colors: dict[int, str] | None = None,
    strategy_color: str | None = None,
    equity_cols: list[str] | None = None,
) -> GT:
    """Apply styling to rows based on their type.
    
    Args:
        table: Great Tables GT object
        row_indices: List of row indices to style
        row_type: Type of rows to style
        config: Styling configuration
        row_colors: Optional dict mapping row index to color
        strategy_color: Optional strategy color for summary rows
        equity_cols: Optional list of equity column names
        
    Returns:
        Styled GT table object
    """
    if not row_indices:
        return table
    
    if row_type == RowType.CATEGORY:
        # Category rows: pastel background, bold text
        for idx in row_indices:
            row_color = row_colors.get(idx) if row_colors else None
            rgba_color = hex_to_rgba(row_color, alpha=0.15) if row_color else None
            style_list = [
                style.text(color="black", weight="bold"),
                style.css(rule=f"font-family: '{config.body_font}', sans-serif !important;"),
            ]
            if rgba_color:
                style_list.insert(0, style.fill(color=rgba_color))
            
            table = table.tab_style(
                style=style_list,
                locations=loc.body(columns=pl.all(), rows=[idx]),
            )
    
    elif row_type == RowType.PRODUCT:
        # Product rows: indentation on asset column, font on all columns
        table = table.tab_style(
            style=[
                style.css(rule=f"padding-left: {config.product_indent}; font-family: '{config.body_font}', sans-serif !important;"),
            ],
            locations=loc.body(columns=["asset_formatted"], rows=row_indices),
        )
        # Apply font to equity columns
        if equity_cols:
            table = table.tab_style(
                style=[
                    style.css(rule=f"font-family: '{config.body_font}', sans-serif !important;"),
                ],
                locations=loc.body(columns=equity_cols, rows=row_indices),
            )
    
    elif row_type == RowType.SPACER:
        # Spacer rows: minimal height
        table = table.tab_style(
            style=[
                style.css(rule=f"height: {config.spacer_height}; line-height: {config.spacer_height};"),
            ],
            locations=loc.body(columns=["asset_formatted"], rows=row_indices),
        )
    
    elif row_type == RowType.SUMMARY:
        # Summary rows: pastel background
        rgba_color = hex_to_rgba(strategy_color, alpha=0.15) if strategy_color else None
        style_list = [
            style.css(rule=f"font-family: '{config.body_font}', sans-serif !important;"),
        ]
        if rgba_color:
            style_list.insert(0, style.fill(color=rgba_color))
        
        table = table.tab_style(
            style=style_list,
            locations=loc.body(columns=pl.all(), rows=row_indices),
        )
    
    return table


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


def _preprocess_product_data(all_model_data: pl.DataFrame) -> pl.DataFrame:
    """Pre-process product data with vectorized operations.
    
    Args:
        all_model_data: Raw model data DataFrame
        
    Returns:
        DataFrame with product_cleaned and weight_float columns
    """
    return all_model_data.with_columns([
        # Vectorized product name cleaning: remove trailing "ETF" (case-insensitive) and whitespace
        pl.col("product")
        .str.strip_chars()
        .str.replace(r"(?i)ETF\s*$", "", literal=False)
        .str.strip_chars()
        .alias("product_cleaned"),
        pl.col("weight").fill_null(0.0).cast(pl.Float64).alias("weight_float")
    ])


def _build_equity_to_strategy_lookup(all_model_data: pl.DataFrame) -> tuple[dict[int, str], list[int]]:
    """Build equity level to strategy name lookup.
    
    Args:
        all_model_data: Model data DataFrame
        
    Returns:
        Tuple of (equity_to_strategy dict, available_equity_levels list)
    """
    all_strategies: pl.DataFrame = (
        all_model_data
        .select(["strategy", "portfolio"])
        .unique()
        .sort("portfolio", descending=True)
    )
    
    equity_to_strategy: dict[int, str] = {
        int(row["portfolio"]): row["strategy"]
        for row in all_strategies.to_dicts()
    }
    
    # Only show columns for equity levels that exist
    available_equity_levels: list[int] = [
        eq for eq in [100, 90, 80, 70, 60, 50, 40, 30, 20, 10] 
        if eq in equity_to_strategy
    ]
    
    return equity_to_strategy, available_equity_levels


def _build_agg_target_lookup(all_model_data: pl.DataFrame) -> dict[tuple[str, str], float]:
    """Build model aggregate target lookup.
    
    Args:
        all_model_data: Model data DataFrame
        
    Returns:
        Dictionary mapping (strategy, model_agg) to target value
    """
    agg_target_lookup: dict[tuple[str, str], float] = {}
    agg_target_data: pl.DataFrame = (
        all_model_data
        .select(["strategy", "model_agg", "agg_target"])
        .unique(subset=["strategy", "model_agg"], keep="first")
    )
    
    for row in agg_target_data.to_dicts():
        strat_name: str = row["strategy"]
        model_agg_name: str = row["model_agg"]
        agg_target: float = row["agg_target"]
        if strat_name and model_agg_name is not None:
            agg_target_lookup[(strat_name, str(model_agg_name))] = float(agg_target) if agg_target is not None else 0.0
    
    return agg_target_lookup


def _build_product_weight_lookup(all_model_data: pl.DataFrame) -> dict[tuple[str, str, str], float]:
    """Build product weight lookup.
    
    Args:
        all_model_data: Model data DataFrame (must have weight_float column)
        
    Returns:
        Dictionary mapping (strategy, model_agg, ticker) to weight value
    """
    product_weight_lookup: dict[tuple[str, str, str], float] = {}
    product_weight_data: pl.DataFrame = (
        all_model_data
        .select(["strategy", "model_agg", "ticker", "weight_float"])
        .unique(subset=["strategy", "model_agg", "ticker"], keep="first")
    )
    
    for row in product_weight_data.to_dicts():
        strat: str = row["strategy"]
        model_agg_val: str = str(row["model_agg"])
        ticker_val: str = str(row["ticker"])
        weight_val: float = row["weight_float"]
        product_weight_lookup[(strat, model_agg_val, ticker_val)] = weight_val
    
    return product_weight_lookup


def _build_model_agg_row(
    model_agg: str | None,
    model_agg_name: str,
    available_equity_levels: list[int],
    equity_to_strategy: dict[int, str],
    agg_target_lookup: dict[tuple[str, str], float],
    strategy_color: str,
) -> tuple[dict[str, Any], RowMetadata]:
    """Build a model aggregate category row.
    
    Args:
        model_agg: Model aggregate name
        model_agg_name: Cleaned model aggregate name
        available_equity_levels: List of available equity percentages
        equity_to_strategy: Equity to strategy mapping
        agg_target_lookup: Aggregate target lookup
        strategy_color: Strategy color for styling
        
    Returns:
        Tuple of (row_data dict, row_metadata dict)
    """
    row_data: dict[str, Any] = {"asset": model_agg_name}
    row_metadata = RowMetadata(
        row_type=RowType.CATEGORY,
        is_category=True,
        name=model_agg_name,
        color=strategy_color,
    )
    
    # Model agg rows use agg_target
    for eq_pct in available_equity_levels:
        strategy_name_at_equity: str = equity_to_strategy[eq_pct]
        strategy_model_agg_key: tuple[str, str] = (strategy_name_at_equity, str(model_agg))
        row_data[str(int(eq_pct))] = agg_target_lookup.get(strategy_model_agg_key, 0.0)
    
    return row_data, row_metadata


def _build_product_rows(
    products: pl.DataFrame,
    model_agg: str | None,
    available_equity_levels: list[int],
    equity_to_strategy: dict[int, str],
    product_weight_lookup: dict[tuple[str, str, str], float],
    strategy_color: str,
) -> tuple[list[dict[str, Any]], list[RowMetadata]]:
    """Build product rows for a model aggregate.
    
    Args:
        products: Products DataFrame for the model aggregate
        model_agg: Model aggregate name
        available_equity_levels: List of available equity percentages
        equity_to_strategy: Equity to strategy mapping
        product_weight_lookup: Product weight lookup
        strategy_color: Strategy color for styling
        
    Returns:
        Tuple of (list of row_data dicts, list of row_metadata dicts)
    """
    product_rows: list[dict[str, Any]] = []
    product_metadata: list[RowMetadata] = []
    
    for product_row in products.to_dicts():
        product_name: str = product_row["product_cleaned"]
        ticker: str = product_row["ticker"]
        
        product_row_data: dict[str, Any] = {"asset": product_name}
        product_metadata.append(
            RowMetadata(
                row_type=RowType.PRODUCT,
                is_category=False,
                name=product_name,
                ticker=ticker,
                color=strategy_color,
            )
        )
        
        # Product allocations shown across all equity levels for comparison
        for eq_pct in available_equity_levels:
            strategy_name_at_equity: str = equity_to_strategy[eq_pct]
            product_weight_key: tuple[str, str, str] = (
                strategy_name_at_equity,
                str(model_agg),
                ticker
            )
            product_row_data[str(int(eq_pct))] = product_weight_lookup.get(product_weight_key, 0.0)
        
        product_rows.append(product_row_data)
    
    return product_rows, product_metadata


def _build_spacer_row(
    available_equity_levels: list[int],
    strategy_color: str,
) -> tuple[dict[str, Any], RowMetadata]:
    """Build a spacer row.
    
    Args:
        available_equity_levels: List of available equity percentages
        strategy_color: Strategy color for styling
        
    Returns:
        Tuple of (row_data dict, row_metadata dict)
    """
    spacer_row: dict[str, Any] = {"asset": ""}
    for eq_pct in available_equity_levels:
        spacer_row[str(int(eq_pct))] = None
    
    spacer_metadata = RowMetadata(
        row_type=RowType.SPACER,
        is_category=False,
        name="",
        color=strategy_color,
        is_spacer=True,
    )
    
    return spacer_row, spacer_metadata


def _calculate_highlighted_column(
    strategy_equity_pct: int | None,
    available_equity_levels: list[int],
) -> int:
    """Calculate highlighted column index.
    
    Args:
        strategy_equity_pct: Strategy equity percentage
        available_equity_levels: List of available equity percentages
        
    Returns:
        Column index (0-based, +1 for asset_formatted column)
    """
    if strategy_equity_pct is not None and strategy_equity_pct in available_equity_levels:
        return available_equity_levels.index(strategy_equity_pct) + 1
    return 0


def _has_collapsible_smas(all_model_data: pl.DataFrame, strategy_name: str) -> bool:
    """Check if there are any model aggregates with products exceeding the collapse threshold."""
    if all_model_data.height == 0:
        return False
    
    normalized_strategy = strategy_name.strip().lower()
    selected_strategy_data = all_model_data.filter(
        pl.col("strategy").str.strip_chars().str.to_lowercase() == normalized_strategy
    )
    if selected_strategy_data.height == 0:
        return False
    
    # Count products per model_agg
    product_counts = (
        selected_strategy_data
        .group_by("model_agg")
        .agg(pl.count("product").alias("product_count"))
    )
    
    # Check if any model_agg has more products than the threshold
    return product_counts.filter(pl.col("product_count") > SMA_COLLAPSE_THRESHOLD).height > 0


@st.cache_data
def _generate_allocation_table_html_cached(
    table_html: str,
    table_data_hash: str
) -> str:
    """Generate cached allocation table HTML.
    
    Args:
        table_html: The HTML string from Great Tables (already generated)
        table_data_hash: Hash of the table data for cache key
        
    Returns:
        Complete HTML string for the table
    """
    css: str = get_allocation_table_main_css()
    return f"""
    <div style="width: 100%; margin: 0 !important; padding: 0 !important;">
        <style>
            {css}
        </style>
        <div id="allocation-table-main">
            {table_html}
        </div>
    </div>
    """


@st.cache_data(hash_funcs={pl.LazyFrame: hash_lazyframe})
def _get_equity_matrix_data(
    cleaned_data: pl.LazyFrame,
    strategy_name: str,
    strategy_equity_pct: int | None,
    collapse_sma: bool = DEFAULT_COLLAPSE_SMA,
) -> tuple[pl.DataFrame, int, list[RowMetadata], dict[int, str]]:
    """Get allocation data in matrix format with equity % columns.
    
    Steps:
    1. Load strategy data and get model information
    2. Pre-process data with vectorized operations
    3. Build lookup dictionaries for efficient data access
    4. Iterate over model aggregates to build matrix rows
    5. Add product rows and spacer rows as needed
    6. Calculate highlighted column index
    """
    # ============================================================================
    # STEP 1: Load strategy data and get model information
    # ============================================================================
    strategy_data: StrategyDetail | None = get_strategy_by_name(cleaned_data, strategy_name, cache_version=3)
    strategy_model: str = strategy_data.model
    type_val: str = strategy_data.type
    strategy_color: str = get_subtype_color(type_val)
    
    all_model_data: pl.DataFrame = _get_model_data(cleaned_data, strategy_model)
    
    # ============================================================================
    # STEP 2: Pre-process data with vectorized operations
    # ============================================================================
    all_model_data = _preprocess_product_data(all_model_data)
    
    # ============================================================================
    # STEP 3: Build lookup dictionaries for efficient data access
    # ============================================================================
    equity_to_strategy, available_equity_levels = _build_equity_to_strategy_lookup(all_model_data)
    agg_target_lookup = _build_agg_target_lookup(all_model_data)
    product_weight_lookup = _build_product_weight_lookup(all_model_data)
    
    model_aggs: list[str | None] = sorted(
        [ma for ma in all_model_data["model_agg"].unique().to_list() if ma is not None],
        key=get_model_agg_sort_order
    )
    
    # Pre-process model agg names: remove "Portfolio" suffix
    model_agg_names: dict[str | None, str] = {
        ma: str(ma).replace(" Portfolio", "").replace("Portfolio", "")
        for ma in model_aggs
    }
    
    # Track which model_agg is the last one for the spacer row
    last_model_agg: str | None = model_aggs[-1] if model_aggs else None
    
    # ============================================================================
    # STEP 4: Iterate over model aggregates to build matrix rows
    # ============================================================================
    data: list[dict[str, Any]] = []
    row_metadata: list[RowMetadata] = []
    
    for model_agg in model_aggs:
        model_agg_name: str = model_agg_names[model_agg]
        
        # Build model aggregate category row
        row_data, meta = _build_model_agg_row(
            model_agg, model_agg_name, available_equity_levels,
            equity_to_strategy, agg_target_lookup, strategy_color
        )
        data.append(row_data)
        row_metadata.append(meta)
        
        # Get products for this model aggregate across the full model
        # (ensures product rows appear even if the selected strategy has 0% allocation)
        products: pl.DataFrame = (
            all_model_data
            .filter(pl.col("model_agg") == model_agg)
            .select(["product_cleaned", "ticker", "weight_float"])
            .group_by(["product_cleaned", "ticker"])
            .agg(pl.col("weight_float").max().alias("weight_float"))
            .sort("weight_float", descending=True)
        )
        
        # Collapse SMAs with many holdings to reduce visual clutter
        num_products: int = products.height
        should_collapse: bool = collapse_sma and num_products > SMA_COLLAPSE_THRESHOLD
        
        if not should_collapse:
            product_rows, product_meta = _build_product_rows(
                products, model_agg, available_equity_levels,
                equity_to_strategy, product_weight_lookup, strategy_color
            )
            data.extend(product_rows)
            row_metadata.extend(product_meta)
        
        # Spacer row between model aggs
        if products.height > 0 and model_agg != last_model_agg:
            spacer_row, spacer_meta = _build_spacer_row(available_equity_levels, strategy_color)
            data.append(spacer_row)
            row_metadata.append(spacer_meta)
    
    # ============================================================================
    # STEP 5: Calculate highlighted column index
    # ============================================================================
    highlighted_col_idx = _calculate_highlighted_column(strategy_equity_pct, available_equity_levels)
    
    return pl.DataFrame(data), highlighted_col_idx, row_metadata, equity_to_strategy


def _format_asset_names(row_metadata: list[RowMetadata]) -> list[str]:
    """Format asset names by combining with tickers.
    
    Args:
        row_metadata: List of row metadata dictionaries
        
    Returns:
        List of formatted asset names
    """
    asset_names_combined: list[str] = []
    for row in row_metadata:
        name: str = row.name
        ticker: str = row.ticker or ""
        if row.is_spacer:
            combined_name = ""
        elif not row.is_category:
            # Product rows: include ticker if available
            combined_name = f"{name} ({ticker})" if ticker else name
        else:
            # Category rows: plain name
            combined_name = name
        asset_names_combined.append(combined_name)
    
    return asset_names_combined


def _prepare_matrix_dataframe(
    matrix_df: pl.DataFrame,
    row_metadata: list[RowMetadata],
    equity_cols: list[str],
) -> pl.DataFrame:
    """Prepare matrix DataFrame with formatted columns.
    
    Args:
        matrix_df: Raw matrix DataFrame
        row_metadata: Row metadata list
        equity_cols: List of equity column names
        
    Returns:
        Formatted DataFrame with asset_formatted, is_category, row_color columns
    """
    asset_names_combined = _format_asset_names(row_metadata)
    is_category_list: list[bool] = [meta.is_category for meta in row_metadata]
    row_colors: list[str] = [meta.color for meta in row_metadata]
    
    formatted_matrix_df: pl.DataFrame = matrix_df.with_columns([
        pl.Series("is_category", is_category_list),
        pl.Series("asset_formatted", asset_names_combined),
        pl.Series("row_color", row_colors),
    ])
    
    column_order: list[str] = ["asset_formatted"] + equity_cols + ["is_category", "asset", "row_color"]
    return formatted_matrix_df.select(column_order)


def _build_summary_metrics_lookup(
    all_model_data: pl.DataFrame,
    equity_to_strategy: dict[int, str],
) -> dict[str, dict[str, float]]:
    """Build summary metrics lookup for all strategies.
    
    Args:
        all_model_data: Model data DataFrame
        equity_to_strategy: Equity to strategy mapping
        
    Returns:
        Dictionary mapping strategy name to metrics dict
    """
    summary_strategies_data: pl.DataFrame = (
        all_model_data
        .filter(pl.col("strategy").is_in(list(equity_to_strategy.values())))
        .select(["strategy", "target", "fee", "yield", "minimum"])
        .group_by("strategy")
        .agg([
            pl.col("target").sum().alias("total_target"),
            (pl.col("target") * pl.col("fee")).sum().alias("weighted_fee_sum"),
            (pl.col("target") * pl.col("yield")).sum().alias("weighted_yield_sum"),
            pl.col("minimum").first().alias("account_min")
        ])
    )
    
    summary_metrics_lookup: dict[str, dict[str, float]] = {}
    for row in summary_strategies_data.to_dicts():
        strategy_name_for_lookup: str = row["strategy"]
        total_target: float = row["total_target"]
        weighted_fee_sum: float = row["weighted_fee_sum"]
        weighted_yield_sum: float = row["weighted_yield_sum"]
        account_min: float = row["account_min"]
        
        if total_target > 0:
            weighted_expense: float = weighted_fee_sum / total_target
            weighted_yield: float = weighted_yield_sum / total_target
        else:
            weighted_expense = 0.0
            weighted_yield = 0.0
        
        summary_metrics_lookup[strategy_name_for_lookup] = {
            "weighted_expense": weighted_expense,
            "weighted_yield": weighted_yield,
            "account_min": account_min
        }
    
    return summary_metrics_lookup


def _build_summary_rows(
    equity_cols: list[str],
    equity_to_strategy: dict[int, str],
    summary_metrics_lookup: dict[str, dict[str, float]],
    strategy_color: str,
) -> tuple[list[dict[str, Any]], list[RowMetadata]]:
    """Build summary metric rows.
    
    Args:
        equity_cols: List of equity column names
        equity_to_strategy: Equity to strategy mapping
        summary_metrics_lookup: Summary metrics lookup
        strategy_color: Strategy color for styling
        
    Returns:
        Tuple of (list of summary row dicts, list of summary metadata dicts)
    """
    summary_metrics_raw: dict[str, dict[str, float]] = {
        "Weighted Expense Ratio": {},
        "Weighted Indicated Yield": {},
        "Account Minimum": {}
    }
    
    for equity_col_name in equity_cols:
        try:
            equity_pct: int = int(equity_col_name)
        except ValueError:
            continue
        
        if equity_pct not in equity_to_strategy:
            continue
        
        strategy_name_at_equity: str = equity_to_strategy[equity_pct]
        if strategy_name_at_equity not in summary_metrics_lookup:
            continue
        
        metrics = summary_metrics_lookup[strategy_name_at_equity]
        summary_metrics_raw["Weighted Expense Ratio"][equity_col_name] = metrics["weighted_expense"] if metrics["weighted_expense"] else 0.0
        summary_metrics_raw["Weighted Indicated Yield"][equity_col_name] = metrics["weighted_yield"] if metrics["weighted_yield"] else 0.0
        summary_metrics_raw["Account Minimum"][equity_col_name] = float(metrics["account_min"]) if metrics["account_min"] else 0.0
    
    summary_rows: list[dict[str, Any]] = []
    summary_row_names: list[str] = ["Weighted Expense Ratio", "Weighted Indicated Yield", "Account Minimum"]
    
    for summary_name in summary_row_names:
        summary_row: dict[str, Any] = {"asset_formatted": summary_name}
        for col in equity_cols:
            summary_row[col] = summary_metrics_raw[summary_name].get(col, 0.0)
        summary_row["is_category"] = False
        summary_row["asset"] = summary_name
        summary_row["row_color"] = strategy_color
        summary_rows.append(summary_row)
    
    summary_metadata: list[RowMetadata] = [
        RowMetadata(
            row_type=RowType.SUMMARY,
            is_category=False,
            name=name,
            color=strategy_color,
            is_summary=True,
        )
        for name in summary_row_names
    ]
    
    return summary_rows, summary_metadata


def _combine_allocation_and_summary(
    formatted_matrix_df: pl.DataFrame,
    equity_cols: list[str],
    summary_rows: list[dict[str, Any]],
    strategy_color: str,
) -> tuple[pl.DataFrame, int, list[RowMetadata]]:
    """Combine allocation and summary DataFrames.
    
    Args:
        formatted_matrix_df: Formatted allocation matrix DataFrame
        equity_cols: List of equity column names
        summary_rows: List of summary row dicts
        strategy_color: Strategy color for styling
        
    Returns:
        Tuple of (combined DataFrame, number of allocation rows, combined metadata)
    """
    num_allocation_rows: int = formatted_matrix_df.height
    
    # Get the exact column order from formatted_matrix_df
    expected_columns: list[str] = formatted_matrix_df.columns
    
    # Create spacer rows with all required columns in correct order
    spacer_row: dict[str, Any] = {}
    spacer_row_2: dict[str, Any] = {}
    
    for col in expected_columns:
        if col == "asset_formatted":
            spacer_row[col] = ""
            spacer_row_2[col] = ""
        elif col == "is_category":
            spacer_row[col] = False
            spacer_row_2[col] = False
        elif col == "asset":
            spacer_row[col] = ""
            spacer_row_2[col] = ""
        elif col == "row_color":
            spacer_row[col] = strategy_color
            spacer_row_2[col] = strategy_color
        else:
            # Equity columns
            spacer_row[col] = None
            spacer_row_2[col] = None
    
    # Create DataFrames ensuring column order matches
    spacer_df: pl.DataFrame = pl.DataFrame([spacer_row], schema=formatted_matrix_df.schema)
    spacer_df_2: pl.DataFrame = pl.DataFrame([spacer_row_2], schema=formatted_matrix_df.schema)
    
    # Ensure summary rows have all columns in correct order
    summary_rows_with_all_cols: list[dict[str, Any]] = []
    for summary_row in summary_rows:
        complete_row: dict[str, Any] = {}
        for col in expected_columns:
            if col in summary_row:
                complete_row[col] = summary_row[col]
            elif col == "is_category":
                complete_row[col] = False
            elif col == "asset":
                complete_row[col] = summary_row.get("asset_formatted", "")
            elif col == "row_color":
                complete_row[col] = strategy_color
            else:
                # Equity columns - should already be in summary_row
                complete_row[col] = summary_row.get(col, 0.0)
        summary_rows_with_all_cols.append(complete_row)
    
    summary_df_data: pl.DataFrame = pl.DataFrame(summary_rows_with_all_cols, schema=formatted_matrix_df.schema)
    
    combined_df: pl.DataFrame = pl.concat([
        formatted_matrix_df,
        spacer_df,
        spacer_df_2,
        summary_df_data
    ])
    
    # Build combined metadata
    spacer_metadata = RowMetadata(
        row_type=RowType.SPACER,
        is_category=False,
        name="",
        color=strategy_color,
        is_spacer=True,
    )
    
    return combined_df, num_allocation_rows, [spacer_metadata, spacer_metadata]


def _build_base_table(
    combined_df: pl.DataFrame,
    header_name: str,
    equity_cols: list[str],
) -> GT:
    """Build base GT table with basic formatting.
    
    Args:
        combined_df: Combined DataFrame
        header_name: Header name for asset column
        equity_cols: List of equity column names
        
    Returns:
        Base GT table
    """
    return (
        GT(combined_df)
        .cols_hide(["is_category", "asset", "row_color"])
        .cols_label(asset_formatted=header_name)
        .sub_missing(columns=equity_cols, missing_text="")
        .cols_align(columns=equity_cols, align="center")
        .cols_align(columns=["asset_formatted"], align="left")
    )


def _apply_allocation_formatting(
    table: GT,
    equity_cols: list[str],
    num_allocation_rows: int,
) -> GT:
    """Apply percent formatting to allocation rows.
    
    Args:
        table: GT table
        equity_cols: List of equity column names
        num_allocation_rows: Number of allocation rows
        
    Returns:
        GT table with allocation formatting
    """
    if num_allocation_rows > 0:
        return table.fmt_percent(
            columns=equity_cols,
            decimals=2,
            rows=list(range(num_allocation_rows))
        )
    return table


def _apply_summary_formatting(
    table: GT,
    equity_cols: list[str],
    num_allocation_rows: int,
) -> GT:
    """Apply formatting to summary rows (percent for expense/yield, currency for min).
    
    Args:
        table: GT table
        equity_cols: List of equity column names
        num_allocation_rows: Number of allocation rows
        
    Returns:
        GT table with summary formatting
    """
    num_spacer_rows: int = 2
    summary_start_idx: int = num_allocation_rows + num_spacer_rows
    
    expense_ratio_idx: int = summary_start_idx
    indicated_yield_idx: int = summary_start_idx + 1
    account_min_idx: int = summary_start_idx + 2
    
    # Format expense ratio and yield as percentages
    table = table.fmt_percent(
        columns=equity_cols,
        decimals=2,
        rows=[expense_ratio_idx, indicated_yield_idx]
    )
    
    # Format account minimum as compact currency
    def format_account_min(x: Any) -> str:
        """Format Account Minimum value as compact currency."""
        if x is None:
            raise ValueError("Account minimum value is None. ETL pipeline must ensure all account minimum values are non-null.")
        if x == "":
            raise ValueError("Account minimum value is empty string. ETL pipeline must ensure all account minimum values are numeric.")
        return format_currency_compact(float(x))
    
    for col in equity_cols:
        table = table.fmt(
            columns=[col],
            rows=[account_min_idx],
            fns=format_account_min
        )
    
    return table


def _apply_table_styling(
    table: GT,
    combined_row_metadata: list[RowMetadata],
    strategy_color: str,
    equity_cols: list[str],
    highlighted_col_idx: int,
) -> GT:
    """Apply all styling to the table.
    
    Args:
        table: GT table
        combined_row_metadata: Combined row metadata
        strategy_color: Strategy color
        equity_cols: List of equity column names
        highlighted_col_idx: Index of highlighted column
        
    Returns:
        Fully styled GT table
    """
    style_config = TableStyleConfig()
    
    # Header styling
    table = table.tab_style(
        style=[
            style.fill(color=strategy_color),
            style.text(color="white", weight="bold", size=style_config.header_font_size),
            style.css(rule=f"font-family: '{style_config.header_font}', serif !important; padding: {style_config.header_padding} !important;"),
        ],
        locations=loc.column_labels(),
    )
    
    # Group rows by type for batch styling
    row_groups = _group_rows_by_type(combined_row_metadata)
    
    # Build row colors dict for category rows
    row_colors: dict[int, str] = {
        idx: combined_row_metadata[idx].color
        for idx in row_groups[RowType.CATEGORY]
        if idx < len(combined_row_metadata)
    }
    
    # Apply styling by row type
    table = _apply_row_styling(
        table, row_groups[RowType.CATEGORY], RowType.CATEGORY,
        style_config, row_colors=row_colors, equity_cols=equity_cols,
    )
    table = _apply_row_styling(
        table, row_groups[RowType.PRODUCT], RowType.PRODUCT,
        style_config, equity_cols=equity_cols,
    )
    table = _apply_row_styling(
        table, row_groups[RowType.SPACER], RowType.SPACER,
        style_config,
    )
    table = _apply_row_styling(
        table, row_groups[RowType.SUMMARY], RowType.SUMMARY,
        style_config, strategy_color=strategy_color, equity_cols=equity_cols,
    )
    
    # Table-wide options
    table = table.tab_options(
        table_font_size=style_config.body_font_size,
        table_font_names=[
            style_config.body_font,
            "-apple-system",
            "BlinkMacSystemFont",
            "Segoe UI",
            "sans-serif",
        ]
    )
    
    # Ensure all body cells use IBM Plex Sans
    table = table.tab_style(
        style=[
            style.css(rule=f"font-family: '{style_config.body_font}', sans-serif !important;"),
        ],
        locations=loc.body(),
    )
    
    # Highlight selected strategy's equity column
    if highlighted_col_idx >= 1 and highlighted_col_idx - 1 < len(equity_cols):
        highlighted_col: str = equity_cols[highlighted_col_idx - 1]
        table = table.tab_style(
            style=[style.fill(color=style_config.highlight_color)],
            locations=loc.body(columns=[highlighted_col]),
        )
    
    return table


def _build_allocation_tables(
    matrix_df: pl.DataFrame,
    equity_cols: list[str],
    row_metadata: list[RowMetadata],
    header_name: str,
    highlighted_col_idx: int,
    all_model_data: pl.DataFrame,
    equity_to_strategy: dict[int, str],
    strategy_color: str,
) -> GT:
    """Build combined allocation table with summary metrics included.
    
    Steps:
    1. Format asset names (combine with tickers)
    2. Prepare matrix data with formatted columns
    3. Pre-compute summary metrics lookup
    4. Add spacer row and summary metric rows to DataFrame
    5. Build and style combined table
    
    Returns:
        Single GT table object containing both allocation and summary rows
    """
    strategy_color: str = row_metadata[0].color if row_metadata else PRIMARY["raspberry"]
    
    # ============================================================================
    # STEP 1: Format asset names and prepare matrix DataFrame
    # ============================================================================
    formatted_matrix_df = _prepare_matrix_dataframe(matrix_df, row_metadata, equity_cols)
    
    # ============================================================================
    # STEP 2: Build summary metrics lookup
    # ============================================================================
    summary_metrics_lookup = _build_summary_metrics_lookup(all_model_data, equity_to_strategy)
    
    # ============================================================================
    # STEP 3: Build summary rows
    # ============================================================================
    summary_rows, summary_metadata = _build_summary_rows(
        equity_cols, equity_to_strategy, summary_metrics_lookup, strategy_color
    )
    
    # ============================================================================
    # STEP 4: Combine allocation and summary DataFrames
    # ============================================================================
    combined_df, num_allocation_rows, spacer_metadata = _combine_allocation_and_summary(
        formatted_matrix_df, equity_cols, summary_rows, strategy_color
    )
    
    # Build combined metadata
    combined_row_metadata: list[RowMetadata] = row_metadata.copy()
    combined_row_metadata.extend(spacer_metadata)
    combined_row_metadata.extend(summary_metadata)
    
    # ============================================================================
    # STEP 5: Build and style combined table
    # ============================================================================
    combined_table = _build_base_table(combined_df, header_name, equity_cols)
    combined_table = _apply_allocation_formatting(combined_table, equity_cols, num_allocation_rows)
    combined_table = _apply_summary_formatting(combined_table, equity_cols, num_allocation_rows)
    combined_table = _apply_table_styling(
        combined_table, combined_row_metadata, strategy_color, equity_cols, highlighted_col_idx
    )
    
    return combined_table


def _load_strategy_allocation_data(
    cleaned_data: pl.LazyFrame,
    strategy_name: str,
) -> tuple[StrategyDetail | None, int | None, str | None, pl.DataFrame]:
    """Load strategy data and prepare model data.
    
    Args:
        cleaned_data: Full cleaned data LazyFrame
        strategy_name: Name of the strategy
        
    Returns:
        Tuple of (strategy_data, strategy_equity_pct, model_name, all_model_data)
    """
    strategy_data: StrategyDetail | None = get_strategy_by_name(cleaned_data, strategy_name, cache_version=3)
    strategy_equity_pct: int | None = None
    model_name: str | None = None
    
    if strategy_data:
        strategy_equity_pct = int(strategy_data.portfolio) if strategy_data.portfolio is not None else None
        model_name = strategy_data.model
    
    # Get model data for summary table (cached)
    if strategy_data and strategy_data.model:
        all_model_data: pl.DataFrame = _get_model_data(cleaned_data, strategy_data.model)
    else:
        all_model_data = pl.DataFrame()
    
    return strategy_data, strategy_equity_pct, model_name, all_model_data


def _prepare_allocation_matrix(
    cleaned_data: pl.LazyFrame,
    strategy_name: str,
    strategy_equity_pct: int | None,
    collapse_sma: bool,
) -> tuple[pl.DataFrame, int, list[RowMetadata], dict[int, str], list[str]]:
    """Prepare allocation matrix data.
    
    Args:
        cleaned_data: Full cleaned data LazyFrame
        strategy_name: Name of the strategy
        strategy_equity_pct: Strategy equity percentage
        collapse_sma: Whether to collapse SMAs
        
    Returns:
        Tuple of (matrix_df, highlighted_col_idx, row_metadata, equity_to_strategy, equity_cols)
    """
    matrix_df, highlighted_col_idx, row_metadata, equity_to_strategy = _get_equity_matrix_data(
        cleaned_data, strategy_name, strategy_equity_pct, collapse_sma=collapse_sma
    )
    
    if matrix_df.height == 0:
        return matrix_df, highlighted_col_idx, row_metadata, equity_to_strategy, []
    
    equity_cols: list[str] = [col for col in matrix_df.columns if col != "asset"]
    
    # Prepare metadata for styling
    is_category_list: list[bool] = [meta.is_category for meta in row_metadata]
    row_colors: list[str] = [meta.color for meta in row_metadata]
    
    # Add formatted columns to matrix_df
    matrix_df = matrix_df.with_columns([
        pl.Series("is_category", is_category_list),
        pl.Series("row_color", row_colors),
    ])
    
    return matrix_df, highlighted_col_idx, row_metadata, equity_to_strategy, equity_cols


def _render_allocation_table(
    matrix_df: pl.DataFrame,
    equity_cols: list[str],
    row_metadata: list[RowMetadata],
    header_name: str,
    highlighted_col_idx: int,
    all_model_data: pl.DataFrame,
    equity_to_strategy: dict[int, str],
    strategy_color: str,
) -> None:
    """Render the allocation table.
    
    Args:
        matrix_df: Matrix DataFrame
        equity_cols: List of equity column names
        row_metadata: Row metadata list
        header_name: Header name for asset column
        highlighted_col_idx: Index of highlighted column
        all_model_data: Model data DataFrame
        equity_to_strategy: Equity to strategy mapping
        strategy_color: Strategy color
    """
    # Build combined table
    combined_table = _build_allocation_tables(
        matrix_df=matrix_df,
        equity_cols=equity_cols,
        row_metadata=row_metadata,
        header_name=header_name,
        highlighted_col_idx=highlighted_col_idx,
        all_model_data=all_model_data,
        equity_to_strategy=equity_to_strategy,
        strategy_color=strategy_color,
    )
    
    # Calculate column widths for consistent layout
    num_equity_cols: int = len(equity_cols)
    asset_col_width: str = "40%"
    equity_col_width: str = f"{(60 / num_equity_cols):.2f}%" if num_equity_cols > 0 else "0%"
    
    # Set column widths
    width_cases: dict[str, str] = {"asset_formatted": asset_col_width}
    width_cases.update({col: equity_col_width for col in equity_cols})
    combined_table = combined_table.cols_width(cases=width_cases)
    
    # Generate table HTML
    table_html: str = combined_table.as_raw_html(inline_css=True)
    
    # Generate hash for caching
    table_data_hash: str = hashlib.md5(
        (
            str(matrix_df.write_json()) + 
            str(equity_cols) +
            str(header_name) +
            asset_col_width + 
            equity_col_width +
            str(strategy_color)
        ).encode()
    ).hexdigest()
    
    # Generate complete HTML (cached)
    complete_html: str = _generate_allocation_table_html_cached(table_html, table_data_hash)
    
    # Render table
    st.html(complete_html)


def _render_asset_class_table(
    strategy_name: str,
    all_model_data: pl.DataFrame,
    strategy_color: str,
    expense_ratio: float,
    yield_pct: float | None,
    minimum: float,
) -> None:
    """Render a simplified allocation table for Asset-Class strategies."""
    if all_model_data.height == 0:
        st.info("No allocation data available for this strategy.")
        return
    
    # Filter to the selected strategy only (case/whitespace tolerant)
    normalized_strategy = strategy_name.strip().lower()
    strategy_products = all_model_data.filter(
        pl.col("strategy").str.strip_chars().str.to_lowercase() == normalized_strategy
    )
    if strategy_products.height == 0:
        st.info("No allocation data available for this strategy.")
        return
    
    data_rows: list[dict[str, Any]] = []
    row_metadata: list[RowMetadata] = []
    
    # Asset-Class strategies are expected to have a single model agg,
    # so just render the strategy's own products without grouping.
    for product_row in strategy_products.select(
        ["product_cleaned", "ticker", "weight_float"]
    ).sort("weight_float", descending=True).to_dicts():
        product_name = product_row["product_cleaned"]
        ticker = product_row["ticker"]
        weight_val = product_row["weight_float"]
        
        data_rows.append({"asset": product_name, "weight": weight_val})
        row_metadata.append(
            RowMetadata(
                row_type=RowType.PRODUCT,
                is_category=False,
                name=product_name,
                ticker=ticker,
                color=strategy_color,
            )
        )
    
    asset_names_combined = _format_asset_names(row_metadata)
    is_category_list: list[bool] = [meta.is_category for meta in row_metadata]
    row_colors: list[str] = [meta.color for meta in row_metadata]
    
    base_df = pl.DataFrame(data_rows).with_columns([
        pl.Series("asset_formatted", asset_names_combined),
        pl.Series("is_category", is_category_list),
        pl.Series("row_color", row_colors),
    ])
    base_df = base_df.select(["asset_formatted", "weight", "is_category", "asset", "row_color"])
    
    # Build summary rows
    summary_rows = [
        {
            "asset_formatted": "Weighted Expense Ratio",
            "weight": expense_ratio,
            "is_category": False,
            "asset": "Weighted Expense Ratio",
            "row_color": strategy_color,
        },
        {
            "asset_formatted": "Weighted Indicated Yield",
            "weight": yield_pct if yield_pct is not None else 0.0,
            "is_category": False,
            "asset": "Weighted Indicated Yield",
            "row_color": strategy_color,
        },
        {
            "asset_formatted": "Account Minimum",
            "weight": float(minimum),
            "is_category": False,
            "asset": "Account Minimum",
            "row_color": strategy_color,
        },
    ]
    summary_metadata: list[RowMetadata] = [
        RowMetadata(
            row_type=RowType.SUMMARY,
            is_category=False,
            name=row["asset_formatted"],
            color=strategy_color,
            is_summary=True,
        )
        for row in summary_rows
    ]
    
    # Spacer rows
    spacer_row = {
        "asset_formatted": "",
        "weight": None,
        "is_category": False,
        "asset": "",
        "row_color": strategy_color,
    }
    spacer_df = pl.DataFrame([spacer_row, spacer_row], schema=base_df.schema)
    summary_df = pl.DataFrame(summary_rows, schema=base_df.schema)
    
    combined_df = pl.concat([base_df, spacer_df, summary_df])
    combined_metadata = row_metadata + [
        RowMetadata(
            row_type=RowType.SPACER,
            is_category=False,
            name="",
            color=strategy_color,
            is_spacer=True,
        ),
        RowMetadata(
            row_type=RowType.SPACER,
            is_category=False,
            name="",
            color=strategy_color,
            is_spacer=True,
        ),
    ] + summary_metadata
    
    equity_cols = ["weight"]
    combined_table = _build_base_table(combined_df, strategy_name, equity_cols)
    combined_table = combined_table.cols_label(weight="Weight")
    combined_table = _apply_allocation_formatting(combined_table, equity_cols, base_df.height)
    combined_table = _apply_summary_formatting(combined_table, equity_cols, base_df.height)
    combined_table = _apply_table_styling(
        combined_table, combined_metadata, strategy_color, equity_cols, highlighted_col_idx=0
    )
    
    # Set column widths (single weight column)
    combined_table = combined_table.cols_width(cases={"asset_formatted": "80%", "weight": "20%"})
    
    table_html: str = combined_table.as_raw_html(inline_css=True)
    table_data_hash: str = hashlib.md5(
        (
            str(combined_df.write_json()) +
            str(strategy_name) +
            str(strategy_color)
        ).encode()
    ).hexdigest()
    complete_html: str = _generate_allocation_table_html_cached(table_html, table_data_hash)
    st.html(complete_html)


def _render_collapse_toggle(
    all_model_data: pl.DataFrame,
    strategy_name: str,
) -> None:
    """Render collapse SMAs toggle if applicable.
    
    Args:
        all_model_data: Model data DataFrame
        strategy_name: Name of the strategy
    """
    if _has_collapsible_smas(all_model_data, strategy_name):
        st.toggle(
            "Collapse SMAs",
            value=get_or_init(ALLOCATION_COLLAPSE_SMA_KEY, DEFAULT_COLLAPSE_SMA),
            key=ALLOCATION_COLLAPSE_SMA_KEY
        )


def render_allocation_tab(strategy_name: str, cleaned_data: pl.LazyFrame) -> None:
    """Render allocation tab with combined matrix table showing allocations and summary metrics.
    
    Steps:
    1. Load strategy data and prepare model data
    2. Render summary statistics metrics
    3. Build equity matrix data (product allocations across equity levels)
    4. Build and render combined allocation table (includes summary metrics)
    5. Render collapse SMAs checkbox
    """
    # ============================================================================
    # STEP 1: Load strategy data and prepare model data
    # ============================================================================
    strategy_data, strategy_equity_pct, model_name, all_model_data = _load_strategy_allocation_data(
        cleaned_data, strategy_name
    )
    if not strategy_data:
        st.info("No allocation data available for this strategy.")
        return
    
    # ============================================================================
    # STEP 2: Render summary statistics metrics
    # ============================================================================
    st.markdown("#### Summary Statistics")
    
    # Row 1: Expense Ratio, Yield, Minimum
    # Note: cleaned_data uses lowercase column names
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    normalized_strategy = strategy_name.strip().lower()
    with row1_col1:
        # Get expense ratio from strategy data (cleaned_data has lowercase column names)
        expense_ratio = strategy_data.expense_ratio or 0
        # If not found, calculate weighted expense ratio from model data
        if expense_ratio == 0 and all_model_data.height > 0:
            strategy_model_data = all_model_data.filter(
                pl.col("strategy").str.strip_chars().str.to_lowercase() == normalized_strategy
            )
            if strategy_model_data.height > 0:
                total_target = strategy_model_data["target"].sum()
                weighted_fee_sum = (strategy_model_data["target"] * strategy_model_data["fee"]).sum()
                if total_target > 0:
                    expense_ratio = weighted_fee_sum / total_target
        st.metric("WEIGHTED AVG EXP RATIO", f"{expense_ratio * 100:.2f}%")
    with row1_col2:
        # Get yield from strategy data
        y: Optional[float] = strategy_data.yield_val
        # If not found, calculate weighted yield from model data
        if y is None and all_model_data.height > 0:
            strategy_model_data = all_model_data.filter(
                pl.col("strategy").str.strip_chars().str.to_lowercase() == normalized_strategy
            )
            if strategy_model_data.height > 0:
                total_target = strategy_model_data["target"].sum()
                weighted_yield_sum = (strategy_model_data["target"] * strategy_model_data["yield"]).sum()
                if total_target > 0:
                    y = weighted_yield_sum / total_target
        st.metric("12-MONTH YIELD", f"{y * 100:.2f}%" if y else "0.00%")
    with row1_col3:
        # Get minimum from strategy data
        minimum = strategy_data.minimum or 0
        st.metric(
            "ACCOUNT MINIMUM", format_currency_compact(float(minimum)) if minimum else "$0.0"
        )
    
    st.divider()
    
    # If this is an Asset-Class or Special Situation strategy, render a simplified table
    preprocessed_model_data = _preprocess_product_data(all_model_data) if all_model_data.height > 0 else all_model_data
    type_label = None
    if strategy_data:
        type_label = strategy_data.category or strategy_data.type
    normalized_type = str(type_label or "").strip().lower()
    is_asset_class = "asset" in normalized_type and "class" in normalized_type
    is_special_situation = "special" in normalized_type and "situation" in normalized_type
    
    # Fallback: if subtype matches Asset-Class subtype names, treat as Asset-Class
    subtype_label = None
    if strategy_data:
        subtype_label = strategy_data.type
    if not (is_asset_class or is_special_situation) and subtype_label in TYPE_TO_SUBTYPE.get("Asset-Class", []):
        is_asset_class = True
    
    if is_asset_class or is_special_situation:
        st.markdown("#### Asset Allocation")
        strategy_color: str = get_subtype_color(subtype_label) if subtype_label else PRIMARY["raspberry"]
        _render_asset_class_table(
            strategy_name,
            preprocessed_model_data,
            strategy_color,
            expense_ratio,
            y,
            minimum,
        )
        return
    
    collapse_sma: bool = get_or_init(ALLOCATION_COLLAPSE_SMA_KEY, DEFAULT_COLLAPSE_SMA)
    
    # ============================================================================
    # STEP 3: Build equity matrix data
    # ============================================================================
    matrix_df, highlighted_col_idx, row_metadata, equity_to_strategy, equity_cols = _prepare_allocation_matrix(
        cleaned_data, strategy_name, strategy_equity_pct, collapse_sma
    )
    
    if matrix_df.height == 0:
        st.info("No allocation data available for this strategy.")
        return
    
    # Determine header name (model name preferred over strategy name)
    if model_name:
        header_name: str = str(model_name)
    else:
        header_name = strategy_name.replace(" Portfolio", "").replace("Portfolio", "")
    
    strategy_color: str = row_metadata[0].color if row_metadata else PRIMARY["raspberry"]
    
    # ============================================================================
    # STEP 4: Render combined allocation table
    # ============================================================================
    st.markdown("#### Asset Allocation")
    _render_allocation_table(
        matrix_df, equity_cols, row_metadata, header_name,
        highlighted_col_idx, all_model_data, equity_to_strategy, strategy_color
    )
    
    st.divider()
    
    # ============================================================================
    # STEP 5: Render collapse SMAs toggle
    # ============================================================================
    _render_collapse_toggle(all_model_data, strategy_name)
    