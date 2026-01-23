"""Download Parquet files from Azure Blob Storage."""

import logging
import time
from io import BytesIO
from urllib.parse import urlparse

import requests  # type: ignore[import-untyped]
import urllib3  # type: ignore[import-untyped]

# Disable SSL warnings when verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logger
logger = logging.getLogger(__name__)


def download_parquet_from_azure(parquet_url: str) -> tuple[BytesIO, float]:
    """Download Parquet file from Azure Blob Storage and store in memory.
    
    Args:
        parquet_url: Full URL to the Parquet file with SAS token
        
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
    logger.info(f"Downloading parquet file from Azure: {safe_url}")
    
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

