import random
from datetime import datetime

import streamlit as st

from components.branding import PRIMARY


def _generate_badges(strategy_data):
    badges = []

    if strategy_data.get("Recommended"):
        badges.append(":primary[Recommend]")

    strategy_type = strategy_data.get("Strategy Type")
    if strategy_type:
        badges.append(f":orange-badge[{strategy_type}]")

    strategy_type_field = strategy_data.get("Type")
    if strategy_type_field:
        badges.append(f":blue-badge[{strategy_type_field}]")

    if strategy_data.get("Tax-Managed"):
        badges.append(":green[Tax-Managed]")

    if strategy_data.get("Private Markets"):
        badges.append(":gray[Private Markets]")

    return badges


def _metric_with_date(label, value, as_of=None):
    if as_of is None:
        as_of = datetime.now().strftime("%m-%d-%Y")
    st.metric(label, value)
    st.caption(f"as of {as_of}")


def render_description_tab(strategy_name, strategy_data):
    has_private = strategy_data["Private Markets"]
    alt_pct = 15 if has_private else 0
    equity_pct = strategy_data["Equity %"] - alt_pct
    fixed_pct = 100 - equity_pct - alt_pct

    # Strategy Name
    st.markdown(
        f'<h2 style="color: {PRIMARY["raspberry"]};">{strategy_name}</h1>',
        unsafe_allow_html=True,
    )

    parts = [f"{int(equity_pct)}% Equity", f"{int(fixed_pct)}% Fixed Income"]
    if alt_pct:
        parts.append(f"{alt_pct}% Alternative")
    exposure_display_text = " - ".join(parts)

    # Strategy Exposure
    st.markdown(f"### {exposure_display_text}")

    # Strategy Description
    st.markdown(
        "Strategic, globally diversified multi-asset portfolios designed to seek long-term capital appreciation. Efficiently covers market exposures through a minimum number of holdings to reduce cost and trading."
    )

    # Strategy Badges
    badges = _generate_badges(strategy_data)
    if badges:
        st.markdown(" &nbsp; ".join(badges) + " &nbsp;")

    st.divider()

    # Summary Statistics
    st.markdown("#### Summary Statistics")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        _metric_with_date(
            "WEIGHTED AVG EXP RATIO", f"{strategy_data['Expense Ratio']:.2}"
        )
    with c2:
        y = strategy_data["Yield"]
        _metric_with_date("12-MONTH YIELD", f"{y:.2f}%" if y else "X.XX")
    with c3:
        _metric_with_date("3 YEAR RETURN", f"{random.uniform(10, 15):.2f}%")
    with c4:
        _metric_with_date("INCEPTION", f"{random.uniform(15, 19):.2f}%")
    with c5:
        _metric_with_date("3 YR STD DEV", f"{random.uniform(10, 15):.2f}%")
    st.divider()

    # Factsheet
    st.download_button(
        label="📄 Download Fact Sheet",
        data="Fact sheet content goes here.",
        file_name=f"{strategy_name}_factsheet.pdf",
        mime="application/pdf",
        disabled=True,
    )
