from datetime import datetime, timedelta

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components.branding import (
    CHART_COLORS_SEQUENTIAL_RASPBERRY,
    CHART_CONFIG,
    FONTS,
    PRIMARY,
    SECONDARY,
    TERTIARY,
    hex_to_rgba,
)


def _get_period_dates(period: str, earliest_date: datetime, latest_date: datetime) -> tuple[datetime, datetime]:
    """Calculate start and end dates for a given period."""
    today = datetime.now().date()
    
    if period == "MTD":
        start = datetime(today.year, today.month, 1)
        end = datetime.now()
    elif period == "QTD":
        quarter = (today.month - 1) // 3 + 1
        start = datetime(today.year, (quarter - 1) * 3 + 1, 1)
        end = datetime.now()
    elif period == "YTD":
        start = datetime(today.year, 1, 1)
        end = datetime.now()
    elif period == "Trailing 1-Year":
        start = datetime.now() - timedelta(days=365)
        end = datetime.now()
    elif period == "Trailing 3-Years":
        start = datetime.now() - timedelta(days=3 * 365)
        end = datetime.now()
    elif period == "Trailing 5-Years":
        start = datetime.now() - timedelta(days=5 * 365)
        end = datetime.now()
    elif period == "Trailing 10-Years":
        start = datetime.now() - timedelta(days=10 * 365)
        end = datetime.now()
    elif period == "Inception":
        start = earliest_date
        end = latest_date
    else:
        start = earliest_date
        end = latest_date
    
    return start, end


def _get_date_range_from_session(earliest_date: datetime, latest_date: datetime, key_prefix: str) -> tuple[datetime, datetime]:
    """Get current date range from session state without rendering widgets."""
    period_options = ["MTD", "QTD", "YTD", "Trailing 1-Year", "Trailing 3-Years", "Trailing 5-Years", "Trailing 10-Years", "Inception"]
    
    period_key = f"{key_prefix}_period"
    if period_key not in st.session_state:
        st.session_state[period_key] = "Inception"
    
    selected_period = st.session_state[period_key]
    start_date, end_date = _get_period_dates(selected_period, earliest_date, latest_date)
    
    return start_date, end_date


def _render_date_filters(earliest_date: datetime, latest_date: datetime, key_prefix: str) -> tuple[datetime, datetime]:
    """Render date filters and period buttons."""
    period_options = ["MTD", "QTD", "YTD", "Trailing 1-Year", "Trailing 3-Years", "Trailing 5-Years", "Trailing 10-Years", "Inception"]
    
    # Initialize period in session state if not exists
    period_key = f"{key_prefix}_period"
    if period_key not in st.session_state:
        st.session_state[period_key] = "Inception"
    
    col_left, col_right = st.columns([1, 1])
    
    with col_right:
        selected_period = st.selectbox(
            "Period",
            options=period_options,
            key=period_key,
            label_visibility="collapsed",
        )
        
        start_date, end_date = _get_period_dates(selected_period, earliest_date, latest_date)
        st.caption(f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    return start_date, end_date


def _filter_data_by_dates(dates: np.ndarray, *arrays: np.ndarray, start_date: datetime, end_date: datetime) -> tuple:
    """Filter arrays by date range."""
    mask = (dates >= start_date) & (dates <= end_date)
    filtered_dates = dates[mask]
    filtered_arrays = tuple(arr[mask] for arr in arrays)
    return (filtered_dates,) + filtered_arrays


@st.cache_data
def _get_strategy_performance(strategy_name):
    seed = hash(strategy_name) % (2**32)
    rng = np.random.default_rng(seed)

    days = 1095
    dates = np.array([datetime.now() - timedelta(days=d) for d in range(days, 0, -1)])

    daily_returns = rng.normal(0.0003, 0.015, days)
    cumulative = np.cumprod(1 + daily_returns)

    peak = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - peak) / peak

    rolling_vol = np.abs(rng.normal(0.12, 0.05, days))
    rolling_vol = np.clip(rolling_vol, 0.05, 0.30)

    return {
        "dates": dates,
        "cumulative": cumulative,
        "drawdown": drawdown,
        "rolling_vol": rolling_vol,
    }


@st.cache_data
def _get_strategy_correlations(strategy_name):
    seed = hash(strategy_name) % (2**32)
    rng = np.random.default_rng(seed)

    n = rng.integers(8, 15)
    tickers = [f"ASSET{i + 1:02d}" for i in range(n)]

    corr = rng.uniform(-0.3, 0.8, (n, n))
    corr = (corr + corr.T) / 2
    np.fill_diagonal(corr, 1.0)
    corr = np.clip(corr, -1, 1)

    return tickers, corr


def _base_layout(height=500):
    return {
        "font": {"family": FONTS["body"], "color": PRIMARY["charcoal"], "size": 12},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": PRIMARY["pale_gray"],
        "margin": {"l": 55, "r": 20, "t": 10, "b": 50},
        "height": height,
        "dragmode": False,
        "xaxis": {
            "gridcolor": PRIMARY["light_gray"],
            "linecolor": PRIMARY["light_gray"],
            "tickfont": {"size": 11},
            "title_font": {"size": 12, "color": PRIMARY["charcoal"]},
            "fixedrange": True,
            "tickformat": "%Y-%m-%d",
            "type": "date",
        },
        "yaxis": {
            "gridcolor": PRIMARY["light_gray"],
            "linecolor": PRIMARY["light_gray"],
            "tickfont": {"size": 11},
            "title_font": {"size": 12, "color": PRIMARY["charcoal"]},
            "fixedrange": True,
        },
        "hovermode": "x unified",
        "hoverlabel": {
            "bgcolor": PRIMARY["white"],
            "bordercolor": PRIMARY["raspberry"],
            "font": {"family": FONTS["body"], "color": PRIMARY["charcoal"], "size": 13},
        },
    }


def render_performance_tab(strategy_name, strategy_data):
    perf_data = _get_strategy_performance(strategy_name)
    earliest_date = perf_data["dates"][0]
    latest_date = perf_data["dates"][-1]

    sub_tabs = st.tabs(["Performance", "Drawdown", "Volatility", "Correlation"])

    with sub_tabs[0]:
        start_date, end_date = _get_date_range_from_session(earliest_date, latest_date, "performance")
        filtered_dates, filtered_cumulative = _filter_data_by_dates(
            perf_data["dates"], perf_data["cumulative"], start_date=start_date, end_date=end_date
        )
        _render_growth_chart(
            filtered_dates,
            filtered_cumulative,
            lambda: _render_date_filters(earliest_date, latest_date, "performance"),
        )
    with sub_tabs[1]:
        start_date, end_date = _get_date_range_from_session(earliest_date, latest_date, "drawdown")
        filtered_dates, filtered_drawdown = _filter_data_by_dates(
            perf_data["dates"], perf_data["drawdown"], start_date=start_date, end_date=end_date
        )
        _render_drawdown_chart(
            filtered_dates,
            filtered_drawdown,
            lambda: _render_date_filters(earliest_date, latest_date, "drawdown"),
        )
    with sub_tabs[2]:
        start_date, end_date = _get_date_range_from_session(earliest_date, latest_date, "volatility")
        filtered_dates, filtered_vol = _filter_data_by_dates(
            perf_data["dates"], perf_data["rolling_vol"], start_date=start_date, end_date=end_date
        )
        _render_volatility_chart(
            filtered_dates,
            filtered_vol,
            lambda: _render_date_filters(earliest_date, latest_date, "volatility"),
        )
    with sub_tabs[3]:
        _render_correlation_matrix(strategy_name)


def _render_line_chart(
    title,
    caption,
    dates,
    values,
    color,
    fill_alpha,
    y_title,
    hovertemplate,
    y_format=None,
    x_title="Date",
    line_width=2,
    date_filters=None,
):
    col_title, col_filters = st.columns([2, 1])
    with col_title:
        st.markdown(f"### {title}")
        st.caption(caption)
    with col_filters:
        if date_filters:
            date_filters()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines",
            name=title,
            line={"color": color, "width": line_width},
            fill="tozeroy",
            fillcolor=hex_to_rgba(color, fill_alpha),
            hovertemplate=hovertemplate,
        )
    )

    layout = _base_layout()
    layout["xaxis"]["title"] = x_title
    layout["yaxis"]["title"] = y_title
    if y_format:
        layout["yaxis"]["tickformat"] = y_format
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)


def _render_growth_chart(dates, cumulative, date_filters=None):
    _render_line_chart(
        "Performance",
        "Growth of $1 invested over the period",
        dates,
        cumulative,
        PRIMARY["raspberry"],
        0.15,
        "Cumulative Return ($)",
        "<b>%{x}</b><br>Value: $%{y:.2f}<extra></extra>",
        date_filters=date_filters,
    )


def _render_drawdown_chart(dates, drawdown, date_filters=None):
    _render_line_chart(
        "Drawdown",
        "Decline from historical peak value",
        dates,
        drawdown,
        TERTIARY["red"],
        0.2,
        "Drawdown (%)",
        "<b>%{x}</b><br>Drawdown: %{y:.1%}<extra></extra>",
        ".0%",
        date_filters=date_filters,
    )


def _render_volatility_chart(dates, rolling_vol, date_filters=None):
    _render_line_chart(
        "Rolling Volatility",
        "21-day annualized rolling volatility",
        dates,
        rolling_vol,
        SECONDARY["iris"],
        0.15,
        "Annualized Volatility",
        "<b>%{x}</b><br>Volatility: %{y:.1%}<extra></extra>",
        ".0%",
        date_filters=date_filters,
    )


def _render_correlation_matrix(strategy_name):
    st.markdown("### Correlation Matrix")
    st.caption("Correlation between asset returns")

    tickers, corr = _get_strategy_correlations(strategy_name)

    colorscale = [
        [0.0, PRIMARY["pale_gray"]],
        [0.5, CHART_COLORS_SEQUENTIAL_RASPBERRY[1]],
        [1.0, CHART_COLORS_SEQUENTIAL_RASPBERRY[3]],
    ]

    fig = go.Figure(
        go.Heatmap(
            z=corr,
            x=tickers,
            y=tickers,
            text=[[f"{v:.2f}" for v in row] for row in corr],
            texttemplate="%{text}",
            textfont={
                "size": 13,
                "color": PRIMARY["charcoal"],
                "family": FONTS["body"],
            },
            colorscale=colorscale,
            zmin=-1,
            zmax=1,
            showscale=True,
            colorbar={"title": "Correlation", "tickfont": {"size": 11}},
            hovertemplate="<b>%{y}</b> vs <b>%{x}</b><br>Correlation: %{z:.2f}<extra></extra>",
        )
    )

    layout = _base_layout(height=420)
    layout["xaxis"] = {
        "side": "bottom",
        "tickfont": {"size": 11},
        "tickangle": -30,
        "fixedrange": True,
    }
    layout["yaxis"] = {
        "autorange": "reversed",
        "tickfont": {"size": 11},
        "fixedrange": True,
    }
    layout["margin"] = {"l": 100, "r": 80, "t": 10, "b": 80}
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)
