"""Performance testing and profiling utilities for tracking function execution times and logs."""

import functools
import time
import traceback
from contextlib import contextmanager
from typing import Any, Callable

import streamlit as st


class PerformanceTracker:
    """Tracks performance metrics and logs for the application."""
    
    def __init__(self):
        """Initialize the performance tracker."""
        self._logs: list[dict[str, Any]] = []
        self._start_time: float | None = None
        self._enabled: bool = True
    
    def enable(self) -> None:
        """Enable performance tracking."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable performance tracking."""
        self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if performance tracking is enabled."""
        return self._enabled
    
    def start_session(self) -> None:
        """Start tracking a new session."""
        self._start_time = time.time()
        self._logs.clear()
        self._log("SESSION_START", "Performance tracking session started", {})
    
    def _log(
        self,
        event_type: str,
        message: str,
        metadata: dict[str, Any],
        duration_ms: float | None = None,
    ) -> None:
        """Internal method to log an event."""
        if not self._enabled:
            return
        
        log_entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "message": message,
            "metadata": metadata,
            "duration_ms": duration_ms,
        }
        
        if self._start_time:
            log_entry["elapsed_ms"] = (time.time() - self._start_time) * 1000
        
        self._logs.append(log_entry)
    
    def log_function_call(
        self,
        function_name: str,
        args: tuple[Any, ...] | None = None,
        kwargs: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        result: Any = None,
        error: Exception | None = None,
    ) -> None:
        """Log a function call with its parameters and execution time."""
        metadata = {
            "function": function_name,
            "args": str(args) if args else None,
            "kwargs": str(kwargs) if kwargs else None,
            "result_type": type(result).__name__ if result is not None else None,
            "error": str(error) if error else None,
            "error_traceback": traceback.format_exc() if error else None,
        }
        
        event_type = "FUNCTION_ERROR" if error else "FUNCTION_CALL"
        message = f"{function_name}() {'failed' if error else 'completed'}"
        
        self._log(event_type, message, metadata, duration_ms)
    
    def log_step(self, step_name: str, details: dict[str, Any] | None = None) -> None:
        """Log a processing step."""
        metadata = details or {}
        metadata["step"] = step_name
        self._log("STEP", f"Step: {step_name}", metadata)
    
    def log_process(self, process_name: str, details: dict[str, Any] | None = None) -> None:
        """Log a process execution."""
        metadata = details or {}
        metadata["process"] = process_name
        self._log("PROCESS", f"Process: {process_name}", metadata)
    
    def log_data_operation(
        self,
        operation: str,
        data_info: dict[str, Any] | None = None,
        duration_ms: float | None = None,
    ) -> None:
        """Log a data operation (e.g., load, filter, transform)."""
        metadata = data_info or {}
        metadata["operation"] = operation
        self._log("DATA_OPERATION", f"Data operation: {operation}", metadata, duration_ms)
    
    def get_logs(self) -> list[dict[str, Any]]:
        """Get all performance logs."""
        return self._logs.copy()
    
    def get_summary(self) -> dict[str, Any]:
        """Get a summary of performance metrics."""
        if not self._logs:
            return {
                "total_events": 0,
                "function_calls": 0,
                "errors": 0,
                "total_duration_ms": 0,
                "session_duration_ms": 0,
            }
        
        function_calls = [log for log in self._logs if log["event_type"] == "FUNCTION_CALL"]
        errors = [log for log in self._logs if log["event_type"] == "FUNCTION_ERROR"]
        
        total_duration = sum(
            log["duration_ms"] for log in self._logs if log["duration_ms"] is not None
        )
        
        session_duration = 0
        if self._start_time:
            session_duration = (time.time() - self._start_time) * 1000
        
        return {
            "total_events": len(self._logs),
            "function_calls": len(function_calls),
            "errors": len(errors),
            "total_duration_ms": total_duration,
            "session_duration_ms": session_duration,
            "average_function_duration_ms": (
                total_duration / len(function_calls) if function_calls else 0
            ),
        }
    
    def clear_logs(self) -> None:
        """Clear all logs."""
        self._logs.clear()
        self._start_time = None


def get_performance_tracker() -> PerformanceTracker:
    """Get or create the performance tracker in session state."""
    if "_performance_tracker" not in st.session_state:
        st.session_state["_performance_tracker"] = PerformanceTracker()
        st.session_state["_performance_tracker"].start_session()
    return st.session_state["_performance_tracker"]


def track_performance(func: Callable) -> Callable:
    """Decorator to track function performance."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracker = get_performance_tracker()
        if not tracker.is_enabled():
            return func(*args, **kwargs)
        
        start_time = time.time()
        error = None
        result = None
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            error = e
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            tracker.log_function_call(
                function_name=func.__name__,
                args=args if len(str(args)) < 200 else None,  # Limit args size
                kwargs=kwargs if len(str(kwargs)) < 200 else None,  # Limit kwargs size
                duration_ms=duration_ms,
                result=result,
                error=error,
            )
    
    return wrapper


@contextmanager
def track_step(step_name: str, details: dict[str, Any] | None = None):
    """Context manager to track a processing step."""
    tracker = get_performance_tracker()
    if not tracker.is_enabled():
        yield
        return
    
    start_time = time.time()
    tracker.log_step(step_name, details)
    
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        tracker.log_step(f"{step_name} (completed)", {**(details or {}), "duration_ms": duration_ms})


@contextmanager
def track_process(process_name: str, details: dict[str, Any] | None = None):
    """Context manager to track a process execution."""
    tracker = get_performance_tracker()
    if not tracker.is_enabled():
        yield
        return
    
    start_time = time.time()
    tracker.log_process(process_name, details)
    
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        tracker.log_process(f"{process_name} (completed)", {**(details or {}), "duration_ms": duration_ms})


@contextmanager
def track_data_operation(operation: str, data_info: dict[str, Any] | None = None):
    """Context manager to track a data operation."""
    tracker = get_performance_tracker()
    if not tracker.is_enabled():
        yield
        return
    
    start_time = time.time()
    
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        tracker.log_data_operation(operation, data_info, duration_ms)
