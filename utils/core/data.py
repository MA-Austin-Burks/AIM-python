"""Data processing utilities for Polars."""

import os
import re

import polars as pl
import streamlit as st

from utils.core.models import StrategyDetail
from utils.core.performance import track_performance

from utils.download_parquet_from_azure import download_parquet_from_azure


def _is_local_mode() -> bool:
    """Check if running in local mode (using local parquet files).
    
    Checks for USE_LOCAL_DATA environment variable.
    
    Returns:
        bool: True if local mode is enabled
    """
    return os.getenv("USE_LOCAL_DATA", "").lower() in ("true", "1", "yes")


@track_performance
@st.cache_data(ttl=3600)
def _load_model_agg_sort_order() -> dict[str, int]:
    """Load model aggregate sort order from CSV (cached for 1 hour).
    
    Returns:
        Dictionary mapping model aggregate names to sort order integers
    """
    model_agg_sort_df: pl.DataFrame = pl.read_csv("pages/search/data/model_agg_sort_order.csv")
    return dict(
        zip(model_agg_sort_df["ModelAggregate"].to_list(), model_agg_sort_df["SortOrder"].to_list())
    )


MODEL_AGG_SORT_DEFAULT: int = 99


def hash_lazyframe(lf: pl.LazyFrame) -> str:
    """Create a stable hash for a LazyFrame based on its schema.
    
    Note: This only checks schema, not data content. For content-aware caching,
    consider adding file modification time or content hash to cache keys.
    
    Uses collect_schema() to avoid performance warnings about schema resolution.
    """
    return str(sorted(lf.collect_schema().items()))


@track_performance
@st.cache_data(ttl=3600)
def get_model_agg_sort_order(model_agg: str | None) -> int:
    """Get sort order for model aggregate based on name patterns.
    
    Matches the ordering logic from the R spreadsheet creation tool.
    Lower numbers appear first in the table.
    
    Uses substring matching: checks if each pattern appears anywhere in the
    model aggregate name (case-insensitive). Prefers longer/more specific patterns
    to avoid substring issues (e.g., "ALL CAP" matching in "SMALL CAP").
    
    Cached to avoid repeated regex operations on the same model aggregate names.
    
    Args:
        model_agg: Model aggregate name (can be None)
    
    Returns:
        Sort order integer (lower = appears first)
    """
    if model_agg is None:
        return MODEL_AGG_SORT_DEFAULT
    
    # Load sort order dictionary (cached)
    model_agg_sort_order: dict[str, int] = _load_model_agg_sort_order()
    
    model_agg_upper = str(model_agg).upper()
    
    # Check each pattern in sort order dictionary
    # Use word boundary matching to ensure whole words/phrases are matched
    # (e.g., "ALL CAP" should NOT match inside "SMALL CAP")
    best_match = MODEL_AGG_SORT_DEFAULT
    best_pattern_length = 0
    
    # Sort patterns by length (longest first) to check more specific patterns first
    # This ensures "SMALL CAP" is checked before "ALL CAP"
    sorted_patterns: list[tuple[str, int]] = sorted(model_agg_sort_order.items(), key=lambda x: len(x[0]), reverse=True)
    
    for pattern, sort_order in sorted_patterns:
        # Escape special regex characters in the pattern
        pattern_escaped = re.escape(pattern)
        # Use word boundaries to match whole words/phrases
        # \b matches word boundaries, but we also want to match multi-word phrases
        # So we'll use a pattern that matches the phrase as a whole unit
        pattern_regex = r'\b' + pattern_escaped + r'\b'
        
        if re.search(pattern_regex, model_agg_upper):
            pattern_length = len(pattern)
            # Always prefer longer (more specific) patterns
            # Only update if this pattern is longer, or same length with lower sort order
            if pattern_length > best_pattern_length:
                best_match = sort_order
                best_pattern_length = pattern_length
            elif pattern_length == best_pattern_length and sort_order < best_match:
                # Same length, prefer lower sort order
                best_match = sort_order
    
    return best_match


def _get_cleaned_data_url() -> str:
    """Get the cleaned-data parquet URL from Streamlit secrets or environment variable.
    
    Checks Streamlit secrets first (for Streamlit Cloud), then falls back to
    environment variables (for Azure deployments).
    
    Returns:
        str: The Azure Blob Storage URL for cleaned-data.parquet
    
    Raises:
        ValueError: If URL is not found in secrets or environment variable
    """
    import os
    
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        if hasattr(st, 'secrets'):
            # Try attribute access first (st.secrets.CLEANED_DATA_PARQUET_URL)
            url = getattr(st.secrets, 'CLEANED_DATA_PARQUET_URL', None)
            # If not found, try dict-style access (st.secrets['CLEANED_DATA_PARQUET_URL'])
            if url is None:
                url = st.secrets.get('CLEANED_DATA_PARQUET_URL', None) if hasattr(st.secrets, 'get') else None
            if url:
                return str(url).strip().strip('"').strip("'")
    except (AttributeError, KeyError, FileNotFoundError, TypeError):
        # Secrets not available, fall back to environment variable
        pass
    
    # Fall back to environment variable (for Azure deployments)
    env_url = os.getenv('CLEANED_DATA_PARQUET_URL')
    if env_url:
        return env_url.strip().strip('"').strip("'")
    
    raise ValueError(
        "Azure Blob Storage URL not found. "
        "Please set CLEANED_DATA_PARQUET_URL in Streamlit secrets or environment variable."
    )


@track_performance
@st.cache_resource
def load_cleaned_data(parquet_url: str | None = None) -> pl.LazyFrame:
    """Load the full cleaned-data file as a Parquet LazyFrame from Azure Blob Storage or local file.
    
    Downloads Parquet file from Azure Blob Storage and loads into Polars as a LazyFrame.
    Uses @st.cache_resource to keep the DataFrame in memory without serialization overhead.
    The download is cached per user session to avoid repeated downloads.
    
    If USE_LOCAL_DATA environment variable is set or --local flag is used, loads from
    local file: utils/archive/data/cleaned-data.parquet
    
    Parquet format provides faster loading and better compression than CSV.
    Schema is preserved from the original conversion, ensuring type consistency.
    
    Args:
        parquet_url: Optional URL to override the default Azure Blob Storage URL.
                     If None, reads from Streamlit secrets or environment variable.
                     Ignored if local mode is enabled.
    
    Returns:
        pl.LazyFrame: A lazy Polars DataFrame ready for querying.
    
    Raises:
        RuntimeError: If there's an error downloading or reading the Parquet file.
        FileNotFoundError: If local mode is enabled but file doesn't exist.
    """
    # Check for local mode first
    if _is_local_mode():
        local_path = "utils/archive/data/cleaned-data.parquet"
        if os.path.exists(local_path):
            return pl.scan_parquet(local_path)
        
        raise FileNotFoundError(
            f"Local mode enabled but cleaned-data.parquet not found at: {local_path}"
        )
    
    # Use provided URL or get from secrets/environment
    url = (parquet_url or _get_cleaned_data_url()).strip().strip('"').strip("'")
    
    # Check if URL is a remote HTTP/HTTPS URL vs local file path
    is_remote_url = url.lower().startswith(("http://", "https://"))
    
    # Check if URL is a local file path (for backward compatibility)
    if not is_remote_url:
        # Local file path - check if it exists
        parquet_path = url.replace(".csv", ".parquet")
        csv_path = url.replace(".parquet", ".csv")
        
        if os.path.exists(parquet_path):
            return pl.scan_parquet(parquet_path)
        elif os.path.exists(csv_path):
            # Fallback to CSV for backward compatibility
            return pl.scan_csv(
                csv_path,
                null_values=["NA", "#VALUE!"],
                infer_schema_length=10000,
            )
        else:
            raise FileNotFoundError(f"Neither {parquet_path} nor {csv_path} found")
    
    # Download from Azure Blob Storage
    parquet_buffer, _ = download_parquet_from_azure(url)
    
    # Optimize: Use scan_parquet for true lazy evaluation
    # Write to temp file since scan_parquet requires a file path
    # The file persists during the session since load_cleaned_data is cached
    import tempfile
    import atexit
    
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as tmp_file:
            tmp_file.write(parquet_buffer.getvalue())
            tmp_path = tmp_file.name
        
        # Register cleanup function to ensure temp file is deleted on exit
        def cleanup_temp_file():
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
        
        atexit.register(cleanup_temp_file)
        
        # Use scan_parquet for true lazy evaluation (doesn't load entire file into memory)
        return pl.scan_parquet(tmp_path)
    except Exception:
        # Ensure cleanup on error
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        raise


def _get_strategy_list_url() -> str | None:
    """Get the strategy_list parquet URL from Streamlit secrets or environment variable.
    
    Checks Streamlit secrets first (for Streamlit Cloud), then falls back to
    environment variables (for Azure deployments).
    
    Returns:
        str | None: The Azure Blob Storage URL for strategy_list.parquet, or None if not set
    """
    import os
    
    # Try Streamlit secrets first (for Streamlit Cloud)
    url = None
    try:
        if hasattr(st, 'secrets') and st.secrets is not None:
            # Try attribute access first (st.secrets.STRATEGY_LIST_PARQUET)
            try:
                url = getattr(st.secrets, 'STRATEGY_LIST_PARQUET', None)
            except (AttributeError, TypeError):
                pass
            
            # If not found, try dict-style access (st.secrets['STRATEGY_LIST_PARQUET'])
            if url is None:
                try:
                    if hasattr(st.secrets, 'get'):
                        url = st.secrets.get('STRATEGY_LIST_PARQUET', None)
                    elif hasattr(st.secrets, '__getitem__'):
                        url = st.secrets['STRATEGY_LIST_PARQUET']
                except (KeyError, AttributeError, TypeError):
                    pass
            
            if url:
                return str(url).strip().strip('"').strip("'")
    except Exception:
        # Any error accessing secrets, fall through to environment variable
        pass
    
    # Fall back to environment variable (for Azure deployments)
    env_url = os.getenv('STRATEGY_LIST_PARQUET')
    if env_url:
        return str(env_url).strip().strip('"').strip("'")
    
    return None


@track_performance
@st.cache_data(ttl=3600)
def load_strategy_list(parquet_url: str | None = None) -> pl.DataFrame:
    """Load the pre-generated strategy_list.parquet file from Azure Blob Storage or local file.
    
    This file contains a summary table for all strategies, pre-aggregated from cleaned-data.
    Use this for card filtering, sorting, and rendering instead of calling get_strategy_table().
    
    If USE_LOCAL_DATA environment variable is set or --local flag is used, loads from
    local file: utils/archive/data/strategy_list.parquet or data/strategy_list.parquet
    
    Args:
        parquet_url: Optional URL to override the default Azure Blob Storage URL.
                     If None, reads from Streamlit secrets or environment variable.
                     Ignored if local mode is enabled.
    
    Returns:
        pl.DataFrame: Strategy-level DataFrame with columns matching get_strategy_table() output.
    
    Raises:
        ValueError: If URL is not found in secrets or environment variable (when not in local mode)
        FileNotFoundError: If local mode is enabled but file doesn't exist
        RuntimeError: If there's an error downloading or reading the Parquet file
    """
    import tempfile
    
    # Check for local mode first
    if _is_local_mode():
        local_path = "utils/archive/data/strategy_list.parquet"
        if os.path.exists(local_path):
            return pl.read_parquet(local_path)
        
        raise FileNotFoundError(
            f"Local mode enabled but strategy_list.parquet not found at: {local_path}"
        )
    
    # Use provided URL or get from secrets/environment
    url = parquet_url or _get_strategy_list_url()
    
    if not url:
        # Provide helpful debug information
        env_check = os.getenv('STRATEGY_LIST_PARQUET')
        secrets_check = None
        try:
            if hasattr(st, 'secrets') and st.secrets is not None:
                secrets_check = getattr(st.secrets, 'STRATEGY_LIST_PARQUET', None) or (
                    st.secrets.get('STRATEGY_LIST_PARQUET', None) if hasattr(st.secrets, 'get') else None
                )
        except Exception:
            pass
        
        error_msg = (
            "Azure Blob Storage URL not found. "
            "Please set STRATEGY_LIST_PARQUET in Streamlit secrets or environment variable.\n"
            f"Environment variable check: {'Set' if env_check else 'Not set'}\n"
            f"Secrets check: {'Set' if secrets_check else 'Not set'}"
        )
        raise ValueError(error_msg)
    
    url = url.strip().strip('"').strip("'")
    
    # Check if URL is a remote HTTP/HTTPS URL
    is_remote_url = url.lower().startswith(("http://", "https://"))
    
    if not is_remote_url:
        raise ValueError(
            f"Invalid URL format: {url}. "
            "STRATEGY_LIST_PARQUET must be a valid HTTP/HTTPS URL to Azure Blob Storage."
        )
    
    # Download from Azure Blob Storage
    parquet_buffer, _ = download_parquet_from_azure(url)
    
    # Write to temp file and read as DataFrame (not LazyFrame since it's small)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as tmp_file:
            tmp_file.write(parquet_buffer.getvalue())
            tmp_path = tmp_file.name
        
        return pl.read_parquet(tmp_path)
    finally:
        # Always clean up temp file, even on error
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                # Log error but don't fail - temp file will be cleaned up by OS eventually
                pass


@track_performance
@st.cache_data(ttl=3600, hash_funcs={pl.LazyFrame: hash_lazyframe})
def get_strategy_by_name(
    cleaned_data: pl.LazyFrame,
    strategy_name: str,
    cache_version: int = 1,
) -> StrategyDetail | None:
    """Get a strategy row as a dataclass by name (cached).
    
    Returns the full strategy row as a StrategyDetail for use in allocation tabs.
    Optimized to use head(1) instead of first() for better performance.
    
    Args:
        cleaned_data: The full cleaned data LazyFrame
        strategy_name: Name of the strategy
    
    Returns:
        StrategyDetail with core fields, or None if not found
    """
    strategy_row = (
        cleaned_data
        .filter(pl.col("strategy") == strategy_name)
        .head(1)
        .collect()
    )
    
    if strategy_row.height == 0:
        return None
    
    return StrategyDetail.from_row(strategy_row.row(0, named=True))


