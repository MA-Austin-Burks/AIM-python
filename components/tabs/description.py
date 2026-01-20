from datetime import datetime
from typing import Any, Optional

import easychart
import polars as pl
import streamlit as st

from utils.styles.branding import (
    CHART_COLORS_PRIMARY,
    FONTS,
    PRIMARY,
    format_currency_compact,
)
from utils.core.chart_tooltips import (
    format_tooltip_pie_chart,
    apply_tooltip_styling,
)
from utils.core.constants import DEFAULT_TOTAL_ASSETS
from utils.core.constants import GROUPING_OPTIONS, PIE_CHART_MAX_ITEMS
from utils.core.data import hash_lazyframe


@st.cache_data
def _load_color_mappings() -> tuple[
    dict[str, str], dict[str, str], dict[str, str],  # colors
    dict[str, int], dict[str, int], dict[str, int]   # sort orders
]:
    """Load color mappings and sort orders from product classification framework CSV.
    
    ETL should ensure this CSV exists and is properly formatted.
    This function will fail fast if the CSV is missing or malformed.
    
    Returns:
        Tuple of (asset_category_colors, asset_type_colors, asset_class_colors,
                  asset_category_sort_orders, asset_type_sort_orders, asset_class_sort_orders) dictionaries
    
    Raises:
        FileNotFoundError: If CSV file is missing
        Exception: If CSV cannot be read or is malformed
    """
    import os
    csv_path = "data/product_classification_framework.csv"
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Color mapping CSV not found at: {csv_path}. "
            "ETL pipeline must generate this file."
        )
    
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


def _get_color_for_group(group_name: str, grouping_option: str) -> str:
    """Get color for a group based on grouping option.
    
    ETL should ensure all groups have colors defined in product_classification_framework.csv.
    This function will fail if a color is missing.
    
    Args:
        group_name: Name of the group to get color for
        grouping_option: One of "Asset Category", "Asset Type", "Asset Class", or "Product"
    
    Returns:
        Color hex string for the group
    
    Raises:
        KeyError: If group_name is not found in the color mappings
    """
    # Load color mappings (cached)
    asset_category_colors, asset_type_colors, asset_class_colors, _, _, _ = _load_color_mappings()
    
    # Simple exact match lookup - ETL should ensure all groups have colors
    if grouping_option == "Asset Category":
        if group_name not in asset_category_colors:
            raise KeyError(
                f"Color not found for Asset Category '{group_name}'. "
                "ETL pipeline must include all asset categories in product_classification_framework.csv"
            )
        return asset_category_colors[group_name]
    elif grouping_option == "Asset Type":
        if group_name not in asset_type_colors:
            raise KeyError(
                f"Color not found for Asset Type '{group_name}'. "
                "ETL pipeline must include all asset types in product_classification_framework.csv"
            )
        return asset_type_colors[group_name]
    elif grouping_option == "Asset Class":
        if group_name not in asset_class_colors:
            raise KeyError(
                f"Color not found for Asset Class '{group_name}'. "
                "ETL pipeline must include all asset classes in product_classification_framework.csv"
            )
        return asset_class_colors[group_name]
    elif grouping_option == "Product":
        # For Product grouping, use the asset_class color (products inherit from their asset class)
        # This should be handled by the caller, but if we get here, fail explicitly
        raise ValueError(
            "Product grouping should use asset_class for color lookup. "
            "ETL pipeline must ensure products have associated asset_class values."
        )
    else:
        raise ValueError(f"Unknown grouping option: {grouping_option}")


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
        # ETL should ensure products have asset_class values
        if grouping_option == "Product":
            if "asset_class" not in row or not row["asset_class"]:
                raise ValueError(
                    f"Product '{group_name}' is missing asset_class. "
                    "ETL pipeline must ensure all products have asset_class values."
                )
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


def apply_brand_theme(chart):
    """Apply branding and theming to easychart."""
    # Set colors
    chart.colors = CHART_COLORS_PRIMARY
    
    # Background styling
    chart.backgroundColor = PRIMARY["white"]
    chart.plotBackgroundColor = PRIMARY["white"]
    
    # Set fonts - handle title as string or object
    if hasattr(chart, "title") and chart.title:
        if isinstance(chart.title, str):
            chart.title = {
                "text": chart.title,
                "style": {
                    "fontFamily": FONTS["headline"],
                    "fontSize": "18px",
                    "color": PRIMARY["charcoal"],
                    "fontWeight": "700"
                }
            }
        elif isinstance(chart.title, dict):
            chart.title.setdefault("style", {})
            chart.title["style"].update({
                "fontFamily": FONTS["headline"],
                "fontSize": "18px",
                "color": PRIMARY["charcoal"],
                "fontWeight": "700"
            })
    
    # Axis styling
    if hasattr(chart, "yAxis"):
        if hasattr(chart.yAxis, "title"):
            if isinstance(chart.yAxis.title, str):
                chart.yAxis.title = {
                    "text": chart.yAxis.title,
                    "style": {
                        "fontFamily": FONTS["body"],
                        "color": PRIMARY["charcoal"],
                        "fontSize": "14px"
                    }
                }
            elif isinstance(chart.yAxis.title, dict):
                chart.yAxis.title.setdefault("style", {})
                chart.yAxis.title["style"].update({
                    "fontFamily": FONTS["body"],
                    "color": PRIMARY["charcoal"],
                    "fontSize": "14px"
                })
        
        try:
            chart.yAxis.lineColor = PRIMARY["charcoal"]
            chart.yAxis.tickColor = PRIMARY["charcoal"]
            chart.yAxis.gridLineColor = PRIMARY["light_gray"]
        except (AttributeError, TypeError):
            pass
    
    if hasattr(chart, "xAxis"):
        if hasattr(chart.xAxis, "title"):
            if isinstance(chart.xAxis.title, str):
                chart.xAxis.title = {
                    "text": chart.xAxis.title,
                    "style": {
                        "fontFamily": FONTS["body"],
                        "color": PRIMARY["charcoal"],
                        "fontSize": "14px"
                    }
                }
            elif isinstance(chart.xAxis.title, dict):
                chart.xAxis.title.setdefault("style", {})
                chart.xAxis.title["style"].update({
                    "fontFamily": FONTS["body"],
                    "color": PRIMARY["charcoal"],
                    "fontSize": "14px"
                })
        
        try:
            chart.xAxis.lineColor = PRIMARY["charcoal"]
            chart.xAxis.tickColor = PRIMARY["charcoal"]
            chart.xAxis.gridLineColor = PRIMARY["light_gray"]
        except (AttributeError, TypeError):
            pass
    
    return chart


def render_easychart(chart, height=400):
    """Helper function to render easychart charts in Streamlit with brand theming."""
    easychart.config.rendering.responsive = True
    chart = apply_brand_theme(chart)
    chart_html = easychart.rendering.render(chart)
    st.components.v1.html(chart_html, height=height, width="stretch")


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
        from utils.core.constants import DEFAULT_TOTAL_ASSETS
        
        total_assets: float = DEFAULT_TOTAL_ASSETS
        chart_data: list[dict[str, Any]] = get_grouped_allocations_for_chart(
            cleaned_data, strategy_name, grouping_option, total_assets
        )
        
        if chart_data:
            # Prepare data for easychart pie chart with formatted dollar amounts
            pie_data = []
            for item in chart_data:
                dollar_amount = item.get("market_value", total_assets * item["allocation"] / 100)
                dollar_formatted = f"${dollar_amount:,.0f}"
                pie_data.append({
                    "name": item["name"],
                    "y": item["allocation"],
                    "color": item["color"],
                    "dollarFormatted": dollar_formatted
                })
            
            chart = easychart.new("pie", legend=False)
            chart.plot(pie_data)
            chart.title = None
            
            # Apply tooltip formatting and styling
            tooltip_format = format_tooltip_pie_chart()
            chart.tooltip.pointFormat = tooltip_format
            apply_tooltip_styling(chart)
            # Create donut chart (innerSize creates the hole in the center)
            try:
                chart.plotOptions.pie.innerSize = "50%"
            except (AttributeError, TypeError):
                # Fallback: set via dict if direct assignment doesn't work
                if not hasattr(chart, "plotOptions"):
                    chart.plotOptions = {}
                chart.plotOptions["pie"] = {"innerSize": "50%"}
            
            # Layout chart and legend side by side
            col_chart, col_legend = st.columns([2, 1])
            with col_chart:
                render_easychart(chart, height=500)
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
