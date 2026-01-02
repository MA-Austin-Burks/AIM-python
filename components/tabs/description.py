"""Description tab component."""

import random
from datetime import datetime
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from components.branding import CHART_COLORS_PRIMARY, PRIMARY, get_chart_layout

CHART_CONFIG = {"displayModeBar": False, "scrollZoom": False}


def render_description_tab(strategy_name: str, strategy_data: dict[str, Any]) -> None:
    equity_pct = float(strategy_data["Equity %"])
    has_private = strategy_data.get("Private Markets", False)

    alt_pct = random.randint(5, 15) if has_private else 0
    fixed_pct = 100 - equity_pct - alt_pct

    # Header
    st.markdown(f'<h1 style="color: {PRIMARY["raspberry"]}; margin-bottom: 0;">{strategy_name}</h1>', unsafe_allow_html=True)
    
    exposure = f"{int(equity_pct)}% Equity - {int(fixed_pct)}% Fixed Income"
    if alt_pct:
        exposure += f" - {alt_pct}% Alternative"
    st.markdown(f'<h2 style="font-weight: bold; margin-top: 0.5rem; margin-bottom: 1rem;">{exposure}</h2>', unsafe_allow_html=True)

    st.markdown("Strategic, globally diversified multi-asset portfolios designed to seek long-term capital appreciation. Efficiently covers market exposures through a minimum number of holdings to reduce cost and trading.")
    st.markdown("---")

    # Characteristics
    chars = []
    if strategy_data.get("Strategy Type"):
        chars.append(strategy_data["Strategy Type"].upper())
    if strategy_data.get("Type"):
        chars.append(strategy_data["Type"].upper())
    if strategy_data.get("Tax-Managed"):
        chars.append("TAX-MANAGED")
    if has_private:
        chars.append("PRIVATE MARKETS")

    st.markdown("**Model Characteristics**")
    st.markdown(" | ".join(chars) if chars else "GROWTH | ETF | STRATEGIC")
    st.markdown("---")

    # Stats
    as_of = datetime.now().strftime("%m/%d/%Y")
    st.markdown("**Summary Statistics**")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("WEIGHTED AVG EXPENSE RATIO", f"{strategy_data.get('Expense Ratio', 0.0004):.2%}")
        st.caption(f"as of {as_of}")
    with c2:
        st.metric("3 YEAR RETURN", "X.XX")
        st.caption(f"as of {as_of}")
    with c3:
        y = strategy_data.get("Yield")
        st.metric("12-MONTH YIELD", f"{y:.2f}%" if y else "X.XX")
        st.caption(f"as of {as_of}")
    with c4:
        st.metric("INCEPTION", "X.XX")
        st.caption(f"as of {as_of}")
    with c5:
        st.metric("3 YR STD DEV", "X.XX")
        st.caption(f"as of {as_of}")
    st.markdown("---")

    # Chart
    random.seed(hash(strategy_name))
    vals = [random.uniform(30, 40), random.uniform(20, 30), random.uniform(30, 45), random.uniform(2, 5), random.uniform(0, 1)]
    total = sum(vals)
    vals = [v / total * 100 for v in vals]
    labels = ["U.S. stocks", "Non-U.S. stocks", "Bonds", "Short-term reserves", "Other"]

    st.markdown("**Asset Allocation**")
    
    layout = get_chart_layout(height=400)
    layout["dragmode"] = False
    
    fig = go.Figure(go.Pie(
        labels=labels, values=vals, hole=0.5, marker_colors=CHART_COLORS_PRIMARY,
        textinfo="none", showlegend=False,
        hovertemplate="<b>%{label}</b><br>%{percent:.1%}<extra></extra>",
    ))
    fig.update_layout(**layout)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)
    with col2:
        for lbl, val, clr in zip(labels, vals, CHART_COLORS_PRIMARY):
            st.markdown(f'<div style="display: flex; align-items: center; margin-bottom: 0.5rem;"><span style="width: 12px; height: 12px; background: {clr}; border-radius: 50%; margin-right: 8px; display: inline-block;"></span><span><strong>{lbl}:</strong> {val:.2f}%</span></div>', unsafe_allow_html=True)
        st.caption(f"as of {as_of}")
    st.markdown("---")

    # Factsheet
    st.markdown('<a href="#" style="display: inline-flex; padding: 10px 20px; color: #333; text-decoration: none; border: 1px solid #ddd; border-radius: 5px; font-weight: 500;">📄 Fact sheet</a>', unsafe_allow_html=True)
