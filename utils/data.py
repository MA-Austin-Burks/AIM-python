"""Data processing utilities for Polars."""

import logging
import re
import time
from typing import Any

import polars as pl
import pyarrow.parquet as pq
import s3fs
import streamlit as st

from utils.models import StrategyDetail

# Set up logger
logger = logging.getLogger(__name__)


@st.cache_data(ttl=3600)
def _get_s3_filesystem() -> s3fs.S3FileSystem:
    """Get S3 filesystem from secrets.toml connections.s3 section (cached).

    Returns:
        s3fs.S3FileSystem: Configured S3 filesystem

    Raises:
        ValueError: If S3 secrets are not configured
    """
    try:
        s3: dict[str, Any] = st.secrets.connections.s3
        logger.info(f"Connecting to S3 (region: {s3.AWS_DEFAULT_REGION})")
        return s3fs.S3FileSystem(
            key=s3.AWS_ACCESS_KEY_ID,
            secret=s3.AWS_SECRET_ACCESS_KEY,
            client_kwargs={"region_name": s3.AWS_DEFAULT_REGION},
            token=None,
        )
    except (AttributeError, KeyError, FileNotFoundError) as e:
        raise ValueError(
            "S3 credentials not found in secrets.toml. "
            "Please configure [connections.s3] section with AWS_ACCESS_KEY_ID, "
            "AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION."
        ) from e


@st.cache_data(ttl=3600)
def read_parquet_from_s3(
    parquet_name: str, bucket: str = "aspen-investing-menu"
) -> pl.LazyFrame:
    """Read a Parquet file from S3 into a Polars LazyFrame (cached for 1 hour).

    Note: This function only executes on cache misses. On cache hits, Streamlit
    returns the cached result without executing this function body.

    Args:
        parquet_name: Name of the parquet file (without .parquet extension)
        bucket: S3 bucket name (default: "aspen-investing-menu")

    Returns:
        pl.LazyFrame: LazyFrame loaded from S3 parquet file

    Raises:
        ValueError: If S3 credentials are not configured
        FileNotFoundError: If parquet file doesn't exist in S3
    """
    path = f"s3://{bucket}/{parquet_name}.parquet"
    logger.info(f"[CACHE MISS] Loading {parquet_name} from S3: {path}")

    start_time = time.time()
    try:
        fs = _get_s3_filesystem()

        with fs.open(path, "rb") as f:
            arrow_table = pq.read_table(f)

        # Convert Arrow to Polars
        result: pl.DataFrame | pl.Series = pl.from_arrow(arrow_table)
        df: pl.DataFrame = (
            result.to_frame() if isinstance(result, pl.Series) else result
        )

        download_time = time.time() - start_time
        file_size_mb = len(df) * len(df.columns) * 8 / (1024 * 1024)  # Rough estimate
        logger.info(
            f"Loaded {parquet_name} from S3: shape={df.shape} | "
            f"Size: ~{file_size_mb:.2f} MB | Time: {download_time:.2f}s"
        )

        return df.lazy()
    except Exception as e:
        logger.error(f"Failed to load {parquet_name} from S3: {e}")
        raise


@st.cache_data(ttl=3600)
def _load_model_agg_sort_order() -> dict[str, int]:
    """Load model aggregate sort order from CSV (cached for 1 hour).

    Returns:
        Dictionary mapping model aggregate names to sort order integers
    """
    model_agg_sort_df: pl.DataFrame = pl.read_csv(
        "app_pages/data/model_agg_sort_order.csv"
    )
    return dict(
        zip(
            model_agg_sort_df["ModelAggregate"].to_list(),
            model_agg_sort_df["SortOrder"].to_list(),
        )
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
    sorted_patterns: list[tuple[str, int]] = sorted(
        model_agg_sort_order.items(), key=lambda x: len(x[0]), reverse=True
    )

    for pattern, sort_order in sorted_patterns:
        # Escape special regex characters in the pattern
        pattern_escaped = re.escape(pattern)
        # Use word boundaries to match whole words/phrases
        # \b matches word boundaries, but we also want to match multi-word phrases
        # So we'll use a pattern that matches the phrase as a whole unit
        pattern_regex = r"\b" + pattern_escaped + r"\b"

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
        ss_all_df.with_columns(
            [
                # Derive target column from agg_target / 100 for calculations
                (pl.col("agg_target") / 100).alias("target"),
            ]
        )
        # Keep all columns - no renaming back to old names
    )


def _derive_strategy_list_from_ss_all(ss_all_df: pl.LazyFrame) -> pl.DataFrame:
    """Derive strategy_list DataFrame from ss_all by aggregating per strategy.

    Groups by strategy and aggregates all strategy-level fields.
    Uses new column names directly as strings.

    Args:
        ss_all_df: LazyFrame loaded from ss_all.parquet

    Returns:
        DataFrame with strategy-level aggregated data using new column names
    """
    return (
        ss_all_df.group_by("strategy")
        .agg(
            [
                pl.col("equity_allo").first().alias("equity_allo"),  # equity_allo
                pl.col("private_allo")
                .first()
                .alias("private_allo"),  # private_allo -> alt_pct
                pl.col("ss_subtype").first().alias("ss_subtype"),  # ss_subtype -> type
                pl.col("has_tm").first().alias("has_tm"),  # has_tm
                pl.col("ic_recommend").first().alias("ic_recommend"),  # ic_recommend
                pl.col("has_private_market")
                .first()
                .alias("has_private_market"),  # has_private_market
                pl.col("has_sma").first().alias("has_sma"),  # has_sma
                pl.col("has_VBI").first().alias("has_VBI"),  # has_VBI
                pl.col("minimum").first().alias("minimum"),
                pl.col("yield").first().alias("yield"),
                pl.col("fee").max().alias("fee"),  # fee -> expense_ratio
                pl.col("ss_subtype")
                .unique()
                .alias("series"),  # ss_subtype -> series (as list)
                pl.col("ss_type").first().alias("ss_type"),  # ss_type -> category
            ]
        )
        .collect()
    )


@st.cache_resource
def load_cleaned_data() -> pl.LazyFrame:
    """Load ss_all.parquet file as a Parquet LazyFrame from S3.

    Uses @st.cache_resource to keep the DataFrame in memory without serialization overhead.
    The download is cached per user session to avoid repeated downloads.

    Parquet format provides faster loading and better compression than CSV.
    Derives target column from agg_target / 100 for calculations.

    Returns:
        pl.LazyFrame: A lazy Polars DataFrame ready for querying with new column names.

    Raises:
        ValueError: If S3 credentials are not configured
        FileNotFoundError: If parquet file doesn't exist in S3
    """
    # Get bucket name from secrets or use default
    bucket = "aspen-investing-menu"
    try:
        s3_config = st.secrets.connections.s3
        if hasattr(s3_config, "BUCKET_NAME"):
            bucket = s3_config.BUCKET_NAME
    except (AttributeError, KeyError):
        pass  # Use default bucket

    logger.info(f"Loading ss_all from S3 bucket: {bucket}")
    ss_all_df = read_parquet_from_s3("ss_all", bucket=bucket)
    return _map_ss_all_to_cleaned_data(ss_all_df)


@st.cache_data(ttl=3600)
def load_cais_data() -> pl.DataFrame:
    """Load and transform CAIS data from CSV file in S3.

    Loads cais_all.csv from S3 and transforms it to match the strategy list DataFrame structure
    for filtering and merging. All CSV fields are preserved, with additional placeholder
    fields added for compatibility with the filtering system.

    Returns:
        pl.DataFrame: CAIS data with all original fields plus filter compatibility fields.
    
    Raises:
        ValueError: If S3 credentials are not configured
        FileNotFoundError: If CSV file doesn't exist in S3
    
    Note:
        This function is cached with @st.cache_data(ttl=3600) for 1 hour.
        The S3 filesystem connection is also cached via _get_s3_filesystem().
        Both the CSV download and transformation are cached together.
    """
    # Get bucket name from secrets or use default
    bucket = "aspen-investing-menu"
    try:
        s3_config = st.secrets.connections.s3
        if hasattr(s3_config, "BUCKET_NAME"):
            bucket = s3_config.BUCKET_NAME
    except (AttributeError, KeyError):
        pass  # Use default bucket
    
    # Read CSV from S3
    path = f"s3://{bucket}/cais_all.csv"
    logger.info(f"[CACHE MISS] Loading cais_all.csv from S3: {path}")
    
    start_time = time.time()
    try:
        # _get_s3_filesystem() is cached, so this won't recreate the connection
        fs = _get_s3_filesystem()
        with fs.open(path, "rb") as f:
            # Read CSV from bytes stream
            cais_df = pl.read_csv(f).rename({"Core/Niche": "core_niche"})
        
        download_time = time.time() - start_time
        logger.info(
            f"Loaded cais_all.csv from S3: shape={cais_df.shape} | "
            f"Time: {download_time:.2f}s"
        )
    except Exception as e:
        logger.error(f"Failed to load cais_all.csv from S3: {e}")
        raise

    # Transform to match strategy list structure for filtering
    # Include all columns that exist in strategy_list so we can merge directly
    return cais_df.with_columns(
        [
            # Filter compatibility fields (matching _derive_strategy_list_from_ss_all columns)
            pl.lit("Asset Class").alias("ss_type"),
            pl.lit("Alternative Strategies").alias("ss_subtype"),
            pl.lit(False).alias("ic_recommend"),
            pl.lit(0.0).alias("equity_allo"),
            pl.lit(100.0).alias("private_allo"),  # Required for strategy_list merge
            pl.lit(0.0).alias("fee"),
            pl.lit(None).alias("yield"),
            pl.lit(False).alias("has_tm"),
            pl.lit(True).alias("has_private_market"),
            pl.lit(False).alias("has_sma"),
            pl.lit(False).alias("has_VBI"),
            pl.lit(["Alternative Strategies"]).alias("series"),
            # Ensure minimum is float
            pl.col("minimum").cast(pl.Float64),
        ]
    )


@st.cache_data(ttl=3600)
def load_strategy_list() -> pl.DataFrame:
    """Derive strategy_list DataFrame from ss_all.parquet by aggregating per strategy.

    Loads ss_all.parquet from S3, then aggregates to create a strategy-level summary table.
    Also merges CAIS data from CSV into the aggregated list.

    This function aggregates ss_all.parquet to create a strategy-level summary table.
    Use this for card filtering, sorting, and rendering.

    Column names use new ss_all column names (no mapping to old names).
    Display names are handled separately at the presentation layer.

    Returns:
        pl.DataFrame: Strategy-level DataFrame with new column names, including CAIS data.

    Raises:
        ValueError: If S3 credentials are not configured
        FileNotFoundError: If parquet file doesn't exist in S3
    """
    # Use load_cleaned_data which loads from S3
    ss_all_df = load_cleaned_data()
    strategy_list = _derive_strategy_list_from_ss_all(ss_all_df)

    # Load CAIS data (already has all required columns defined)
    cais_data = load_cais_data()

    # Get all unique columns from both DataFrames
    strategy_cols = set(strategy_list.columns)
    cais_cols = set(cais_data.columns)
    all_cols = sorted(list(strategy_cols | cais_cols))  # Sort for consistent order

    # Add missing columns to strategy_list (CAIS-specific columns)
    # Need to infer types from cais_data to match schema
    cais_only_cols = cais_cols - strategy_cols
    if cais_only_cols:
        cais_schema = cais_data.schema
        strategy_list = strategy_list.with_columns(
            [pl.lit(None, dtype=cais_schema[col]).alias(col) for col in cais_only_cols]
        )

    # Add missing columns to cais_data (strategy_list columns that don't exist in CAIS)
    # Need to infer types from strategy_list to match schema
    strategy_only_cols = strategy_cols - cais_cols
    if strategy_only_cols:
        strategy_schema = strategy_list.schema
        cais_data = cais_data.with_columns(
            [
                pl.lit(None, dtype=strategy_schema[col]).alias(col)
                for col in strategy_only_cols
            ]
        )

    # Select columns in the same order for both DataFrames before concatenating
    strategy_list = strategy_list.select(all_cols)
    cais_data = cais_data.select(all_cols)

    # Merge CAIS data into strategy list (columns are now aligned and in same order)
    merged_list = pl.concat([strategy_list, cais_data])

    return merged_list


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
        cleaned_data.filter(pl.col("strategy") == strategy_name).head(1).collect()
    )

    if strategy_row.height == 0:
        return None

    return StrategyDetail.from_row(strategy_row.row(0, named=True))
