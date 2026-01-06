import polars as pl
import streamlit as st


def render_sidebar(strats):
    schema = strats.collect_schema()

    with st.sidebar:
        st.header("Search")
        selected_strategy_search = st.text_input(
            "Search by Strategy Name",
            value="",
            placeholder="Type to filter by strategy name...",
        )
        st.divider()

        recommended_only = st.toggle(
            "Investment Committee Recommended Only",
            value=True,
            help="Show only recommended strategies when enabled",
        )
        show_recommended = recommended_only
        show_approved = False

        strategy_types: list[str] = ["Risk-Based", "Asset-Class", "Special Situation", "Blended"]
        default_type: str = "Risk-Based"

        selected_types: list[str] = [default_type] if default_type else []
        type_options: list[str] = ([
            "Multifactor Series",
            "Market Series",
            "Income Series",
            "Equity Strategies",
            "Fixed Income Strategies",
            "Cash Strategies",
            "Alternative Strategies",
            "Special Situation Strategies",
            "Blended Strategy",
        ])

        col_min, col_equity = st.columns(2)
        with col_min:
            min_strategy = st.number_input(
                "Account Value ($)",
                min_value=0,
                value=20000,
                step=10000,
                key="min_strategy",
            )
        with col_equity:
            equity_range = st.slider(
                "Equity Allocation Range",
                min_value=0,
                max_value=100,
                value=(0, 100),
                step=10,
                key="equity_range",
            )

        col_tax, col_sma, col_private = st.columns(3)
        with col_tax:
            tax_managed_selection = st.pills(
                "Tax-Managed (TM)",
                options=["Yes", "No"],
                selection_mode="single",
                default=None,
            )
        with col_sma:
            has_sma_manager_selection = st.pills(
                "Has SMA Manager",
                options=["Yes", "No"],
                selection_mode="single",
                default=None,
                disabled="Has SMA Manager" not in schema,
            )
        with col_private:
            private_markets_selection = st.pills(
                "Private Markets",
                options=["Yes", "No"],
                selection_mode="single",
                default=None,
            )

        selected_type = st.pills(
            "Strategy Type",
            options=strategy_types,
            selection_mode="single",
            default=default_type,
        )
        selected_types = [selected_type] if selected_type else []

        selected_subtypes = st.pills(
            "Series",
            options=type_options,
            selection_mode="multi",
            default=["Multifactor Series"]
            if "Multifactor Series" in type_options
            else [],
        )

        selected_managers = st.pills(
            "Manager",
            options=[
                "Mercer Advisors",
                "Blackrock",
                "Nuveen",
                "PIMCO",
                "AQR",
                "Quantinno",
                "SpiderRock",
                "Shelton",
            ],
            selection_mode="multi",
            default=[],
            disabled="Manager" not in schema,
        )

        selected_geography = st.pills(
            "Geography",
            options=[
                "US",
                "International",
                "Global",
                "Emerging Markets",
                "Developed Markets",
            ],
            selection_mode="multi",
            default=[],
            disabled=True,
        )

        col_tracking, col_benchmark = st.columns(2)
        with col_tracking:
            tracking_error = st.selectbox(
                "Tracking Error",
                options=["<1%", "<1.5%", "<2%", "<2.5%", "<3%"],
                index=0,
                disabled=True,
            )
        with col_benchmark:
            reference_benchmark = st.selectbox(
                "Reference Benchmark",
                options=[
                    "S&P 500",
                    "Russell 2000",
                    "Bloomberg Aggregate",
                    "MSCI World",
                    "Barclays Aggregate",
                    "Custom",
                ],
                index=0,
                disabled=True,
            )

        st.divider()
        with st.container(border=True):
            st.markdown("**Abbreviations**")
            st.markdown(
                """
                - **5YTRYSMA** - MA 5 Year Treasury Ladder (SMA)
                - **B5YCRP** - BlackRock Corporate 1-5 Year
                - **MA** - Managed Account
                - **MUSLGMKTLM** - MA Market US Large (SMA Low Min)
                - **N7YMUN** - Nuveen Municipal 1-7 Year
                - **QP** - Quantitative Portfolio
                - **QUSALMKT** - QP Market US All Cap
                - **QUSLGVMQ** - QP Factor US Large Cap VMQ
                - **SMA** - Separately Managed Account
                - **VMQ** - Value, Momentum, Quality
                """
            )

    tax_managed_filter = tax_managed_selection if tax_managed_selection else "All"
    has_sma_manager_filter = has_sma_manager_selection if has_sma_manager_selection else "All"
    private_markets_filter = private_markets_selection if private_markets_selection else "All"

    return {
        "strategy_search": selected_strategy_search or None,
        "selected_managers": selected_managers,
        "min_strategy": min_strategy,
        "tax_managed_filter": tax_managed_filter,
        "has_sma_manager_filter": has_sma_manager_filter,
        "private_markets_filter": private_markets_filter,
        "show_recommended": show_recommended,
        "show_approved": show_approved,
        "selected_types": selected_types,
        "selected_subtypes": selected_subtypes,
        "equity_range": equity_range,
        "selected_geography": selected_geography,
        "tracking_error": tracking_error,
        "reference_benchmark": reference_benchmark,
    }
