"""Compare Models page - side-by-side comparison of up to 3 models."""

from typing import Any, Optional

import easychart
import polars as pl
import streamlit as st

from components import render_footer
from components.dataframe import filter_and_sort_strategies, _hash_filter_expression
from components.filters import render_filters, render_filters_inline
from components.tabs.description import get_grouped_allocations_for_chart
from utils.styles.branding import (
    CHART_COLORS_PRIMARY,
    FONTS,
    PRIMARY,
    format_currency_compact,
    get_strategy_color,
)
from utils.core.constants import DEFAULT_TOTAL_ASSETS, GROUPING_OPTIONS
from utils.core.data import load_cleaned_data, load_strategy_list
from utils.core.session_state import initialize_session_state
from utils.core.chart_tooltips import (
    format_tooltip_bar_chart,
    format_tooltip_pie_chart,
    apply_tooltip_styling,
)

st.set_page_config(page_title="Compare Models", layout="wide")

# Initialize session state explicitly at app start
initialize_session_state()


def apply_brand_theme(chart):
    """Apply Mercer Advisors brand theming to easychart."""
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


# Load data
strats: pl.DataFrame = load_strategy_list()
cleaned_data: pl.LazyFrame = load_cleaned_data()

st.markdown("# Compare Models")

st.markdown(
    "Select up to 3 models to compare their key metrics, allocations, and characteristics side-by-side."
)

st.divider()

# Render filters inline (no search on this page, so search_active=False)
render_filters_inline(search_active=False)

# Get filter expression from session state
filter_expr: pl.Expr = render_filters(search_active=False)

# Filter strategies based on filters
filter_hash: str = _hash_filter_expression(filter_expr)
filtered_strategies: pl.DataFrame = filter_and_sort_strategies(strats, filter_expr, filter_hash)

# Model selection dropdowns
col1, col2, col3 = st.columns(3)

selected_models: list[Optional[str]] = []

# Default strategies
default_strategies = [
    "Multifactor 90 TM (ETF, All Weather)",
    "Market 60 (ETF)",
    "Income 70 TM (ETF)",
]

# Get filtered strategies list
all_strategies = sorted(filtered_strategies["Strategy"].unique().to_list())

# Helper function to get index for default strategy
def get_default_index(default_strategy: str, available_strategies: list[str]) -> int:
    """Get the index for a default strategy in the dropdown, or 0 if not available."""
    if default_strategy in available_strategies:
        return available_strategies.index(default_strategy) + 1  # +1 for None option
    return 0

with col1:
    model_1 = st.selectbox(
        "Model 1",
        options=[None] + all_strategies,
        index=get_default_index(default_strategies[0], all_strategies),
        key="compare_model_1",
    )
    selected_models.append(model_1)

with col2:
    model_2 = st.selectbox(
        "Model 2",
        options=[None] + all_strategies,
        index=get_default_index(default_strategies[1], all_strategies),
        key="compare_model_2",
    )
    selected_models.append(model_2)

with col3:
    model_3 = st.selectbox(
        "Model 3",
        options=[None] + all_strategies,
        index=get_default_index(default_strategies[2], all_strategies),
        key="compare_model_3",
    )
    selected_models.append(model_3)

# Filter out None values
selected_models = [m for m in selected_models if m is not None]

if not selected_models:
    st.info("👆 Please select at least one model to compare.")
    render_footer()
    st.stop()

# Get data for selected models (use filtered_strategies to ensure consistency)
models_data: list[dict[str, Any]] = []
for model_name in selected_models:
    model_row = filtered_strategies.filter(pl.col("Strategy") == model_name)
    if model_row.height > 0:
        model_dict = model_row.row(0, named=True)
        models_data.append(model_dict)

if not models_data:
    st.error("No data found for selected models.")
    render_footer()
    st.stop()

st.divider()

# ============================================================================
# Summary Metrics Comparison
# ============================================================================
st.markdown("## Summary Metrics")

# Create comparison metrics
num_models = len(models_data)
cols = st.columns(num_models)

for idx, (col, model_dict) in enumerate(zip(cols, models_data)):
    with col:
        model_name = model_dict["Strategy"]
        strategy_type = model_dict.get("Type", "")
        strategy_color = get_strategy_color(strategy_type)
        recommended = model_dict.get("Recommended", False)
        
        # Display model name with color and star in header
        star_icon = "⭐ " if recommended else ""
        st.markdown(
            f'<div style="background-color: {strategy_color}; color: white; padding: 12px; border-radius: 8px; margin-bottom: 16px;">'
            f'<h3 style="margin: 0; color: white; display: flex; align-items: center; gap: 8px;">'
            f'<span>{star_icon}</span><span>{model_name}</span>'
            f'</h3>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        # Key metrics in 2x2 grid
        expense_ratio = model_dict.get("Expense Ratio", 0)
        yield_val = model_dict.get("Yield")
        minimum = model_dict.get("Minimum", 0)
        equity_pct = model_dict.get("Equity %", 0)
        
        # Create 2x2 grid using columns
        metric_col1, metric_col2 = st.columns(2)
        
        with metric_col1:
            st.metric("Expense Ratio", f"{expense_ratio * 100:.2f}%")
            st.metric("Account Minimum", format_currency_compact(float(minimum)) if minimum else "$0")
        
        with metric_col2:
            st.metric("12-Month Yield", f"{yield_val * 100:.2f}%" if yield_val else "N/A")
            st.metric("Equity %", f"{equity_pct:.0f}%")

st.divider()

# ============================================================================
# Side-by-side Metrics Visualization
# ============================================================================
# Calculate averages across all filtered strategies (Polars mean() automatically ignores nulls)
avg_expense_ratio = (
    filtered_strategies["Expense Ratio"].mean() * 100 
    if filtered_strategies.height > 0 and filtered_strategies["Expense Ratio"].null_count() < filtered_strategies.height 
    else 0
)
avg_yield = (
    filtered_strategies["Yield"].mean() * 100 
    if filtered_strategies.height > 0 and filtered_strategies["Yield"].null_count() < filtered_strategies.height 
    else 0
)
avg_minimum = (
    filtered_strategies["Minimum"].mean() 
    if filtered_strategies.height > 0 and filtered_strategies["Minimum"].null_count() < filtered_strategies.height 
    else 0
)

# Create bar charts comparing key metrics
metrics_to_compare = ["Expense Ratio", "Yield", "Account Minimum"]
metric_cols = st.columns(len(metrics_to_compare))

for metric_idx, (metric_col, metric_name) in enumerate(zip(metric_cols, metrics_to_compare)):
    with metric_col:
        st.markdown(f"**{metric_name}**")
        
        # Extract values for selected models
        model_names = [m["Strategy"] for m in models_data]
        if metric_name == "Expense Ratio":
            values = [m.get("Expense Ratio", 0) * 100 for m in models_data]
            avg_value = avg_expense_ratio
            y_label = "Percentage (%)"
        elif metric_name == "Yield":
            values = [m.get("Yield", 0) * 100 if m.get("Yield") else 0 for m in models_data]
            avg_value = avg_yield
            y_label = "Percentage (%)"
        else:  # Account Minimum
            values = [m.get("Minimum", 0) for m in models_data]
            avg_value = avg_minimum
            y_label = "Amount ($)"
        
        # Get colors for each model
        colors = [get_strategy_color(m.get("Type", "")) for m in models_data]
        
        # Add average column with distinct color (average of all filtered strategies)
        model_names.append("Average (All Strategies)")
        values.append(avg_value)
        colors.append(PRIMARY["charcoal"])  # Use charcoal for average bar
        
        # Create bar chart data with colors
        bar_data = [
            {"y": val, "color": color}
            for val, color in zip(values, colors)
        ]
        
        # Format labels and tooltips based on metric type
        if metric_name == "Account Minimum":
            # Format as currency for Account Minimum
            labels_format = "{point.y:,.0f}"
            tooltip_format = format_tooltip_bar_chart(value_format="currency")
        else:
            # Format as percentage for Expense Ratio and Yield
            labels_format = "{point.y:.2f}%"
            tooltip_format = format_tooltip_bar_chart(value_format="percentage")
        
        chart = easychart.new("column", legend=False)
        chart.categories = model_names
        chart.plot(bar_data, name=metric_name, labels=labels_format)
        chart.title = None
        chart.yAxis.title = y_label
        
        # Apply tooltip formatting and styling
        chart.tooltip.pointFormat = tooltip_format
        apply_tooltip_styling(chart)
        # Set bottom margin to prevent x-axis labels from being cut off
        try:
            chart.chart.marginBottom = 80
        except (AttributeError, TypeError):
            if not hasattr(chart, "chart"):
                chart.chart = {}
            chart.chart["marginBottom"] = 80
        render_easychart(chart, height=380)

st.divider()

# ============================================================================
# Allocation Comparison
# ============================================================================
st.markdown("## Asset Allocation Comparison")

# Grouping option selector
grouping_option: Optional[str] = st.segmented_control(
    "Group By",
    options=GROUPING_OPTIONS,
    default="Asset Class",
    key="compare_allocation_grouping",
)

if grouping_option is None:
    grouping_option = "Asset Class"

# Render allocation charts side by side
num_charts = len(models_data)
chart_cols = st.columns(num_charts)

for idx, (col, model_dict) in enumerate(zip(chart_cols, models_data)):
    with col:
        model_name = model_dict["Strategy"]
        strategy_type = model_dict.get("Type", "")
        strategy_color = get_strategy_color(strategy_type)
        
        st.markdown(f"**{model_name}**")
        
        # Get allocation data
        chart_data: list[dict[str, Any]] = get_grouped_allocations_for_chart(
            cleaned_data, model_name, grouping_option, DEFAULT_TOTAL_ASSETS
        )
        
        if chart_data:
            # Prepare data for easychart pie chart
            # Calculate and format dollar amount for each item
            pie_data = []
            for item in chart_data:
                dollar_amount = (item["allocation"] * DEFAULT_TOTAL_ASSETS) / 100
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
            render_easychart(chart, height=400)
            
            # Legend
            st.markdown("**Breakdown:**")
            for item in chart_data:
                st.markdown(
                    f'<div style="display: flex; align-items: center; margin-bottom: 0.25rem;">'
                    f'<span style="width: 12px; height: 12px; background: {item["color"]}; '
                    f'border-radius: 50%; margin-right: 8px; display: inline-block;"></span>'
                    f'<span><strong>{item["name"]}:</strong> {item["allocation"]:.2f}%</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No allocation data available.")

# Footer
render_footer()
