"""Table styling constants and utilities."""

# CSS for allocation table main section
def get_allocation_table_main_css() -> str:
    """Generate CSS for the main allocation table.
    
    Note: Column widths are now handled via Great Tables cols_width() API.
    """
    return f"""
        #allocation-table-main {{ margin: 0 !important; padding: 0 !important; border: none !important; }}
        #allocation-table-main .gt_table {{ width: 100% !important; table-layout: fixed !important; margin: 0 !important; padding: 0 !important; border: none !important; }}
        #allocation-table-main .gt_table table {{ width: 100% !important; table-layout: fixed !important; margin: 0 !important; border-collapse: collapse !important; border: none !important; border-spacing: 0 !important; }}
        #allocation-table-main .gt_table thead {{ border: none !important; }}
        #allocation-table-main .gt_table thead th {{ padding-top: 12px !important; padding-bottom: 12px !important; padding-left: 12px !important; padding-right: 12px !important; border: none !important; border-bottom: none !important; border-top: none !important; border-left: none !important; border-right: none !important; }}
        #allocation-table-main .gt_table tbody {{ border: none !important; }}
        #allocation-table-main .gt_table tbody tr td {{ padding-top: 5px !important; padding-bottom: 5px !important; border: none !important; border-bottom: none !important; border-top: none !important; border-left: none !important; border-right: none !important; }}
        #allocation-table-main .gt_table thead th:first-child {{ padding-top: 8px !important; }}
        #allocation-table-main .gt_table tbody tr:last-child td {{ padding-bottom: 8px !important; }}
        #allocation-table-main .gt_table tbody tr {{ height: auto !important; border: none !important; }}
        #allocation-table-main .gt_table table td, #allocation-table-main .gt_table table th {{ border: none !important; border-width: 0 !important; outline: none !important; }}
        #allocation-table-main .gt_table * {{ border: none !important; border-width: 0 !important; outline: none !important; }}
        #allocation-table-main .gt_table table, #allocation-table-main .gt_table table * {{ border: none !important; border-width: 0 !important; }}
        /* Column widths now handled via Great Tables cols_width() API */
        /* Text alignment handled via Great Tables cols_align() API */
        /* Note: Indentation and spacing handled via Great Tables style.css() API */
    """


# CSS for allocation table summary section
def get_allocation_table_summary_css(summary_metric_col_width: str, equity_col_width: str) -> str:
    """Generate CSS for the summary allocation table."""
    return f"""
        #allocation-table-summary .gt_table {{ width: 100% !important; table-layout: fixed !important; }}
        #allocation-table-summary .gt_table table {{ width: 100% !important; table-layout: fixed !important; border-collapse: collapse !important; }}
        #allocation-table-summary .gt_table thead th {{ padding-top: 12px !important; padding-bottom: 12px !important; border: none !important; border-bottom: none !important; border-top: none !important; }}
        #allocation-table-summary .gt_table tbody tr td {{ padding-top: 7px !important; padding-bottom: 7px !important; border: none !important; border-bottom: none !important; border-top: none !important; }}
        #allocation-table-summary .gt_table tbody tr {{ border: none !important; }}
        #allocation-table-summary .gt_table table td, #allocation-table-summary .gt_table table th {{ border: none !important; }}
        #allocation-table-summary .gt_table thead th:first-child {{ width: {summary_metric_col_width} !important; }}
        #allocation-table-summary .gt_table tbody td:first-child {{ width: {summary_metric_col_width} !important; }}
        #allocation-table-summary .gt_table thead th:not(:first-child) {{ width: {equity_col_width} !important; text-align: center !important; }}
        #allocation-table-summary .gt_table tbody td:not(:first-child) {{ width: {equity_col_width} !important; text-align: center !important; }}
    """
