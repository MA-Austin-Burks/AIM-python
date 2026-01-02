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


def _base_layout(height=380):
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


def render_performance_tab(strategy_name, strategy_data):
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


def _render_line_chart(
    title,
    caption,
    dates,
    values,
    color,
    fillcolor,
    y_title,
    hovertemplate,
    y_format=None,
):
    st.markdown(
        f'<h3 style="color: {PRIMARY["charcoal"]}; font-family: {FONTS["headline"]}; margin-bottom: 0;">{title}</h3>',
        unsafe_allow_html=True,
    )
    st.caption(caption)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines",
            name=title,
            line={"color": color, "width": 2},
            fill="tozeroy",
            fillcolor=fillcolor,
            hovertemplate=hovertemplate,
        )
    )

    layout = _base_layout()
    layout["xaxis"]["title"] = "Date"
    layout["yaxis"]["title"] = y_title
    if y_format:
        layout["yaxis"]["tickformat"] = y_format
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)


def _render_growth_chart(dates, cumulative):
    _render_line_chart(
        "Performance",
        "Growth of $1 invested over the period",
        dates,
        cumulative,
        PRIMARY["raspberry"],
        hex_to_rgba(PRIMARY["raspberry"], 0.15),
        "Cumulative Return ($)",
        "<b>%{x}</b><br>Value: $%{y:.2f}<extra></extra>",
    )


def _render_drawdown_chart(dates, drawdown):
    _render_line_chart(
        "Drawdown",
        "Decline from historical peak value",
        dates,
        drawdown,
        TERTIARY["red"],
        hex_to_rgba(TERTIARY["red"], 0.2),
        "Drawdown (%)",
        "<b>%{x}</b><br>Drawdown: %{y:.1%}<extra></extra>",
        ".0%",
    )


def _render_volatility_chart(dates, rolling_vol):
    _render_line_chart(
        "Rolling Volatility",
        "21-day annualized rolling volatility",
        dates,
        rolling_vol,
        SECONDARY["iris"],
        hex_to_rgba(SECONDARY["iris"], 0.15),
        "Annualized Volatility",
        "<b>%{x}</b><br>Volatility: %{y:.1%}<extra></extra>",
        ".0%",
    )


def _render_correlation_matrix(strategy_name):
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
