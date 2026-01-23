import json
from datetime import datetime

import streamlit as st

from utils.core.performance import get_performance_tracker


def _format_duration_ms(duration_ms: float) -> str:
    """Format duration in milliseconds to a human-readable string."""
    if duration_ms < 1:
        return f"{duration_ms * 1000:.2f} μs"
    elif duration_ms < 1000:
        return f"{duration_ms:.2f} ms"
    else:
        return f"{duration_ms / 1000:.2f} s"


def _render_performance_details() -> None:
    """Render performance tracking details in an expander."""
    tracker = get_performance_tracker()
    
    with st.expander("🔍 Performance Details", expanded=False):
        # Summary section
        summary = tracker.get_summary()
        
        st.markdown("### Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Events", summary["total_events"])
        with col2:
            st.metric("Function Calls", summary["function_calls"])
        with col3:
            st.metric("Errors", summary["errors"], delta=None)
        with col4:
            st.metric(
                "Session Duration",
                _format_duration_ms(summary["session_duration_ms"])
            )
        
        if summary["function_calls"] > 0:
            st.metric(
                "Avg Function Duration",
                _format_duration_ms(summary["average_function_duration_ms"])
            )
        
        st.markdown("---")
        
        # Controls
        col_enable, col_clear, col_export = st.columns(3)
        with col_enable:
            enabled = st.toggle(
                "Enable Tracking",
                value=tracker.is_enabled(),
                key="perf_tracking_enabled",
            )
            if enabled != tracker.is_enabled():
                if enabled:
                    tracker.enable()
                else:
                    tracker.disable()
        
        with col_clear:
            if st.button("Clear Logs", key="perf_clear_logs"):
                tracker.clear_logs()
                tracker.start_session()
                st.rerun()
        
        with col_export:
            logs = tracker.get_logs()
            if logs:
                json_logs = json.dumps(logs, indent=2, default=str)
                st.download_button(
                    "Export Logs (JSON)",
                    json_logs,
                    file_name=f"performance_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="perf_export_logs",
                )
        
        st.markdown("---")
        
        # Detailed logs
        st.markdown("### Detailed Logs")
        logs = tracker.get_logs()
        
        if not logs:
            st.info("No performance logs available. Enable tracking to start logging.")
            return
        
        # Filter options
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            event_types = list(set(log["event_type"] for log in logs))
            selected_types = st.multiselect(
                "Filter by Event Type",
                options=event_types,
                default=event_types,
                key="perf_filter_types",
            )
        
        with filter_col2:
            search_term = st.text_input(
                "Search Logs",
                placeholder="Search by function name, message, etc.",
                key="perf_search_logs",
            )
        
        # Filter logs
        filtered_logs = logs
        if selected_types:
            filtered_logs = [log for log in filtered_logs if log["event_type"] in selected_types]
        if search_term:
            search_lower = search_term.lower()
            filtered_logs = [
                log
                for log in filtered_logs
                if search_lower in str(log.get("message", "")).lower()
                or search_lower in str(log.get("metadata", {})).lower()
            ]
        
        if not filtered_logs:
            st.info("No logs match the selected filters.")
            return
        
        # Display logs in a scrollable container
        st.markdown(f"**Showing {len(filtered_logs)} of {len(logs)} logs**")
        
        for idx, log in enumerate(filtered_logs):
            with st.container():
                # Event type badge
                event_type = log["event_type"]
                color_map = {
                    "FUNCTION_CALL": "🟢",
                    "FUNCTION_ERROR": "🔴",
                    "STEP": "🔵",
                    "PROCESS": "🟡",
                    "DATA_OPERATION": "🟣",
                    "SESSION_START": "⚪",
                }
                icon = color_map.get(event_type, "⚪")
                
                # Header with timestamp and event type
                timestamp = datetime.fromtimestamp(log["timestamp"]).strftime("%H:%M:%S.%f")[:-3]
                elapsed = f" (+{_format_duration_ms(log.get('elapsed_ms', 0))})" if log.get("elapsed_ms") else ""
                
                st.markdown(
                    f"**{icon} {event_type}** - `{timestamp}`{elapsed}"
                )
                
                # Message
                if log.get("message"):
                    st.markdown(f"*{log['message']}*")
                
                # Duration if available
                if log.get("duration_ms"):
                    st.markdown(f"⏱️ Duration: **{_format_duration_ms(log['duration_ms'])}**")
                
                # Metadata
                metadata = log.get("metadata", {})
                if metadata:
                    with st.expander("View Details", expanded=False):
                        # Format metadata nicely
                        if "function" in metadata:
                            st.markdown(f"**Function:** `{metadata['function']}`")
                        if "step" in metadata:
                            st.markdown(f"**Step:** `{metadata['step']}`")
                        if "process" in metadata:
                            st.markdown(f"**Process:** `{metadata['process']}`")
                        if "operation" in metadata:
                            st.markdown(f"**Operation:** `{metadata['operation']}`")
                        if "result_type" in metadata:
                            st.markdown(f"**Result Type:** `{metadata['result_type']}`")
                        if "error" in metadata:
                            st.error(f"**Error:** {metadata['error']}")
                        if "error_traceback" in metadata and metadata["error_traceback"]:
                            with st.expander("View Traceback"):
                                st.code(metadata["error_traceback"], language="python")
                        
                        # Show full metadata as JSON
                        st.markdown("**Full Metadata:**")
                        st.json(metadata)
                
                if idx < len(filtered_logs) - 1:
                    st.markdown("---")


def render_footer() -> None:
    """Render the footer with copyright, bug report link, and performance details."""
    st.markdown("---")
    
    # Performance details expander
    _render_performance_details()
    
    # Copyright footer
    footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
    with footer_col2:
        st.markdown(
            """
            <div style="text-align: center; padding: 0.25rem 0; color: #454759; font-size: 0.875rem;">
                © 2026 Mercer Advisors. All rights reserved. | 
                <a href="mailto:aburks@merceradvisors.com" style="color: #C00686; text-decoration: none;">Report a Bug</a>
            </div>
            """,
            unsafe_allow_html=True
        )
