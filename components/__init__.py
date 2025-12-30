"""Component modules for the Aspen Investing Menu app."""

from components.dataframe import (
    format_display_dataframe,
    render_dataframe,
    render_dataframe_section,
)
from components.expressions import (
    fmt_cur,
    fmt_dec,
    fmt_equity_pct,
    fmt_pct,
    fmt_tax_managed,
)
from components.filters import build_filter_expression
from components.footer import render_footer
from components.header import render_page_header
from components.sidebar import render_sidebar
from components.tabs import render_tabs
from components.utils import filter_and_sort_strategies, load_strats

__all__ = [
    "format_display_dataframe",
    "render_dataframe",
    "render_dataframe_section",
    "fmt_cur",
    "fmt_dec",
    "fmt_equity_pct",
    "fmt_pct",
    "fmt_tax_managed",
    "build_filter_expression",
    "render_footer",
    "render_page_header",
    "render_sidebar",
    "render_tabs",
    "filter_and_sort_strategies",
    "load_strats",
]