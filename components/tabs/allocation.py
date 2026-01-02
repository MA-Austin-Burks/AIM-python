import random
from datetime import datetime

import plotly.graph_objects as go
import polars as pl
import streamlit as st

from components.branding import (
    CHART_COLORS_PRIMARY,
    CHART_CONFIG,
    FONTS,
    PRIMARY,
    SECONDARY,
    TERTIARY,
)

CATEGORY_COLORS = {
    "Equity": PRIMARY["raspberry"],
    "Bonds": TERTIARY["azure"],
    "Alternative": SECONDARY["iris"],
    "Cash": TERTIARY["spring"],
    "Other": PRIMARY["charcoal"],
}


@st.cache_data
def _load_allocation_data():
    return pl.read_csv("data/allocations.csv")


def _get_strategy_allocations(strategy_name, total_assets):
    df = _load_allocation_data().filter(pl.col("strategy") == strategy_name)

    data = []
    categories = df.filter(pl.col("subcategory").is_null())["category"].to_list()

    for category in categories:
        cat_row = df.filter(
            (pl.col("category") == category) & (pl.col("subcategory").is_null())
        ).row(0, named=True)

        cat_pct = cat_row["allocation_pct"]
        color = CATEGORY_COLORS[category]

        data.append(
            {
                "name": category,
                "allocation": cat_pct,
                "market_value": total_assets * cat_pct / 100,
                "color": color,
                "is_category": True,
            }
        )

        subs = df.filter(
            (pl.col("category") == category) & (pl.col("subcategory").is_not_null())
        )
        if subs.height > 0:
            for row in subs.iter_rows(named=True):
                pct = float(row["allocation_pct"])
                data.append(
                    {
                        "name": row["subcategory"],
                        "allocation": pct,
                        "market_value": total_assets * pct / 100,
                        "color": color,
                        "is_category": False,
                    }
                )

    return data


def _render_table(data):
    st.markdown(
        """<div style="display: grid; grid-template-columns: 22px 1fr 95px 130px; gap: 6px; padding: 6px 0; border-bottom: 1px solid #ddd; font-weight: 600; color: #666; font-size: 0.82rem;">
            <div></div><div>Asset</div><div style="text-align: right;">Allocation</div><div style="text-align: right;">Market Value</div>
        </div>""",
        unsafe_allow_html=True,
    )

    for item in data:
        is_cat = item["is_category"]
        st.markdown(
            f"""<div style="display: grid; grid-template-columns: 22px 1fr 95px 130px; gap: 6px; padding: 7px 0; border-bottom: 1px solid #eee; background: {"#f8f9fa" if is_cat else "transparent"}; font-weight: {"600" if is_cat else "400"}; font-size: 0.875rem;">
                <div style="display: flex; align-items: center; justify-content: center;"><span style="width: 9px; height: 9px; background: {item["color"]}; border-radius: 50%; display: inline-block;"></span></div>
                <div style="{"" if is_cat else "padding-left: 14px;"}">{item["name"]}</div>
                <div style="text-align: right;">{item["allocation"]:.2f}%</div>
                <div style="text-align: right;">${item["market_value"]:,.2f}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def render_allocation_tab(strategy_name, filters):
    st.segmented_control(
        "Group By",
        options=["Asset Category", "Asset Type", "Asset Class", "Product"],
        default="Product",
        disabled=True,
    )

    colChart, colTable = st.columns([1, 1])

    with colChart:
        st.space("medium")

        # Asset Allocation Chart
        random.seed(hash(strategy_name))
        ranges = [(30, 40), (20, 30), (30, 45), (2, 5), (0, 1)]
        vals = []
        for low, high in ranges:
            vals.append(random.uniform(low, high))
        total = sum(vals)
        vals = [v / total * 100 for v in vals]
        labels = [
            "U.S. stocks",
            "Non-U.S. stocks",
            "Bonds",
            "Short-term reserves",
            "Other",
        ]

        fig = go.Figure(
            go.Pie(
                labels=labels,
                values=vals,
                hole=0.5,
                marker_colors=CHART_COLORS_PRIMARY,
                textinfo="none",
                showlegend=False,
                hovertemplate="<b>%{label}</b><br>%{percent:.1%}<extra></extra>",
            ),
            layout={
                "font": {"family": FONTS["body"], "color": PRIMARY["charcoal"]},
                "height": 500,
                "margin": {"l": 40, "r": 20, "t": 0, "b": 40},
            },
        )
        st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)

        # Legend
        for lbl, val, clr in zip(labels, vals, CHART_COLORS_PRIMARY):
            st.markdown(
                f'<div style="display: flex; align-items: center; margin-bottom: 0.5rem;"><span style="width: 12px; height: 12px; background: {clr}; border-radius: 50%; margin-right: 8px; display: inline-block;"></span><span><strong>{lbl}:</strong> {val:.2f}%</span></div>',
                unsafe_allow_html=True,
            )
        st.caption(f"as of {datetime.now().strftime('%m-%d-%Y')}")

    with colTable:
        allocation_data = _get_strategy_allocations(
            strategy_name, filters["min_strategy"]
        )
        _render_table(allocation_data)
