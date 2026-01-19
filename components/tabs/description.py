from datetime import datetime
from typing import Any, Optional

import plotly.graph_objects as go
import polars as pl
import streamlit as st

from styles.branding import (
    CHART_CONFIG,
    FONTS,
    PRIMARY,
    SECONDARY,
    TERTIARY,
)
from components.constants import GROUPING_OPTIONS, PIE_CHART_MAX_ITEMS
from utils.core.data import hash_lazyframe
from utils.core.formatting import format_currency_compact


@st.cache_data
def _load_color_mappings() -> tuple[
    dict[str, str], dict[str, str], dict[str, str],  # colors
    dict[str, int], dict[str, int], dict[str, int]   # sort orders
]:
    """Load color mappings and sort orders from product classification framework CSV.
    
    Returns:
        Tuple of (asset_category_colors, asset_type_colors, asset_class_colors,
                  asset_category_sort_orders, asset_type_sort_orders, asset_class_sort_orders) dictionaries
    """
    try:
        import os
        csv_path = "data/product_classification_framework.csv"
        if not os.path.exists(csv_path):
            st.error(f"Color mapping CSV not found at: {csv_path}")
            return {}, {}, {}, {}, {}, {}
        
        color_df = pl.read_csv(csv_path)
        
        # Create mappings: name -> color
        # Use unique() to get unique combinations, keeping the first occurrence
        # Sort by sort_order first to ensure consistent selection when multiple rows exist
        asset_category_data = (
            color_df.select(["asset_category", "asset_category_color", "asset_category_sort_order"])
            .sort("asset_category_sort_order")
            .unique(subset=["asset_category"], keep="first")
            .to_dict(as_series=False)
        )
        # Normalize keys by stripping whitespace to handle any CSV formatting issues
        asset_category_map = {
            key.strip(): value 
            for key, value in zip(
                asset_category_data["asset_category"],
                asset_category_data["asset_category_color"]
            )
        }
        asset_category_sort_map = {
            key.strip(): value 
            for key, value in zip(
                asset_category_data["asset_category"],
                asset_category_data["asset_category_sort_order"]
            )
        }
        
        asset_type_data = (
            color_df.select(["asset_type", "asset_type_color", "asset_type_sort_order"])
            .sort("asset_type_sort_order")
            .unique(subset=["asset_type"], keep="first")
            .to_dict(as_series=False)
        )
        # Normalize keys by stripping whitespace
        asset_type_map = {
            key.strip(): value 
            for key, value in zip(
                asset_type_data["asset_type"],
                asset_type_data["asset_type_color"]
            )
        }
        asset_type_sort_map = {
            key.strip(): value 
            for key, value in zip(
                asset_type_data["asset_type"],
                asset_type_data["asset_type_sort_order"]
            )
        }
        
        asset_class_data = (
            color_df.select(["asset_class", "asset_class_color", "asset_class_sort_order"])
            .sort("asset_class_sort_order")
            .unique(subset=["asset_class"], keep="first")
            .to_dict(as_series=False)
        )
        # Normalize keys by stripping whitespace
        asset_class_map = {
            key.strip(): value 
            for key, value in zip(
                asset_class_data["asset_class"],
                asset_class_data["asset_class_color"]
            )
        }
        asset_class_sort_map = {
            key.strip(): value 
            for key, value in zip(
                asset_class_data["asset_class"],
                asset_class_data["asset_class_sort_order"]
            )
        }
        
        return (
            asset_category_map, asset_type_map, asset_class_map,
            asset_category_sort_map, asset_type_sort_map, asset_class_sort_map
        )
    except Exception as e:
        # Fallback to default colors if CSV can't be loaded
        st.error(f"Could not load color mappings: {e}")
        import traceback
        st.error(traceback.format_exc())
        return {}, {}, {}, {}, {}, {}


def _get_color_for_group(group_name: str, grouping_option: str) -> str:
    """Get color for a group based on grouping option.
    
    Uses colors from product_classification_framework.csv when available.
    Falls back to hash-based assignment for Product grouping or if CSV lookup fails.
    """
    # Load color mappings (cached)
    asset_category_colors, asset_type_colors, asset_class_colors, _, _, _ = _load_color_mappings()
    
    # Simple exact match lookup - lightweight since input is controlled
    if grouping_option == "Asset Category":
        color = asset_category_colors.get(group_name)
        if color:
            return color
    elif grouping_option == "Asset Type":
        color = asset_type_colors.get(group_name)
        if color:
            return color
    elif grouping_option == "Asset Class":
        color = asset_class_colors.get(group_name)
        if color:
            return color
    
    # Fallback: Hash-based assignment for Product grouping or if CSV lookup fails
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


def _get_sort_order_for_group(group_name: str, grouping_option: str) -> int:
    """Get sort order for a group based on grouping option.
    
    Uses sort orders from product_classification_framework.csv when available.
    Falls back to a large number if not found (so unknown items sort last).
    """
    # Load sort order mappings (cached)
    _, _, _, asset_category_sort, asset_type_sort, asset_class_sort = _load_color_mappings()
    
    # Simple exact match lookup - lightweight since input is controlled
    if grouping_option == "Asset Category":
        sort_order = asset_category_sort.get(group_name)
        if sort_order is not None:
            return sort_order
    elif grouping_option == "Asset Type":
        sort_order = asset_type_sort.get(group_name)
        if sort_order is not None:
            return sort_order
    elif grouping_option == "Asset Class":
        sort_order = asset_class_sort.get(group_name)
        if sort_order is not None:
            return sort_order
    
    # Fallback: Return large number so unknown items sort last
    return 999999


@st.cache_data(hash_funcs={pl.LazyFrame: hash_lazyframe})
def get_grouped_allocations_for_chart(
    cleaned_data: pl.LazyFrame,
    strategy_name: str,
    grouping_option: str,
    total_assets: float,
) -> list[dict[str, Any]]:
    """Get grouped allocation data for pie chart only.
    
    Steps:
    1. Validate and map grouping option to column name
    2. Apply product name cleaning if grouping by Product
    3. Group and aggregate allocation data
    4. Convert to chart data format with colors
    5. Combine excess items into "Others" if more than PIE_CHART_MAX_ITEMS
    """
    # ============================================================================
    # STEP 1: Validate and map grouping option to column name
    # ============================================================================
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
    
    # ============================================================================
    # STEP 2: Apply product name cleaning if grouping by Product
    # ============================================================================
    # Apply vectorized product name cleaning if grouping by Product
    strategy_data_processed = strategy_data
    if grouping_option == "Product":
        strategy_data_processed = strategy_data.with_columns([
            pl.col(group_column)
            .str.strip_chars()
            .str.replace(r"(?i)ETF\s*$", "", literal=False)
            .str.strip_chars()
            .alias(group_column)
        ])
    
    # ============================================================================
    # STEP 3: Group and aggregate allocation data
    # ============================================================================
    # When grouping by Product, also get asset_class for color/sort order lookup
    if grouping_option == "Product":
        grouped = (
            strategy_data_processed
            .group_by([group_column, "asset_class"])
            .agg([
                pl.sum("weight").alias("total_weight"),
            ])
            .group_by(group_column)
            .agg([
                pl.sum("total_weight").alias("total_weight"),
                pl.first("asset_class").alias("asset_class"),  # Take first asset_class for each product
            ])
            .filter(
                pl.col(group_column).is_not_null() &
                (pl.col(group_column) != "")
            )
            .collect()
        )
    else:
        grouped = (
            strategy_data_processed
            .group_by(group_column)
            .agg([
                pl.sum("weight").alias("total_weight"),
            ])
            .filter(
                pl.col(group_column).is_not_null() &
                (pl.col(group_column) != "")
            )
            .collect()
        )
    
    # ============================================================================
    # STEP 4: Convert to chart data format with colors and sort orders
    # ============================================================================
    data = []
    for row in grouped.to_dicts():
        group_name = str(row[group_column])
        # weight is stored as decimal (0-1), convert to percentage
        allocation_pct = float(row["total_weight"]) * 100
        
        # For Product grouping, use asset_class for color and sort order
        if grouping_option == "Product" and "asset_class" in row:
            asset_class = str(row["asset_class"])
            color = _get_color_for_group(asset_class, "Asset Class")
            sort_order = _get_sort_order_for_group(asset_class, "Asset Class")
        else:
            color = _get_color_for_group(group_name, grouping_option)
            sort_order = _get_sort_order_for_group(group_name, grouping_option)
        
        data.append({
            "name": group_name,
            "allocation": allocation_pct,
            "market_value": total_assets * allocation_pct / 100,
            "color": color,
            "sort_order": sort_order,
        })
    
    # Sort by sort_order (ascending), then by allocation (descending) as tiebreaker
    data.sort(key=lambda x: (x["sort_order"], -x["allocation"]))
    
    # ============================================================================
    # STEP 5: Combine excess items into "Others" if more than PIE_CHART_MAX_ITEMS
    # ============================================================================
    # If more than PIE_CHART_MAX_ITEMS items, combine the rest into "Others"
    if len(data) > PIE_CHART_MAX_ITEMS:
        top_items = data[:PIE_CHART_MAX_ITEMS]
        others_allocation = sum(item["allocation"] for item in data[PIE_CHART_MAX_ITEMS:])
        others_market_value = sum(item["market_value"] for item in data[PIE_CHART_MAX_ITEMS:])
        
        # Use a neutral color for "Others"
        others_color = PRIMARY["charcoal"]
        
        # Add "Others" with a high sort_order so it appears at the end
        others_item = {
            "name": "Others",
            "allocation": others_allocation,
            "market_value": others_market_value,
            "color": others_color,
            "sort_order": 999999,  # Ensure "Others" appears last
        }
        top_items.append(others_item)
        
        # Re-sort to ensure "Others" is in the correct position
        top_items.sort(key=lambda x: (x["sort_order"], -x["allocation"]))
        
        return top_items
    
    return data


def _metric_with_date(label: str, value: str, as_of: Optional[str] = None, help: Optional[str] = None) -> None:
    if as_of is None:
        as_of = datetime.now().strftime("%m-%d-%Y")
    st.metric(label, value, help=help)
    st.caption(f"as of {as_of}")


def render_description_tab(strategy_name: str, strategy_data: dict[str, Any], cleaned_data: Optional[pl.LazyFrame] = None) -> None:
    """Render description tab with summary statistics and allocation chart.
    
    Steps:
    1. Display strategy description
    2. Render summary statistics metrics
    3. Render allocation chart with grouping options
    4. Render fact sheet download button
    """
    # ============================================================================
    # STEP 1: Display strategy description
    # ============================================================================
    st.markdown(
        "Strategic, globally diversified multi-asset portfolios designed to seek long-term capital appreciation. Efficiently covers market exposures through a minimum number of holdings to reduce cost and trading."
    )

    st.divider()

    # ============================================================================
    # STEP 2: Render summary statistics metrics
    # ============================================================================
    # Summary Statistics - 2 rows x 3 columns
    st.markdown("#### Summary Statistics")
    
    # Row 1: Expense Ratio, Yield, Minimum
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    with row1_col1:
        expense_ratio = strategy_data.get("Expense Ratio", 0)
        _metric_with_date(
            "WEIGHTED AVG EXP RATIO", f"{expense_ratio * 100:.2f}%"
        )
    with row1_col2:
        y: Optional[float] = strategy_data.get("Yield")
        _metric_with_date("12-MONTH YIELD", f"{y * 100:.2f}%" if y else "0.00%")
    with row1_col3:
        minimum = strategy_data.get("Minimum", 0)
        _metric_with_date(
            "ACCOUNT MINIMUM", format_currency_compact(float(minimum)) if minimum else "$0.0"
        )
    
    st.divider()

    # ============================================================================
    # STEP 3: Render allocation chart with grouping options
    # ============================================================================
    st.markdown("#### Asset Allocation")
    # Allocation chart provides visual breakdown by grouping option
    if cleaned_data is not None:
        grouping_option: Optional[str] = st.segmented_control(
            "Group By",
            options=GROUPING_OPTIONS,
            default="Asset Class",
            key="description_allocation_grouping",
        )
        
        # Ensure grouping_option is never None (fallback to default)
        if grouping_option is None:
            grouping_option = "Asset Class"
        
        # Total assets used for market value calculation (display only)
        total_assets: float = 100000.0
        chart_data: list[dict[str, Any]] = get_grouped_allocations_for_chart(
            cleaned_data, strategy_name, grouping_option, total_assets
        )
        
        if chart_data:
            labels: list[str] = [item["name"] for item in chart_data]
            values: list[float] = [item["allocation"] for item in chart_data]
            colors: list[str] = [item["color"] for item in chart_data]

            fig: go.Figure = go.Figure(
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.5,
                    marker_colors=colors,
                    textinfo="none",
                    showlegend=False,
                    sort=False,  # Prevent Plotly from reordering slices - use our custom sort order
                    hovertemplate="<b>%{label}</b><br>%{percent:.1%}<extra></extra>",
                ),
                layout={
                    "font": {"family": FONTS["body"], "color": PRIMARY["charcoal"]},
                    "height": 500,
                    "margin": {"l": 40, "r": 20, "t": 0, "b": 40},
                },
            )
            
            # Layout chart and legend side by side
            col_chart, col_legend = st.columns([2, 1])
            with col_chart:
                st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)
                st.caption(f"as of {datetime.now().strftime('%m-%d-%Y')}")
            
            with col_legend:
                st.markdown("**Legend**")
                for item in chart_data:
                    st.markdown(
                        f'<div style="display: flex; align-items: center; margin-bottom: 0.5rem;"><span style="width: 12px; height: 12px; background: {item["color"]}; border-radius: 50%; margin-right: 8px; display: inline-block;"></span><span><strong>{item["name"]}:</strong> {item["allocation"]:.2f}%</span></div>',
                        unsafe_allow_html=True,
                    )
    
    st.divider()

    # ============================================================================
    # STEP 4: Render fact sheet download button
    # ============================================================================
    # Factsheet
    st.download_button(
        label="📄 Download Fact Sheet",
        data="",
        disabled=True,
        key=f"factsheet_download_{strategy_name}",
    )
