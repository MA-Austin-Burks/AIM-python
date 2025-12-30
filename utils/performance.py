"""Performance monitoring utilities for benchmarking Streamlit apps."""

import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable

import streamlit as st


class PerformanceMonitor:
    """Track and display performance metrics for Streamlit operations."""

    def __init__(self):
        """Initialize the performance monitor."""
        if "performance_timings" not in st.session_state:
            st.session_state.performance_timings = {}

    def record_timing(self, operation: str, duration: float) -> None:
        """
        Record a timing measurement.

        Args:
            operation: Name of the operation being timed
            duration: Duration in seconds
        """
        if operation not in st.session_state.performance_timings:
            st.session_state.performance_timings[operation] = []
        st.session_state.performance_timings[operation].append(duration)

    def get_stats(self, operation: str) -> dict[str, float] | None:
        """
        Get statistics for an operation.

        Args:
            operation: Name of the operation

        Returns:
            Dictionary with min, max, mean, and last timing, or None if no data
        """
        if operation not in st.session_state.performance_timings:
            return None

        timings = st.session_state.performance_timings[operation]
        if not timings:
            return None

        return {
            "min": min(timings),
            "max": max(timings),
            "mean": sum(timings) / len(timings),
            "last": timings[-1],
            "count": len(timings),
        }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """
        Get statistics for all operations.

        Returns:
            Dictionary mapping operation names to their statistics
        """
        result: dict[str, dict[str, float]] = {}
        for op in st.session_state.performance_timings.keys():
            stats = self.get_stats(op)
            if stats is not None:
                result[op] = stats
        return result

    def reset(self) -> None:
        """Reset all timing data."""
        st.session_state.performance_timings = {}


@contextmanager
def time_operation(operation_name: str, monitor: PerformanceMonitor | None = None):
    """
    Context manager to time an operation.

    Args:
        operation_name: Name of the operation being timed
        monitor: PerformanceMonitor instance (optional, creates new if None)

    Example:
        >>> monitor = PerformanceMonitor()
        >>> with time_operation("load_data", monitor):
        ...     data = load_data()
    """
    if monitor is None:
        monitor = PerformanceMonitor()

    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        monitor.record_timing(operation_name, duration)


def timed_function(operation_name: str | None = None):
    """
    Decorator to time a function execution.

    Args:
        operation_name: Name for the operation (defaults to function name)

    Example:
        >>> @timed_function("load_csv")
        >>> def load_data():
        ...     return pd.read_csv("data.csv")
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        op_name = operation_name or getattr(func, "__name__", "unknown_function")
        monitor = PerformanceMonitor()

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with time_operation(op_name, monitor):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def render_performance_panel(monitor: PerformanceMonitor | None = None) -> None:
    """
    Render a performance monitoring panel in the sidebar.

    Args:
        monitor: PerformanceMonitor instance (optional, creates new if None)
    """
    if monitor is None:
        monitor = PerformanceMonitor()

    with st.sidebar.expander("⚡ Performance Metrics", expanded=False):
        stats = monitor.get_all_stats()

        if not stats:
            st.info(
                "No performance data collected yet. Interact with the app to see metrics."
            )
            return

        # Sort by mean time (slowest first)
        sorted_ops = sorted(stats.items(), key=lambda x: x[1]["mean"], reverse=True)

        st.caption("Operation timings (seconds)")

        for operation, timing_stats in sorted_ops:
            st.write(f"**{operation}**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Last", f"{timing_stats['last']:.4f}s")
                st.metric("Mean", f"{timing_stats['mean']:.4f}s")
            with col2:
                st.metric("Min", f"{timing_stats['min']:.4f}s")
                st.metric("Max", f"{timing_stats['max']:.4f}s")
            st.caption(f"Runs: {timing_stats['count']}")
            st.divider()

        if st.button("🔄 Reset Metrics", use_container_width=True):
            monitor.reset()
            st.rerun()
