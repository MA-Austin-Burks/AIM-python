from typing import Any, Final
from enum import Enum
from dataclasses import dataclass

import polars as pl
import streamlit as st
from great_tables import GT, loc, style

from styles.branding import (
    PRIMARY,
    hex_to_rgba,
)
from utils.core.session_state import get_or_init
from styles import (
    get_allocation_table_main_css,
)
import hashlib

from utils.core.constants import (
    ALLOCATION_COLLAPSE_SMA_KEY,
    DEFAULT_COLLAPSE_SMA,
    SMA_COLLAPSE_THRESHOLD,
)
from utils.core.data import get_model_agg_sort_order, get_strategy_by_name, hash_lazyframe
from utils.core.formatting import format_currency_compact, get_strategy_color


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

def _group_rows_by_type(metadata: list[dict[str, Any]]) -> dict[RowType, list[int]]:
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
        # Check for row_type first (new approach)
        row_type_str = meta.get("row_type")
        if row_type_str:
            try:
                row_type = RowType(row_type_str)
                groups[row_type].append(idx)
                continue
            except ValueError:
                pass
        
        # Fallback to old boolean flags for backward compatibility
        if meta.get("is_summary", False):
            groups[RowType.SUMMARY].append(idx)
        elif meta.get("is_category", False):
            groups[RowType.CATEGORY].append(idx)
        elif meta.get("is_spacer", False):
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


def _has_collapsible_smas(all_model_data: pl.DataFrame, strategy_name: str) -> bool:
    """Check if there are any model aggregates with products exceeding the collapse threshold."""
    if all_model_data.height == 0:
        return False
    
    selected_strategy_data = all_model_data.filter(pl.col("strategy") == strategy_name)
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
) -> tuple[pl.DataFrame, int, list[dict[str, Any]], dict[int, str]]:
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
    # Get the strategy's model to find related strategies
    strategy_data: dict[str, Any] | None = get_strategy_by_name(cleaned_data, strategy_name)
    strategy_model: str = strategy_data["model"]
    strategy_type: str = strategy_data["type"]
    strategy_color: str = get_strategy_color(strategy_type)
    
    all_model_data: pl.DataFrame = _get_model_data(cleaned_data, strategy_model)
    
    # ============================================================================
    # STEP 2: Pre-process data with vectorized operations
    # ============================================================================
    # Pre-process data using vectorized operations (much faster than map_elements)
    all_model_data: pl.DataFrame = all_model_data.with_columns([
        # Vectorized product name cleaning: remove trailing "ETF" (case-insensitive) and whitespace
        pl.col("product")
        .str.strip_chars()
        .str.replace(r"(?i)ETF\s*$", "", literal=False)
        .str.strip_chars()
        .alias("product_cleaned"),
        pl.col("weight").fill_null(0.0).cast(pl.Float64).alias("weight_float")
    ])
    
    selected_strategy_data: pl.DataFrame = all_model_data.filter(pl.col("strategy") == strategy_name)
    
    # ============================================================================
    # STEP 3: Build lookup dictionaries for efficient data access
    # ============================================================================
    # Optimize: Build equity_to_strategy lookup directly from DataFrame without intermediate steps
    all_strategies: pl.DataFrame = (
        all_model_data
        .select(["strategy", "portfolio"])
        .unique()
        .sort("portfolio", descending=True)
    )
    
    # Use Polars native to_dicts for faster lookup construction
    equity_to_strategy: dict[int, str] = {
        int(row["portfolio"]): row["strategy"]
        for row in all_strategies.to_dicts()
    }
    
    # Only show columns for equity levels that exist
    available_equity_levels: list[int] = [
        eq for eq in [100, 90, 80, 70, 60, 50, 40, 30, 20, 10] 
        if eq in equity_to_strategy
    ]
    
    model_aggs: list[str | None] = sorted(
        [ma for ma in selected_strategy_data["model_agg"].unique().to_list() if ma is not None],
        key=get_model_agg_sort_order
    )
    
    data: list[dict[str, Any]] = []
    row_metadata: list[dict[str, Any]] = []
    
    # Track which model_agg is the last one for the spacer row
    last_model_agg: str | None = model_aggs[-1] if model_aggs else None
    
    # Pre-process model agg names: remove "Portfolio" suffix
    model_agg_names: dict[str | None, str] = {
        ma: str(ma).replace(" Portfolio", "").replace("Portfolio", "")
        for ma in model_aggs
    }
    
    # Optimize: Build lookup using Polars native operations, convert to dict in one pass
    agg_target_lookup: dict[tuple[str, str], float] = {}
    agg_target_data: pl.DataFrame = (
        all_model_data
        .select(["strategy", "model_agg", "agg_target"])
        .unique(subset=["strategy", "model_agg"], keep="first")
    )
    # Single pass conversion to dict (preserve original null checking logic)
    for row in agg_target_data.to_dicts():
        strat_name: str = row["strategy"]
        model_agg_name: str = row["model_agg"]
        agg_target: float = row["agg_target"]
        if strat_name and model_agg_name is not None:
            agg_target_lookup[(strat_name, str(model_agg_name))] = float(agg_target) if agg_target is not None else 0.0
    
    # Optimize: Build lookup using Polars native operations, convert to dict in one pass
    product_weight_lookup: dict[tuple[str, str, str], float] = {}
    product_weight_data: pl.DataFrame = (
        all_model_data
        .select(["strategy", "model_agg", "ticker", "weight_float"])
        .unique(subset=["strategy", "model_agg", "ticker"], keep="first")
    )
    # Single pass conversion to dict
    for row in product_weight_data.to_dicts():
        strat: str = row["strategy"]
        model_agg_val: str = str(row["model_agg"])
        ticker_val: str = str(row["ticker"])
        weight_val: float = row["weight_float"]
        product_weight_lookup[(strat, model_agg_val, ticker_val)] = weight_val
    
    # ============================================================================
    # STEP 4: Iterate over model aggregates to build matrix rows
    # ============================================================================
    # Iterate over model aggs to build the matrix data
    for model_agg in model_aggs:
        model_agg_name: str = model_agg_names[model_agg]
        row_data: dict[str, Any] = {"asset": model_agg_name}
        row_metadata.append({
            "row_type": RowType.CATEGORY.value,
            "is_category": True,  # Keep for backward compatibility
            "name": model_agg_name,
            "color": strategy_color
        })
        
        # Model agg rows use agg_target
        # Product rows below use weight
        for eq_pct in available_equity_levels:
            strategy_name_at_equity: str = equity_to_strategy[eq_pct]
            strategy_model_agg_key: tuple[str, str] = (strategy_name_at_equity, str(model_agg))
            row_data[str(int(eq_pct))] = agg_target_lookup.get(strategy_model_agg_key, 0.0)
        
        data.append(row_data)
        
        products: pl.DataFrame = (
            selected_strategy_data
            .filter(pl.col("model_agg") == model_agg)
            .select(["product_cleaned", "ticker", "weight_float"])
            .sort("weight_float", descending=True)
        )
        
        # Collapse SMAs with many holdings to reduce visual clutter
        num_products: int = products.height
        should_collapse: bool = collapse_sma and num_products > SMA_COLLAPSE_THRESHOLD
        
        if not should_collapse:
            for product_row in products.to_dicts():
                product_name: str = product_row["product_cleaned"]
                ticker: str = product_row["ticker"]
                
                product_row_data: dict[str, Any] = {"asset": product_name}
                row_metadata.append({
                    "row_type": RowType.PRODUCT.value,
                    "is_category": False,  # Keep for backward compatibility
                    "name": product_name,
                    "ticker": ticker,
                    "color": strategy_color
                })
                
                # Product allocations shown across all equity levels for comparison
                for eq_pct in available_equity_levels:
                    strategy_name_at_equity: str = equity_to_strategy[eq_pct]
                    product_weight_key: tuple[str, str, str] = (
                        strategy_name_at_equity,
                        str(model_agg),
                        ticker
                    )
                    product_row_data[str(int(eq_pct))] = product_weight_lookup.get(product_weight_key, 0.0)
                
                data.append(product_row_data)
        
        # Spacer row between model aggs
        if products.height > 0 and model_agg != last_model_agg:
            spacer_row = {"asset": ""}
            for eq_pct in available_equity_levels:
                spacer_row[str(int(eq_pct))] = None
            data.append(spacer_row)
            row_metadata.append({
                "row_type": RowType.SPACER.value,
                "is_category": False,  # Keep for backward compatibility
                "is_spacer": True,  # Keep for backward compatibility
                "name": "",
                "color": strategy_color
            })
    
    # ============================================================================
    # STEP 5: Calculate highlighted column index
    # ============================================================================
    # Highlight the column corresponding to the selected strategy's equity
    highlighted_col_idx: int = 0
    if strategy_equity_pct is not None and strategy_equity_pct in available_equity_levels:
        highlighted_col_idx = available_equity_levels.index(strategy_equity_pct) + 1  # +1 for asset_formatted column
    
    return pl.DataFrame(data), highlighted_col_idx, row_metadata, equity_to_strategy


def _build_allocation_tables(
    matrix_df: pl.DataFrame,
    equity_cols: list[str],
    row_metadata: list[dict[str, Any]],
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
    strategy_color: str = row_metadata[0]["color"] if row_metadata else PRIMARY["raspberry"]
    
    # ============================================================================
    # STEP 1: Format asset names (combine with tickers)
    # ============================================================================
    asset_names_combined: list[str] = []
    for row in row_metadata:
        name: str = row["name"]
        ticker: str = row.get("ticker", "")
        is_spacer: bool = row.get("is_spacer", False)
        
        if is_spacer:
            # Spacer rows: empty content (height handled by Great Tables CSS)
            combined_name = ""
        elif not row["is_category"]:
            # Product rows: include ticker if available
            if ticker:
                combined_name = f"{name} ({ticker})"
            else:
                combined_name = name
        else:
            # Category rows: plain name
            combined_name = name
        asset_names_combined.append(combined_name)
    
    # ============================================================================
    # STEP 2: Prepare matrix data with formatted columns
    # ============================================================================
    is_category_list: list[bool] = [meta["is_category"] for meta in row_metadata]
    row_colors: list[str] = [meta.get("color", PRIMARY["raspberry"]) for meta in row_metadata]
    
    formatted_matrix_df: pl.DataFrame = matrix_df.with_columns([
        pl.Series("is_category", is_category_list),
        pl.Series("asset_formatted", asset_names_combined),
        pl.Series("row_color", row_colors),
    ])
    
    column_order: list[str] = ["asset_formatted"] + equity_cols + ["is_category", "asset", "row_color"]
    formatted_matrix_df = formatted_matrix_df.select(column_order)
    
    # ============================================================================
    # STEP 3: Pre-compute summary metrics lookup
    # ============================================================================
    # Pre-filter and group data once instead of filtering in loop
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
    
    # Build lookup dictionary for O(1) access using native Polars conversion
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
    
    # ============================================================================
    # STEP 4: Add spacer row and summary metric rows to DataFrame
    # ============================================================================
    # Calculate summary metrics for each equity level (store as numeric values)
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
        weighted_expense: float = metrics["weighted_expense"]
        weighted_yield: float = metrics["weighted_yield"]
        account_min: float = metrics["account_min"]
        
        # Store as percentages (0.0052 for 0.52%)
        summary_metrics_raw["Weighted Expense Ratio"][equity_col_name] = weighted_expense if weighted_expense else 0.0
        summary_metrics_raw["Weighted Indicated Yield"][equity_col_name] = weighted_yield if weighted_yield else 0.0
        # Store account minimum as raw number
        summary_metrics_raw["Account Minimum"][equity_col_name] = float(account_min) if account_min else 0.0
    
    # Add spacer row after last allocation row
    spacer_row: dict[str, Any] = {"asset_formatted": ""}
    for col in equity_cols:
        spacer_row[col] = None
    spacer_row["is_category"] = False
    spacer_row["asset"] = ""
    spacer_row["row_color"] = strategy_color
    
    # Add second spacer row before summary section
    spacer_row_2: dict[str, Any] = {"asset_formatted": ""}
    for col in equity_cols:
        spacer_row_2[col] = None
    spacer_row_2["is_category"] = False
    spacer_row_2["asset"] = ""
    spacer_row_2["row_color"] = strategy_color
    
    # Add summary metric rows (all numeric for compatible concatenation)
    summary_rows: list[dict[str, Any]] = []
    summary_row_names: list[str] = ["Weighted Expense Ratio", "Weighted Indicated Yield", "Account Minimum"]
    
    for summary_name in summary_row_names:
        summary_row: dict[str, Any] = {"asset_formatted": summary_name}
        for col in equity_cols:
            # Keep all values numeric for compatible concatenation
            summary_row[col] = summary_metrics_raw[summary_name].get(col, 0.0)
        summary_row["is_category"] = False
        summary_row["asset"] = summary_name
        summary_row["row_color"] = strategy_color
        summary_rows.append(summary_row)
    
    # Create spacer row DataFrames
    spacer_df: pl.DataFrame = pl.DataFrame([spacer_row])
    spacer_df_2: pl.DataFrame = pl.DataFrame([spacer_row_2])
    
    # Create summary rows DataFrame (all numeric)
    summary_df_data: pl.DataFrame = pl.DataFrame(summary_rows)
    
    # Combine DataFrames: allocation + spacer1 + spacer2 + summary (all numeric, compatible types)
    combined_df: pl.DataFrame = pl.concat([
        formatted_matrix_df,
        spacer_df,
        spacer_df_2,
        summary_df_data
    ])
    
    num_allocation_rows: int = formatted_matrix_df.height
    
    # Update row_metadata for styling
    combined_row_metadata: list[dict[str, Any]] = row_metadata.copy()
    # Add spacer rows metadata
    combined_row_metadata.append({
        "row_type": RowType.SPACER.value,
        "is_category": False,  # Keep for backward compatibility
        "is_spacer": True,  # Keep for backward compatibility
        "name": "",
        "color": strategy_color
    })
    combined_row_metadata.append({
        "row_type": RowType.SPACER.value,
        "is_category": False,  # Keep for backward compatibility
        "is_spacer": True,  # Keep for backward compatibility
        "name": "",
        "color": strategy_color
    })
    # Add summary rows metadata
    for summary_name in summary_row_names:
        combined_row_metadata.append({
            "row_type": RowType.SUMMARY.value,
            "is_category": False,  # Keep for backward compatibility
            "is_summary": True,  # Keep for backward compatibility
            "name": summary_name,
            "color": strategy_color
        })
    
    # ============================================================================
    # STEP 5: Build and style combined table
    # ============================================================================
    combined_table: GT = (
        GT(combined_df)
        .cols_hide(["is_category", "asset", "row_color"])
        .cols_label(asset_formatted=header_name)
        .sub_missing(columns=equity_cols, missing_text="")
        .cols_align(columns=equity_cols, align="center")
        .cols_align(columns=["asset_formatted"], align="left")
    )
    
    # Apply percent formatting to allocation rows only (not summary rows)
    if num_allocation_rows > 0:
        combined_table = combined_table.fmt_percent(
            columns=equity_cols,
            decimals=2,
            rows=list(range(num_allocation_rows))
        )
    
    # Format summary rows: percent for expense/yield, currency for account minimum
    num_spacer_rows: int = 2
    summary_start_idx: int = num_allocation_rows + num_spacer_rows
    
    # Find indices for expense ratio and yield rows (Account Minimum is already formatted as strings)
    expense_ratio_idx: int = summary_start_idx
    indicated_yield_idx: int = summary_start_idx + 1
    
    # Format "Weighted Expense Ratio" and "Weighted Indicated Yield" as percentages
    combined_table = combined_table.fmt_percent(
        columns=equity_cols,
        decimals=2,
        rows=[expense_ratio_idx, indicated_yield_idx]
    )
    
    # Format "Account Minimum" as compact currency (K/M suffixes)
    account_min_idx: int = summary_start_idx + 2
    
    # Create formatter function for Account Minimum
    def format_account_min(x: Any) -> str:
        """Format Account Minimum value as compact currency.
        
        ETL should ensure all account minimum values are valid numeric values.
        This function will fail if the value cannot be converted to float.
        
        Args:
            x: Account minimum value (should be numeric from ETL)
        
        Returns:
            Formatted currency string
        
        Raises:
            ValueError: If x cannot be converted to float
            TypeError: If x is not a numeric type
        """
        if x is None:
            raise ValueError(
                "Account minimum value is None. "
                "ETL pipeline must ensure all account minimum values are non-null."
            )
        if x == "":
            raise ValueError(
                "Account minimum value is empty string. "
                "ETL pipeline must ensure all account minimum values are numeric."
            )
        # ETL should ensure this is always a valid numeric value
        return format_currency_compact(float(x))
    
    # Format each equity column for Account Minimum row
    for col in equity_cols:
        combined_table = combined_table.fmt(
            columns=[col],
            rows=[account_min_idx],
            fns=format_account_min
        )
    
    # Initialize styling configuration
    style_config = TableStyleConfig()
    
    # Header uses strategy color for brand consistency
    combined_table = combined_table.tab_style(
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
        idx: combined_row_metadata[idx]["color"]
        for idx in row_groups[RowType.CATEGORY]
        if idx < len(combined_row_metadata)
    }
    
    # Apply styling by row type
    combined_table = _apply_row_styling(
        combined_table,
        row_groups[RowType.CATEGORY],
        RowType.CATEGORY,
        style_config,
        row_colors=row_colors,
        equity_cols=equity_cols,
    )
    
    combined_table = _apply_row_styling(
        combined_table,
        row_groups[RowType.PRODUCT],
        RowType.PRODUCT,
        style_config,
        equity_cols=equity_cols,
    )
    
    combined_table = _apply_row_styling(
        combined_table,
        row_groups[RowType.SPACER],
        RowType.SPACER,
        style_config,
    )
    
    combined_table = _apply_row_styling(
        combined_table,
        row_groups[RowType.SUMMARY],
        RowType.SUMMARY,
        style_config,
        strategy_color=strategy_color,
        equity_cols=equity_cols,
    )
    
    # Apply table-wide options
    combined_table = combined_table.tab_options(
        table_font_size=style_config.body_font_size,
        table_font_names=[
            style_config.body_font,
            "-apple-system",
            "BlinkMacSystemFont",
            "Segoe UI",
            "sans-serif",
        ]
    )
    
    # Ensure all body cells use IBM Plex Sans (explicit override)
    combined_table = combined_table.tab_style(
        style=[
            style.css(rule=f"font-family: '{style_config.body_font}', sans-serif !important;"),
        ],
        locations=loc.body(),
    )
    
    # Highlight selected strategy's equity column for quick identification
    if highlighted_col_idx >= 1 and highlighted_col_idx - 1 < len(equity_cols):
        highlighted_col: str = equity_cols[highlighted_col_idx - 1]
        combined_table = combined_table.tab_style(
            style=[
                style.fill(color=style_config.highlight_color),
            ],
            locations=loc.body(columns=[highlighted_col]),
        )
    
    return combined_table


def render_allocation_tab(strategy_name: str, cleaned_data: pl.LazyFrame) -> None:
    """Render allocation tab with combined matrix table showing allocations and summary metrics.
    
    Steps:
    1. Load strategy data and prepare model data
    2. Build equity matrix data (product allocations across equity levels)
    3. Format matrix data (combine asset names with tickers)
    4. Build and render combined allocation table (includes summary metrics)
    5. Render collapse SMAs checkbox
    """
    # ============================================================================
    # STEP 1: Load strategy data and prepare model data
    # ============================================================================
    strategy_data: dict[str, Any] | None = get_strategy_by_name(cleaned_data, strategy_name)
    strategy_equity_pct: int | None = None
    model_name: str | None = None
    if strategy_data:
        portfolio_val = strategy_data.get("portfolio")
        strategy_equity_pct = int(portfolio_val) if portfolio_val is not None else None
        model_name = strategy_data.get("model")
    
    collapse_sma: bool = get_or_init(ALLOCATION_COLLAPSE_SMA_KEY, DEFAULT_COLLAPSE_SMA)
    
    # Get model data for summary table (cached)
    if strategy_data and strategy_data.get("model"):
        all_model_data: pl.DataFrame = _get_model_data(cleaned_data, strategy_data["model"])
    else:
        all_model_data = pl.DataFrame()
    
    # ============================================================================
    # STEP 2: Build equity matrix data (product allocations across equity levels)
    # ============================================================================
    matrix_df, highlighted_col_idx, row_metadata, equity_to_strategy = _get_equity_matrix_data(
        cleaned_data, strategy_name, strategy_equity_pct, collapse_sma=collapse_sma
    )
    
    if matrix_df.height == 0:
        st.info("No allocation data available for this strategy.")
        return
    
    equity_cols: list[str] = [col for col in matrix_df.columns if col != "asset"]
    
    # ============================================================================
    # STEP 3: Format matrix data and build tables
    # ============================================================================
    # Prepare metadata for styling: category rows get background color, products get indentation
    is_category_list: list[bool] = [meta["is_category"] for meta in row_metadata]
    row_colors: list[str] = [meta.get("color", PRIMARY["raspberry"]) for meta in row_metadata]
    
    # Format asset names (will be done inside _build_allocation_tables)
    # Add formatted columns to matrix_df
    matrix_df = matrix_df.with_columns([
        pl.Series("is_category", is_category_list),
        pl.Series("row_color", row_colors),
    ])
    
    # Determine header name (model name preferred over strategy name)
    if model_name:
        header_name: str = str(model_name)
    else:
        header_name = strategy_name.replace(" Portfolio", "").replace("Portfolio", "")
    
    strategy_color: str = row_metadata[0]["color"] if row_metadata else PRIMARY["raspberry"]
    
    # Build combined table using Great Tables API (formatting and styling handled inside)
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
    
    # ============================================================================
    # STEP 4: Render combined allocation table
    # ============================================================================
    # Calculate column widths for consistent layout
    num_equity_cols: int = len(equity_cols)
    asset_col_width: str = "40%"  # Combined width for asset+ticker
    equity_col_width: str = f"{(60 / num_equity_cols):.2f}%" if num_equity_cols > 0 else "0%"
    
    # Set column widths using native Great Tables API instead of CSS
    width_cases: dict[str, str] = {"asset_formatted": asset_col_width}
    width_cases.update({col: equity_col_width for col in equity_cols})
    combined_table = combined_table.cols_width(cases=width_cases)
    
    # Generate table HTML from GT object
    table_html: str = combined_table.as_raw_html(inline_css=True)
    
    # Generate hash of table data for cache key
    # Hash the matrix DataFrame content and styling parameters
    # Use a single hash combining all relevant data (HTML is deterministic from data, so no need for separate hash)
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
    
    # Generate complete HTML (cached based on data hash)
    # Since HTML is deterministic from the data, we only need the data hash
    complete_html: str = _generate_allocation_table_html_cached(
        table_html, table_data_hash
    )
    
    # Render table using Great Tables with fixed column widths
    st.html(complete_html)
    
    st.divider()    

    # ============================================================================
    # STEP 6: Render collapse SMAs toggle (only if there are collapsible SMAs)
    # ============================================================================
    if _has_collapsible_smas(all_model_data, strategy_name):
        st.toggle(
            "Collapse SMAs",
            value=get_or_init(ALLOCATION_COLLAPSE_SMA_KEY, DEFAULT_COLLAPSE_SMA),
            key=ALLOCATION_COLLAPSE_SMA_KEY
        )
    