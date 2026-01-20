"""Reusable tooltip formatting and styling for easychart charts."""

from typing import Literal

from utils.styles.branding import PRIMARY


def format_tooltip_bar_chart(
    category_placeholder: str = "{point.category}",
    value_placeholder: str = "{point.y}",
    value_format: Literal["currency", "percentage"] = "percentage",
) -> str:
    """Format tooltip for bar charts with dynamic bullet color.
    
    Args:
        category_placeholder: Placeholder for category name (e.g., "{point.category}")
        value_placeholder: Placeholder for value (e.g., "{point.y}")
        value_format: Format for the value - "currency" or "percentage"
    
    Returns:
        HTML formatted tooltip string with bullet point, label, and bold value
    """
    charcoal_color = PRIMARY["charcoal"]
    
    # Build value format string - need to properly construct Highcharts format specifiers
    # value_placeholder is "{point.y}", we need to insert format specifier before the closing brace
    if value_format == "currency":
        # For currency: ${point.y:,.0f}
        # Remove closing brace, add format, add closing brace
        value_formatted = "$" + value_placeholder[:-1] + ":,.0f}"
    else:  # percentage
        # For percentage: {point.y:.2f}%
        # Remove closing brace, add format, add closing brace and %
        value_formatted = value_placeholder[:-1] + ":.2f}%"
    
    # Build the HTML string using string concatenation to avoid f-string issues with braces
    return (
        '<span style="color: {point.color};">•</span> '
        '<span style="color: ' + charcoal_color + ';">' + category_placeholder + ':</span> '
        '<span style="color: ' + charcoal_color + '; font-weight: bold;">' + value_formatted + '</span>'
    )


def format_tooltip_pie_chart(
    name_placeholder: str = "{point.name}",
    value_placeholder: str = "{point.options.dollarFormatted}",
    use_formatted_value: bool = True,
) -> str:
    """Format tooltip for pie charts with dynamic bullet color and dollar amount.
    
    Args:
        name_placeholder: Placeholder for asset name (e.g., "{point.name}")
        value_placeholder: Placeholder for value (e.g., "{point.options.dollarFormatted}")
        use_formatted_value: If True, uses the formatted value directly; if False, formats as currency
    
    Returns:
        HTML formatted tooltip string with bullet point, label, and bold dollar amount
    """
    if use_formatted_value:
        value_formatted = value_placeholder
    else:
        value_formatted = f'${{{value_placeholder}:,.0f}}'
    
    return (
        f'<span style="color: {{point.color}};">•</span> '
        f'<span style="color: {PRIMARY["charcoal"]};">{name_placeholder}:</span> '
        f'<span style="color: {PRIMARY["charcoal"]}; font-weight: bold;">{value_formatted}</span>'
    )


def apply_tooltip_styling(chart) -> None:
    """Apply consistent tooltip styling to an easychart chart.
    
    Args:
        chart: easychart chart object to style
    """
    try:
        chart.tooltip.shared = False
        chart.tooltip.headerFormat = ""
        chart.tooltip.useHTML = True
        # Style the tooltip container
        chart.tooltip.backgroundColor = PRIMARY["pale_gray"]
        chart.tooltip.borderColor = PRIMARY["charcoal"]
        chart.tooltip.borderRadius = 4
        chart.tooltip.borderWidth = 1
        chart.tooltip.shadow = True
        chart.tooltip.style = {
            "color": PRIMARY["charcoal"],
            "padding": "8px 12px"
        }
    except (AttributeError, TypeError):
        # Fallback: set via dict if direct assignment doesn't work
        if not hasattr(chart, "tooltip"):
            chart.tooltip = {}
        chart.tooltip["shared"] = False
        chart.tooltip["headerFormat"] = ""
        chart.tooltip["useHTML"] = True
        chart.tooltip["backgroundColor"] = PRIMARY["pale_gray"]
        chart.tooltip["borderColor"] = PRIMARY["charcoal"]
        chart.tooltip["borderRadius"] = 4
        chart.tooltip["borderWidth"] = 1
        chart.tooltip["shadow"] = True
        chart.tooltip["style"] = {
            "color": PRIMARY["charcoal"],
            "padding": "8px 12px"
        }
