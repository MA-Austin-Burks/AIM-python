"""Data processing utilities for Polars."""

import re
from typing import Any

import polars as pl
import streamlit as st

from components.constants import MODEL_AGG_SORT_DEFAULT, MODEL_AGG_SORT_ORDER
from utils.download_parquet_from_azure import download_parquet_from_azure


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
    
    model_agg_upper = str(model_agg).upper()
    
    # Check each pattern in sort order dictionary
    # Use word boundary matching to ensure whole words/phrases are matched
    # (e.g., "ALL CAP" should NOT match inside "SMALL CAP")
    best_match = MODEL_AGG_SORT_DEFAULT
    best_pattern_length = 0
    
    # Sort patterns by length (longest first) to check more specific patterns first
    # This ensures "SMALL CAP" is checked before "ALL CAP"
    sorted_patterns = sorted(MODEL_AGG_SORT_ORDER.items(), key=lambda x: len(x[0]), reverse=True)
    
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
    """Get the cleaned-data parquet URL from secrets or environment.
    
    Checks Streamlit secrets first, then falls back to environment variable.
    
    Returns:
        str: The Azure Blob Storage URL for cleaned-data.parquet
    
    Raises:
        ValueError: If neither secrets nor environment variable is available
    """
    # Try Streamlit secrets first (production)
    try:
        return st.secrets['azure_blob_storage']['cleaned_data_parquet_url']
    except (AttributeError, KeyError, TypeError):
        # Secrets not available or key doesn't exist
        pass
    
    # Fallback to environment variable
    import os
    env_url = os.getenv('CLEANED_DATA_PARQUET_URL')
    if env_url:
        return env_url
    
    # No fallback - raise error if neither is available
    raise ValueError(
        "Azure Blob Storage URL not found. "
        "Please set it in .streamlit/secrets.toml under [azure_blob_storage].cleaned_data_parquet_url "
        "or as environment variable CLEANED_DATA_PARQUET_URL"
    )


@st.cache_resource
def load_cleaned_data(parquet_url: str | None = None) -> pl.LazyFrame:
    """Load the full cleaned-data file as a Parquet LazyFrame from Azure Blob Storage.
    
    Downloads Parquet file from Azure Blob Storage and loads into Polars as a LazyFrame.
    Uses @st.cache_resource to keep the DataFrame in memory without serialization overhead.
    The download is cached per user session to avoid repeated downloads.
    
    Parquet format provides faster loading and better compression than CSV.
    Schema is preserved from the original conversion, ensuring type consistency.
    
    Args:
        parquet_url: Optional URL to override the default Azure Blob Storage URL.
                     If None, reads from Streamlit secrets or environment variable.
    
    Returns:
        pl.LazyFrame: A lazy Polars DataFrame ready for querying.
    
    Raises:
        RuntimeError: If there's an error downloading or reading the Parquet file.
    """
    import os
    
    # Use provided URL or get from secrets/environment
    url = (parquet_url or _get_cleaned_data_url()).strip().strip('"').strip("'")
    
    # Debug: print URL info to help diagnose issues
    print(f"DEBUG: URL length={len(url)}, first 10 chars={repr(url[:10])}")
    
    # Check if URL is a remote HTTP/HTTPS URL vs local file path
    is_remote_url = url.lower().startswith(("http://", "https://"))
    print(f"DEBUG: is_remote_url={is_remote_url}")
    
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
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as tmp_file:
        tmp_file.write(parquet_buffer.getvalue())
        tmp_path = tmp_file.name
    
    # Use scan_parquet for true lazy evaluation (doesn't load entire file into memory)
    # File cleanup handled by OS temp directory cleanup (or can be managed in cache clear)
    return pl.scan_parquet(tmp_path)


@st.cache_data(ttl=3600, hash_funcs={pl.LazyFrame: hash_lazyframe})
def get_strategy_by_name(cleaned_data: pl.LazyFrame, strategy_name: str) -> dict[str, Any] | None:
    """Get a strategy row as a dict by name (cached).
    
    Returns the full strategy row as a dict for use in modals and other components.
    Optimized to use head(1) instead of first() for better performance.
    
    Args:
        cleaned_data: The full cleaned data LazyFrame
        strategy_name: Name of the strategy
    
    Returns:
        dict with all strategy fields, or None if not found
    """
    strategy_row = (
        cleaned_data
        .filter(pl.col("strategy") == strategy_name)
        .head(1)
        .collect()
    )
    
    if strategy_row.height == 0:
        return None
    
    return strategy_row.row(0, named=True)


@st.cache_data(ttl=3600, hash_funcs={pl.LazyFrame: hash_lazyframe})
def get_strategy_table(df: pl.LazyFrame) -> pl.DataFrame:
    """Build and cache a strategy-level DataFrame for card filtering, sorting, and rendering.
    
    Pre-aggregated table improves performance for card/table views. Full cleaned_data
    only loaded when viewing allocation details (product-level data).
    
    Maps column names from cleaned-data.csv format to display format and handles
    type conversions (CSV stores booleans as "TRUE"/"FALSE" strings).
    """
    return (
        df.group_by("strategy")
        .first()
        .with_columns([
            # Rename columns
            pl.col("strategy").alias("Strategy"),
            pl.col("portfolio").cast(pl.Float64).alias("Equity %"),  # int → float, nulls preserved
            pl.col("type").alias("Type"),
            pl.col("minimum").cast(pl.Float64).alias("Minimum"),
            pl.col("yield").cast(pl.Float64).alias("Yield"),
            pl.col("fee").cast(pl.Float64).alias("Expense Ratio"),
            pl.col("category").alias("Strategy Type"),
            # CSV stores booleans as strings, convert to boolean type
            (pl.col("tax_managed") == "TRUE").alias("Tax-Managed"),
            pl.when(pl.col("recommended").is_null() | (pl.col("recommended") == ""))
            .then(False)
            .otherwise(pl.col("recommended") == "TRUE")
            .alias("Recommended"),
            (pl.col("private_markets") == "TRUE").alias("Private Markets"),
            (pl.col("is_SMA") == "TRUE").alias("Has SMA Manager"),
            # Series column wrapped in list for multiselect display in table view
            pl.when(pl.col("type").is_not_null())
            .then(pl.concat_list([pl.col("type")]))
            .otherwise(pl.lit([]).cast(pl.List(pl.Utf8)))
            .alias("Series"),
        ])
        .select([
            "Strategy",
            "Equity %",
            "Type",
            "Tax-Managed",
            "Recommended",
            "Minimum",
            "Yield",
            "Expense Ratio",
            "Strategy Type",
            "Private Markets",
            "Has SMA Manager",
            "Series",
        ])
        .collect()
    )
