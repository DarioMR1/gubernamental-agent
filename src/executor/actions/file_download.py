"""File download actions."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List

from playwright.async_api import Page, Download

from ...utils import retry_on_failure, sanitize_filename


logger = logging.getLogger(__name__)


@retry_on_failure(max_attempts=2, base_delay=2.0)
async def download_file(
    page: Page,
    link_selector: str,
    download_path: str,
    timeout: int = 60000
) -> str:
    """Download a file by clicking a download link.
    
    Args:
        page: Playwright page object
        link_selector: CSS selector for the download link
        download_path: Directory to save downloaded files
        timeout: Timeout in milliseconds
        
    Returns:
        Path to downloaded file
    """
    logger.info(f"Downloading file from link: {link_selector}")
    
    download_dir = Path(download_path)
    download_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Set up download promise before clicking
        async with page.expect_download(timeout=timeout) as download_info:
            # Wait for and click the download link
            await page.wait_for_selector(link_selector, state="visible", timeout=timeout)
            await page.click(link_selector)
        
        # Get the download object
        download = await download_info.value
        
        # Generate safe filename
        suggested_filename = download.suggested_filename
        safe_filename = sanitize_filename(suggested_filename) if suggested_filename else "download"
        
        # Save the file
        file_path = download_dir / safe_filename
        await download.save_as(str(file_path))
        
        logger.info(f"File downloaded successfully: {file_path}")
        return str(file_path)
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise


async def wait_for_download(
    page: Page,
    expected_filename: Optional[str] = None,
    timeout: int = 30000
) -> str:
    """Wait for a download to complete.
    
    Args:
        page: Playwright page object
        expected_filename: Expected filename pattern
        timeout: Timeout in milliseconds
        
    Returns:
        Path to downloaded file
    """
    logger.info(f"Waiting for download to complete")
    
    try:
        async with page.expect_download(timeout=timeout) as download_info:
            pass  # Just wait for download to start
        
        download = await download_info.value
        
        # Wait for download to finish
        path = await download.path()
        if path:
            logger.info(f"Download completed: {path}")
            return str(path)
        else:
            raise RuntimeError("Download path not available")
            
    except Exception as e:
        logger.error(f"Failed to wait for download: {e}")
        raise


async def download_file_direct_url(
    page: Page,
    file_url: str,
    download_path: str,
    filename: Optional[str] = None
) -> str:
    """Download file directly from URL.
    
    Args:
        page: Playwright page object
        file_url: Direct URL to file
        download_path: Directory to save file
        filename: Optional custom filename
        
    Returns:
        Path to downloaded file
    """
    logger.info(f"Downloading file from URL: {file_url}")
    
    download_dir = Path(download_path)
    download_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Navigate to the file URL
        response = await page.goto(file_url)
        
        if not response or not response.ok:
            raise RuntimeError(f"Failed to access file URL: {response.status if response else 'No response'}")
        
        # Get content
        content = await response.body()
        
        # Determine filename
        if not filename:
            # Try to get filename from Content-Disposition header
            content_disposition = response.headers.get("content-disposition", "")
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')
            else:
                # Use URL path
                filename = Path(file_url).name or "download"
        
        safe_filename = sanitize_filename(filename)
        file_path = download_dir / safe_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"File downloaded successfully: {file_path}")
        return str(file_path)
        
    except Exception as e:
        logger.error(f"Direct URL download failed: {e}")
        raise


async def check_download_started(page: Page, timeout: int = 5000) -> bool:
    """Check if a download has started.
    
    Args:
        page: Playwright page object
        timeout: Timeout in milliseconds
        
    Returns:
        True if download started
    """
    try:
        async with page.expect_download(timeout=timeout):
            pass
        return True
    except Exception:
        return False


async def get_download_status(download: Download) -> dict:
    """Get download status information.
    
    Args:
        download: Playwright download object
        
    Returns:
        Dictionary with download status
    """
    try:
        failure = download.failure()
        path = await download.path()
        
        return {
            "url": download.url,
            "suggested_filename": download.suggested_filename,
            "path": str(path) if path else None,
            "failed": failure is not None,
            "failure_reason": failure if failure else None
        }
    except Exception as e:
        return {"error": str(e)}


async def download_multiple_files(
    page: Page,
    link_selectors: List[str],
    download_path: str,
    timeout: int = 60000
) -> List[str]:
    """Download multiple files sequentially.
    
    Args:
        page: Playwright page object
        link_selectors: List of CSS selectors for download links
        download_path: Directory to save files
        timeout: Timeout per download in milliseconds
        
    Returns:
        List of paths to downloaded files
    """
    logger.info(f"Downloading {len(link_selectors)} files")
    
    downloaded_files = []
    
    for i, selector in enumerate(link_selectors):
        try:
            logger.info(f"Downloading file {i+1}/{len(link_selectors)}")
            file_path = await download_file(page, selector, download_path, timeout)
            downloaded_files.append(file_path)
            
            # Wait between downloads to avoid overwhelming the server
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to download file {i+1}: {e}")
            # Continue with next file instead of failing completely
            continue
    
    logger.info(f"Downloaded {len(downloaded_files)}/{len(link_selectors)} files")
    return downloaded_files


async def verify_download_completed(file_path: str, min_size: int = 0) -> bool:
    """Verify that a download completed successfully.
    
    Args:
        file_path: Path to downloaded file
        min_size: Minimum expected file size in bytes
        
    Returns:
        True if download appears to be complete
    """
    try:
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return False
        
        # Check file size
        size = path.stat().st_size
        if size < min_size:
            return False
        
        # Check if file is still being written (basic check)
        # Wait a bit and see if size changes
        initial_size = size
        await asyncio.sleep(1)
        
        current_size = path.stat().st_size
        if current_size != initial_size:
            return False  # Still being written
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify download: {e}")
        return False


async def cleanup_partial_downloads(download_path: str) -> None:
    """Clean up partial or failed downloads.
    
    Args:
        download_path: Directory containing downloads
    """
    try:
        download_dir = Path(download_path)
        if not download_dir.exists():
            return
        
        # Look for common partial download extensions
        partial_patterns = ["*.part", "*.crdownload", "*.tmp"]
        
        for pattern in partial_patterns:
            for file_path in download_dir.glob(pattern):
                try:
                    file_path.unlink()
                    logger.info(f"Cleaned up partial download: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {file_path}: {e}")
                    
    except Exception as e:
        logger.error(f"Failed to cleanup partial downloads: {e}")