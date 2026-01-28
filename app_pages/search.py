import hashlib
from datetime import datetime

import polars as pl
import streamlit as st

from components import (
    build_filter_expression,
    render_card_view,
    render_filters,
    render_footer,
)
from components.cards import (
    CARD_ORDER_KEY,
    CARDS_DISPLAYED_KEY,
    CARDS_PER_LOAD,
    DEFAULT_CARD_ORDER,
    SELECTED_MODAL_TYPE_KEY,
    SELECTED_STRATEGY_MODAL_KEY,
)
from components.modals import render_modal_by_type
from utils.branding import SUBTYPE_COLORS, get_subtype_color
from utils.data import load_cleaned_data, load_strategy_list
from utils.models import CAISSummary, StrategySummary
from utils.models.base import _normalize_bool, _normalize_subtype
from utils.session_state import get_or_init, initialize_session_state, reset_if_changed

CARD_ORDER_OPTIONS = [
    "Recommended (Default)",
    "Acct Min - Highest to Lowest",
    "Acct Min - Lowest to Highest",
    "Expense Ratio - Highest to Lowest",
    "Expense Ratio - Lowest to Highest",
    "Yield - High to Low",
    "Yield - Low to High",
    "Equity % - High to Low",
    "Equity % - Low to High",
    "Strategy Name - A to Z",
    "Strategy Name - Z to A",
]


def _hash_filter_expression(filter_expr: pl.Expr) -> str:
    """Create a stable hash for filter expression."""
    # Convert expression to string representation for hashing
    filter_str = str(filter_expr)
    return hashlib.md5(filter_str.encode()).hexdigest()


@st.cache_data
def filter_and_sort_strategies(
    strats: pl.DataFrame, _filter_expr: pl.Expr, filter_hash: str
) -> pl.DataFrame:
    """Filter and sort the strategy table DataFrame.

    Cached using filter_hash as part of the cache key to avoid re-filtering
    when filters haven't changed.

    Args:
        strats: Strategy-level DataFrame (already collected, not LazyFrame)
        _filter_expr: Polars filter expression from sidebar (prefixed with _ to exclude from cache key)
        filter_hash: Hash of the filter expression for cache key (computed in app.py)
    """
    # Default sort prioritizes Investment Committee recommendations
    return strats.filter(_filter_expr).sort(
        by=["ic_recommend", "equity_allo", "strategy"],
        descending=[True, True, False],
        nulls_last=True,
    )


# Initialize session state explicitly at app start
initialize_session_state()

st.markdown("# Aspen Investing Menu (Development Version - v2.1)")

strats: pl.DataFrame = load_strategy_list()
cleaned_data: pl.LazyFrame = load_cleaned_data()

st.caption(f"last updated: {datetime.now().strftime('%Y-%m-%d')}")

render_filters()
st.space(1)

card_order: str = get_or_init(CARD_ORDER_KEY, DEFAULT_CARD_ORDER)
selected_order: str = st.selectbox(
    "Order By:",
    options=CARD_ORDER_OPTIONS,
    index=CARD_ORDER_OPTIONS.index(card_order)
    if card_order in CARD_ORDER_OPTIONS
    else 0,
    key="card_order_by_select",
    on_change=lambda: st.session_state.update({CARDS_DISPLAYED_KEY: CARDS_PER_LOAD}),
)
st.session_state[CARD_ORDER_KEY] = selected_order

filter_expr: pl.Expr = build_filter_expression()
filter_hash: str = _hash_filter_expression(filter_expr)
filtered_strategies: pl.DataFrame = filter_and_sort_strategies(
    strats, filter_expr, filter_hash
)

reset_if_changed("last_filter_hash", filter_hash, CARDS_DISPLAYED_KEY, CARDS_PER_LOAD)
render_card_view(filtered_strategies)

strategy_name: str | None = st.session_state.get(SELECTED_STRATEGY_MODAL_KEY)
modal_type: str | None = st.session_state.get(SELECTED_MODAL_TYPE_KEY)
if strategy_name and modal_type:
    strategy_row: pl.DataFrame = filtered_strategies.filter(
        pl.col("strategy") == strategy_name
    )
    if strategy_row.height > 0:
        row_dict = strategy_row.row(0, named=True)

        # Check if this is a CAIS row
        if (
            modal_type == "cais"
            and "cais_type" in row_dict
            and row_dict["cais_type"] is not None
        ):
            # For CAIS modals, create a minimal StrategySummary from CAIS data
            # The modal will use the CAIS-specific data internally if needed
            cais_data = CAISSummary.from_row(row_dict)
            # Create a minimal StrategySummary for modal compatibility
            strategy_data = StrategySummary(
                strategy=cais_data.strategy,
                recommended=False,
                equity_pct=0.0,
                yield_decimal=0.0,
                expense_ratio_decimal=0.0,
                minimum=cais_data.minimum,
                subtype=["Alternative Strategies"],
                subtype_primary="Alternative Strategies",
                type="Asset Class",
                tax_managed=False,
                private_markets=True,
                sma=False,
                vbi=False,
            )
            strategy_color: str = SUBTYPE_COLORS.get(
                "Alternative Strategies", "#F9A602"
            )
        else:
            # Regular strategy modal - create StrategySummary directly from row dict
            strategy_data = StrategySummary(
                strategy=str(row_dict.get("strategy", "")),
                recommended=_normalize_bool(row_dict.get("ic_recommend", False)),
                equity_pct=float(row_dict.get("equity_allo", 0) or 0),
                yield_decimal=float(row_dict.get("yield", 0) or 0),
                expense_ratio_decimal=float(row_dict.get("fee", 0) or 0),
                minimum=float(row_dict.get("minimum", 0) or 0),
                subtype=_normalize_subtype(row_dict.get("series", [])),
                subtype_primary=str(row_dict.get("ss_subtype", "")),
                type=str(row_dict.get("ss_type", "")),
                tax_managed=_normalize_bool(row_dict.get("has_tm", False)),
                private_markets=_normalize_bool(
                    row_dict.get("has_private_market", False)
                ),
                sma=_normalize_bool(row_dict.get("has_sma", False)),
                vbi=_normalize_bool(row_dict.get("has_VBI", False)),
            )
            strategy_color: str = get_subtype_color(strategy_data.subtype_primary)

        render_modal_by_type(
            modal_type, strategy_name, strategy_data, strategy_color, cleaned_data
        )
    del st.session_state[SELECTED_STRATEGY_MODAL_KEY]
    del st.session_state[SELECTED_MODAL_TYPE_KEY]

render_footer()
