"""Navigation-related Playwright actions."""

import logging
from typing import Optional

from playwright.async_api import Page, ElementHandle

from ...types import ActionResult
from ...utils import retry_on_failure


logger = logging.getLogger(__name__)


@retry_on_failure(max_attempts=2, base_delay=2.0)
async def navigate_to_page(page: Page, url: str) -> None:
    """Navigate to a specific URL.
    
    Args:
        page: Playwright page object
        url: URL to navigate to
    """
    logger.info(f"Navigating to: {url}")
    
    try:
        response = await page.goto(url, wait_until="networkidle", timeout=30000)
        
        if response and not response.ok:
            logger.warning(f"Navigation returned status {response.status}")
        
        # Wait for page to be fully loaded
        await page.wait_for_load_state("domcontentloaded")
        
    except Exception as e:
        logger.error(f"Navigation failed: {e}")
        raise


@retry_on_failure(max_attempts=3, base_delay=1.0)
async def click_element(page: Page, selector: str, timeout: int = 30000) -> None:
    """Click on an element.
    
    Args:
        page: Playwright page object
        selector: CSS selector for the element
        timeout: Timeout in milliseconds
    """
    logger.info(f"Clicking element: {selector}")
    
    try:
        # Wait for element to be visible and clickable
        await page.wait_for_selector(selector, state="visible", timeout=timeout)
        
        # Scroll element into view if needed
        await page.locator(selector).scroll_into_view_if_needed()
        
        # Click the element
        await page.click(selector, timeout=timeout)
        
        # Wait a bit for any actions to process
        await page.wait_for_timeout(500)
        
    except Exception as e:
        logger.error(f"Click failed on {selector}: {e}")
        raise


async def scroll_to_element(page: Page, selector: str) -> None:
    """Scroll to bring an element into view.
    
    Args:
        page: Playwright page object  
        selector: CSS selector for the element
    """
    logger.info(f"Scrolling to element: {selector}")
    
    try:
        element = page.locator(selector)
        await element.scroll_into_view_if_needed()
        
        # Wait a bit for scroll to complete
        await page.wait_for_timeout(500)
        
    except Exception as e:
        logger.error(f"Scroll failed for {selector}: {e}")
        raise


async def wait_for_navigation(
    page: Page, 
    url_pattern: Optional[str] = None,
    timeout: int = 30000
) -> None:
    """Wait for page navigation to complete.
    
    Args:
        page: Playwright page object
        url_pattern: Optional URL pattern to wait for
        timeout: Timeout in milliseconds
    """
    logger.info("Waiting for navigation to complete")
    
    try:
        if url_pattern:
            await page.wait_for_url(url_pattern, timeout=timeout)
        else:
            await page.wait_for_load_state("networkidle", timeout=timeout)
            
    except Exception as e:
        logger.error(f"Navigation wait failed: {e}")
        raise


async def go_back(page: Page) -> None:
    """Navigate back in browser history.
    
    Args:
        page: Playwright page object
    """
    logger.info("Navigating back")
    
    try:
        await page.go_back(wait_until="networkidle")
    except Exception as e:
        logger.error(f"Go back failed: {e}")
        raise


async def go_forward(page: Page) -> None:
    """Navigate forward in browser history.
    
    Args:
        page: Playwright page object
    """
    logger.info("Navigating forward")
    
    try:
        await page.go_forward(wait_until="networkidle")
    except Exception as e:
        logger.error(f"Go forward failed: {e}")
        raise


async def refresh_page(page: Page) -> None:
    """Refresh the current page.
    
    Args:
        page: Playwright page object
    """
    logger.info("Refreshing page")
    
    try:
        await page.reload(wait_until="networkidle")
    except Exception as e:
        logger.error(f"Page refresh failed: {e}")
        raise


async def check_element_exists(page: Page, selector: str, timeout: int = 5000) -> bool:
    """Check if an element exists on the page.
    
    Args:
        page: Playwright page object
        selector: CSS selector for the element
        timeout: Timeout in milliseconds
        
    Returns:
        True if element exists, False otherwise
    """
    try:
        await page.wait_for_selector(selector, state="attached", timeout=timeout)
        return True
    except Exception:
        return False


async def get_element_text(page: Page, selector: str) -> Optional[str]:
    """Get text content of an element.
    
    Args:
        page: Playwright page object
        selector: CSS selector for the element
        
    Returns:
        Element text content or None if not found
    """
    try:
        element = await page.query_selector(selector)
        if element:
            return await element.inner_text()
        return None
    except Exception as e:
        logger.error(f"Failed to get element text for {selector}: {e}")
        return None


async def get_page_title(page: Page) -> str:
    """Get the current page title.
    
    Args:
        page: Playwright page object
        
    Returns:
        Page title
    """
    try:
        return await page.title()
    except Exception as e:
        logger.error(f"Failed to get page title: {e}")
        return ""


async def get_current_url(page: Page) -> str:
    """Get the current page URL.
    
    Args:
        page: Playwright page object
        
    Returns:
        Current URL
    """
    try:
        return page.url
    except Exception as e:
        logger.error(f"Failed to get current URL: {e}")
        return ""