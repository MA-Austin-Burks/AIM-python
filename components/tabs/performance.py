"""Performance tab component with sub-tabs."""

from datetime import datetime, timedelta
from typing import Any

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components.branding import (
    CHART_COLORS_SEQUENTIAL_RASPBERRY,
    FONTS,
    PRIMARY,
    SECONDARY,
    TERTIARY,
)

CHART_CONFIG = {"displayModeBar": False, "scrollZoom": False}


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def _get_strategy_performance(strategy_name: str) -> dict:
    """Generate random performance data for a specific strategy."""
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


def _get_strategy_correlations(strategy_name: str) -> tuple[list[str], np.ndarray]:
    """Generate random correlation matrix for a specific strategy."""
    seed = hash(strategy_name) % (2**32)
    rng = np.random.default_rng(seed)

    n = rng.integers(8, 15)
    tickers = [f"ASSET{i + 1:02d}" for i in range(n)]

    corr = rng.uniform(-0.3, 0.8, (n, n))
    corr = (corr + corr.T) / 2
    np.fill_diagonal(corr, 1.0)
    corr = np.clip(corr, -1, 1)

    return tickers, corr


def _base_layout(height: int = 380) -> dict:
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


def render_performance_tab(strategy_name: str, strategy_data: dict[str, Any]) -> None:
    perf_data = _get_strategy_performance(strategy_name)

    sub_tabs = st.tabs(["Performance", "Drawdown", "Volatility", "Correlation"])

    with sub_tabs[0]:
        _render_growth_chart(perf_data["dates"], perf_data["cumulative"])
    with sub_tabs[1]:
        _render_drawdown_chart(perf_data["dates"], perf_data["drawdown"])
    with sub_tabs[2]:
        _render_volatility_chart(perf_data["dates"], perf_data["rolling_vol"])
    with sub_tabs[3]:
        _render_correlation_matrix(strategy_name)


def _render_growth_chart(dates: np.ndarray, cumulative: np.ndarray) -> None:
    st.markdown(
        f'<h3 style="color: {PRIMARY["charcoal"]}; font-family: {FONTS["headline"]}; margin-bottom: 0;">Performance</h3>',
        unsafe_allow_html=True,
    )
    st.caption("Growth of $1 invested over the period")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=cumulative,
            mode="lines",
            name="Portfolio",
            line={"color": PRIMARY["raspberry"], "width": 2},
            fill="tozeroy",
            fillcolor=_hex_to_rgba(PRIMARY["raspberry"], 0.15),
            hovertemplate="<b>%{x}</b><br>Value: $%{y:.2f}<extra></extra>",
        )
    )

    layout = _base_layout()
    layout["xaxis"]["title"] = "Date"
    layout["yaxis"]["title"] = "Cumulative Return ($)"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)


def _render_drawdown_chart(dates: np.ndarray, drawdown: np.ndarray) -> None:
    st.markdown(
        f'<h3 style="color: {PRIMARY["charcoal"]}; font-family: {FONTS["headline"]}; margin-bottom: 0;">Drawdown</h3>',
        unsafe_allow_html=True,
    )
    st.caption("Decline from historical peak value")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=drawdown,
            mode="lines",
            name="Drawdown",
            line={"color": TERTIARY["red"], "width": 2},
            fill="tozeroy",
            fillcolor=_hex_to_rgba(TERTIARY["red"], 0.2),
            hovertemplate="<b>%{x}</b><br>Drawdown: %{y:.1%}<extra></extra>",
        )
    )

    layout = _base_layout()
    layout["xaxis"]["title"] = "Date"
    layout["yaxis"]["title"] = "Drawdown (%)"
    layout["yaxis"]["tickformat"] = ".0%"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)


def _render_volatility_chart(dates: np.ndarray, rolling_vol: np.ndarray) -> None:
    st.markdown(
        f'<h3 style="color: {PRIMARY["charcoal"]}; font-family: {FONTS["headline"]}; margin-bottom: 0;">Rolling Volatility</h3>',
        unsafe_allow_html=True,
    )
    st.caption("21-day annualized rolling volatility")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=rolling_vol,
            mode="lines",
            name="Volatility",
            line={"color": SECONDARY["iris"], "width": 2},
            fill="tozeroy",
            fillcolor=_hex_to_rgba(SECONDARY["iris"], 0.15),
            hovertemplate="<b>%{x}</b><br>Volatility: %{y:.1%}<extra></extra>",
        )
    )

    layout = _base_layout()
    layout["xaxis"]["title"] = "Date"
    layout["yaxis"]["title"] = "Annualized Volatility"
    layout["yaxis"]["tickformat"] = ".0%"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)


def _render_correlation_matrix(strategy_name: str) -> None:
    st.markdown(
        f'<h3 style="color: {PRIMARY["charcoal"]}; font-family: {FONTS["headline"]}; margin-bottom: 0;">Correlation Matrix</h3>',
        unsafe_allow_html=True,
    )
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
