import polars as pl
import streamlit as st

from components.branding import PRIMARY, SECONDARY, TERTIARY, hex_to_rgba

CATEGORY_COLORS = {
    "Equity": PRIMARY["raspberry"],
    "Bonds": TERTIARY["azure"],
    "Alternative": SECONDARY["iris"],
    "Cash": TERTIARY["spring"],
}


def _sub_opacity(pct, max_pct):
    return 0.4 + 0.6 * (pct / max_pct)


@st.cache_resource
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
            max_pct = max(subs["allocation_pct"].to_list())
            for row in subs.iter_rows(named=True):
                pct = float(row["allocation_pct"])
                opacity = _sub_opacity(pct, max_pct)
                data.append(
                    {
                        "name": row["subcategory"],
                        "allocation": pct,
                        "market_value": total_assets * pct / 100,
                        "color": hex_to_rgba(color, opacity),
                        "is_category": False,
                    }
                )

    return data


def render_allocation_tab(strategy_name, strategy_data, filters):
    st.segmented_control(
        "Group By",
        options=["Asset Category", "Asset Type", "Asset Class", "Product"],
        default="Product",
        disabled=True,
    )

    total_assets = float(filters["min_strategy"])

    allocation_data = _get_strategy_allocations(strategy_name, total_assets)
    _render_table(allocation_data)


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
