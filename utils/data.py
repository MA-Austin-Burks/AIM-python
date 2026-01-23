"""Data processing utilities for Polars."""

import logging
import os
import re
import time
from io import BytesIO
from urllib.parse import urlparse

import polars as pl
import requests
import streamlit as st
import urllib3

from utils.models import StrategyDetail
from utils.column_names import STRATEGY

# Disable SSL warnings when verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logger
logger = logging.getLogger(__name__)


def download_parquet(parquet_url: str) -> tuple[BytesIO, float]:
    """Download Parquet file from URL and store in memory.
    
    Args:
        parquet_url: Full URL to the Parquet file (may include SAS token or other auth)
        
    Returns:
        tuple: (BytesIO buffer, download_time_in_seconds)
    """
    # Log sanitized URL (without query parameters/tokens) for security
    try:
        parsed = urlparse(parquet_url)
        # Only show scheme, netloc, and path - exclude query and fragment
        safe_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if len(safe_url) > 50:
            safe_url = safe_url[:50] + "..."
    except Exception:
        safe_url = "[URL parsing failed]"
    logger.info(f"Downloading parquet file: {safe_url}")
    
    start_time = time.time()
    response = requests.get(parquet_url, stream=True, verify=False)
    response.raise_for_status()
    
    # Read into memory buffer with optimized chunk size (64KB for better network performance)
    parquet_data = BytesIO()
    for chunk in response.iter_content(chunk_size=65536):  # 64KB chunks
        parquet_data.write(chunk)
    
    parquet_data.seek(0)  # Reset pointer to beginning
    download_time = time.time() - start_time
    
    file_size_mb = len(parquet_data.getvalue()) / (1024 * 1024)
    logger.info(f"Download complete! File size: {file_size_mb:.2f} MB | Time: {download_time:.2f}s")
    
    return parquet_data, download_time


def _is_local_mode() -> bool:
    """Check if running in local mode (using local parquet files).
    
    Checks for USE_LOCAL_DATA environment variable.
    
    Returns:
        bool: True if local mode is enabled
    """
    return os.getenv("USE_LOCAL_DATA", "").lower() in ("true", "1", "yes")


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


def _map_ss_all_to_cleaned_data(ss_all_df: pl.LazyFrame) -> pl.LazyFrame:
    """Load ss_all.parquet and derive target column for calculations.
    
    Keeps all new column names (ss_subtype, ss_suite, ss_type, etc.) and derives
    target column from agg_target / 100 for backward compatibility with calculations.
    
    Args:
        ss_all_df: LazyFrame loaded from ss_all.parquet
        
    Returns:
        LazyFrame with target column derived from agg_target / 100
    """
    return (
        ss_all_df
        .with_columns([
            # Derive target column from agg_target / 100 for calculations
            (pl.col("agg_target") / 100).alias("target"),
        ])
        # Keep all columns - no renaming back to old names
    )


def _derive_strategy_list_from_ss_all(ss_all_df: pl.LazyFrame) -> pl.DataFrame:
    """Derive strategy_list DataFrame from ss_all by aggregating per strategy.
    
    Groups by strategy and aggregates all strategy-level fields.
    Uses new column names matching constants from utils.column_names.
    
    Args:
        ss_all_df: LazyFrame loaded from ss_all.parquet
        
    Returns:
        DataFrame with strategy-level aggregated data using new column names
    """
    from utils.column_names import (
        STRATEGY, EQUITY_PCT, TYPE, TAX_MANAGED, RECOMMENDED,
        PRIVATE_MARKETS, HAS_SMA_MANAGER, MINIMUM, YIELD,
        EXPENSE_RATIO, SERIES, CATEGORY
    )
    
    return (
        ss_all_df
        .group_by(STRATEGY)
        .agg([
            pl.col("equity_allo").first().alias(EQUITY_PCT),  # equity_allo
            pl.col("ss_subtype").first().alias(TYPE),  # ss_subtype -> type
            pl.col("has_tm").first().alias(TAX_MANAGED),  # has_tm
            pl.col("ic_recommend").first().alias(RECOMMENDED),  # ic_recommend
            pl.col("has_private_market").first().alias(PRIVATE_MARKETS),  # has_private_market
            pl.col("has_sma").first().alias(HAS_SMA_MANAGER),  # has_sma
            pl.col(MINIMUM).first().alias(MINIMUM),
            pl.col(YIELD).first().alias(YIELD),
            pl.col("fee").max().alias(EXPENSE_RATIO),  # fee -> expense_ratio
            pl.col("ss_subtype").unique().alias(SERIES),  # ss_subtype -> series (as list)
            pl.col("ss_type").first().alias(CATEGORY),  # ss_type -> category
        ])
        .collect()
    )


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


@st.cache_resource
def load_cleaned_data(parquet_url: str | None = None) -> pl.LazyFrame:
    """Load ss_all.parquet file as a Parquet LazyFrame from local file.
    
    Currently loads only from local file: archive/data/ss_all.parquet
    Azure download functions are kept but not used (for future use).
    
    Uses @st.cache_resource to keep the DataFrame in memory without serialization overhead.
    The download is cached per user session to avoid repeated downloads.
    
    Parquet format provides faster loading and better compression than CSV.
    Derives target column from agg_target / 100 for calculations.
    
    Args:
        parquet_url: Optional URL (not used currently, kept for future Azure support).
    
    Returns:
        pl.LazyFrame: A lazy Polars DataFrame ready for querying with new column names.
    
    Raises:
        FileNotFoundError: If ss_all.parquet file doesn't exist.
    """
    # Load only from local file
    local_path = "archive/data/ss_all.parquet"
    if not os.path.exists(local_path):
        raise FileNotFoundError(
            f"ss_all.parquet not found at: {local_path}"
        )
    
    # Load ss_all.parquet and apply transformations
    ss_all_df = pl.scan_parquet(local_path)
    return _map_ss_all_to_cleaned_data(ss_all_df)


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


@st.cache_data(ttl=3600)
def load_strategy_list(parquet_url: str | None = None) -> pl.DataFrame:
    """Derive strategy_list DataFrame from ss_all.parquet by aggregating per strategy.
    
    Currently loads only from local file: archive/data/ss_all.parquet
    Azure download functions are kept but not used (for future use).
    
    This function aggregates ss_all.parquet to create a strategy-level summary table.
    Use this for card filtering, sorting, and rendering.
    
    Column names use new ss_all column names (no mapping to old names).
    Display names are handled separately at the presentation layer.
    
    Args:
        parquet_url: Optional URL (not used currently, kept for future Azure support).
    
    Returns:
        pl.DataFrame: Strategy-level DataFrame with new column names.
    
    Raises:
        FileNotFoundError: If ss_all.parquet file doesn't exist.
    """
    # Load only from local file
    local_path = "archive/data/ss_all.parquet"
    if not os.path.exists(local_path):
        raise FileNotFoundError(
            f"ss_all.parquet not found at: {local_path}"
        )
    
    # Load ss_all.parquet and derive strategy_list
    ss_all_df = pl.scan_parquet(local_path)
    return _derive_strategy_list_from_ss_all(ss_all_df)


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
        .filter(pl.col(STRATEGY) == strategy_name)
        .head(1)
        .collect()
    )
    
    if strategy_row.height == 0:
        return None
    
    return StrategyDetail.from_row(strategy_row.row(0, named=True))
