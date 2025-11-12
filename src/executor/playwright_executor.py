"""Playwright-based web executor for government portal automation."""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from playwright.async_api import (
    async_playwright, 
    Browser, 
    BrowserContext, 
    Page,
    PlaywrightContextManager,
    ElementHandle,
    Download
)

from ..types import Action, ActionResult, ActionType
from ..config import AgentConfig
from ..utils import retry_on_failure, sanitize_filename
from .actions.navigation import navigate_to_page, click_element, scroll_to_element
from .actions.form_filling import fill_text_field, select_dropdown_option, upload_file
from .actions.file_download import download_file, wait_for_download


logger = logging.getLogger(__name__)


class PlaywrightExecutor:
    """Playwright-based executor for web automation."""
    
    def __init__(self, config: AgentConfig):
        """Initialize Playwright executor.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.playwright: Optional[PlaywrightContextManager] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Setup paths
        self.screenshots_path = Path(config.screenshots_path)
        self.downloads_path = Path(config.downloads_path)
        self.screenshots_path.mkdir(parents=True, exist_ok=True)
        self.downloads_path.mkdir(parents=True, exist_ok=True)
        
        # Track downloads and screenshots
        self.session_downloads: List[str] = []
        self.session_screenshots: List[str] = []
    
    async def start(self) -> None:
        """Start Playwright browser session."""
        logger.info("Starting Playwright browser session")
        
        try:
            self.playwright = async_playwright()
            await self.playwright.start()
            
            # Launch browser
            browser_type = getattr(self.playwright, self.config.playwright.browser_type)
            self.browser = await browser_type.launch(
                headless=self.config.playwright.headless,
                slow_mo=self.config.playwright.slow_mo,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    f'--window-size={self.config.playwright.window_width},{self.config.playwright.window_height}'
                ]
            )
            
            # Create context with download settings
            self.context = await self.browser.new_context(
                viewport={
                    'width': self.config.playwright.window_width,
                    'height': self.config.playwright.window_height
                },
                accept_downloads=True,
                permissions=['downloads'],
                bypass_csp=True
            )
            
            # Set up download handling
            self.context.on("download", self._handle_download)
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set timeouts
            self.page.set_default_timeout(
                self.config.playwright.timeout_seconds * 1000
            )
            self.page.set_default_navigation_timeout(
                self.config.playwright.timeout_seconds * 1000
            )
            
            logger.info("Playwright browser session started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Playwright: {e}")
            await self.cleanup()
            raise
    
    async def stop(self) -> None:
        """Stop Playwright browser session."""
        await self.cleanup()
    
    async def cleanup(self) -> None:
        """Clean up Playwright resources."""
        logger.info("Cleaning up Playwright resources")
        
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    @retry_on_failure(max_attempts=3, base_delay=1.0)
    async def execute_action(self, action: Action) -> ActionResult:
        """Execute a single action.
        
        Args:
            action: Action to execute
            
        Returns:
            Action result
        """
        if not self.page:
            raise RuntimeError("Playwright not started. Call start() first.")
        
        logger.info(f"Executing action: {action.type.value} - {action.id}")
        start_time = time.time()
        screenshot_path = None
        error_message = None
        data_extracted = None
        
        try:
            # Take screenshot before action if configured
            if self.config.monitoring.screenshot_on_action:
                screenshot_path = await self.take_screenshot(
                    f"{action.type.value}_{action.id}_before"
                )
            
            # Execute action based on type
            if action.type == ActionType.NAVIGATE:
                await self._execute_navigate(action)
                
            elif action.type == ActionType.CLICK:
                await self._execute_click(action)
                
            elif action.type == ActionType.FILL_FORM:
                await self._execute_fill_form(action)
                
            elif action.type == ActionType.WAIT:
                await self._execute_wait(action)
                
            elif action.type == ActionType.WAIT_FOR_ELEMENT:
                await self._execute_wait_for_element(action)
                
            elif action.type == ActionType.DOWNLOAD:
                await self._execute_download(action)
                
            elif action.type == ActionType.SCREENSHOT:
                screenshot_path = await self._execute_screenshot(action)
                
            elif action.type == ActionType.EXTRACT_DATA:
                data_extracted = await self._execute_extract_data(action)
                
            elif action.type == ActionType.SCROLL:
                await self._execute_scroll(action)
                
            elif action.type == ActionType.SELECT_DROPDOWN:
                await self._execute_select_dropdown(action)
                
            elif action.type == ActionType.UPLOAD_FILE:
                await self._execute_upload_file(action)
                
            elif action.type == ActionType.AUTHENTICATE:
                await self._execute_authenticate(action)
                
            else:
                raise ValueError(f"Unsupported action type: {action.type}")
            
            # Take screenshot after successful action
            if (self.config.monitoring.screenshot_on_action and 
                action.type != ActionType.SCREENSHOT):
                after_screenshot = await self.take_screenshot(
                    f"{action.type.value}_{action.id}_after"
                )
                if not screenshot_path:
                    screenshot_path = after_screenshot
            
            execution_time = time.time() - start_time
            
            logger.info(f"Action {action.id} completed successfully in {execution_time:.2f}s")
            
            return ActionResult(
                action_id=action.id,
                success=True,
                execution_time=execution_time,
                screenshot_path=screenshot_path,
                data_extracted=data_extracted
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            
            logger.error(f"Action {action.id} failed: {error_message}")
            
            # Take error screenshot
            if self.config.monitoring.screenshot_on_error:
                try:
                    error_screenshot = await self.take_screenshot(
                        f"{action.type.value}_{action.id}_error"
                    )
                    if not screenshot_path:
                        screenshot_path = error_screenshot
                except Exception as screenshot_error:
                    logger.warning(f"Failed to take error screenshot: {screenshot_error}")
            
            return ActionResult(
                action_id=action.id,
                success=False,
                execution_time=execution_time,
                screenshot_path=screenshot_path,
                error_message=error_message
            )
    
    async def take_screenshot(self, filename: str) -> str:
        """Take a screenshot of the current page.
        
        Args:
            filename: Screenshot filename (without extension)
            
        Returns:
            Path to saved screenshot
        """
        if not self.page:
            raise RuntimeError("No page available for screenshot")
        
        # Sanitize filename
        safe_filename = sanitize_filename(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{timestamp}_{safe_filename}.png"
        
        screenshot_path = self.screenshots_path / full_filename
        
        try:
            await self.page.screenshot(
                path=str(screenshot_path),
                full_page=True,
                type="png"
            )
            
            self.session_screenshots.append(str(screenshot_path))
            logger.debug(f"Screenshot saved: {screenshot_path}")
            
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            raise
    
    async def wait_for_element(
        self, 
        selector: str, 
        timeout: int = 30000,
        state: str = "visible"
    ) -> Optional[ElementHandle]:
        """Wait for element to appear.
        
        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
            state: Element state to wait for
            
        Returns:
            Element handle if found
        """
        if not self.page:
            raise RuntimeError("No page available")
        
        try:
            element = await self.page.wait_for_selector(
                selector,
                timeout=timeout,
                state=state
            )
            return element
        except Exception as e:
            logger.warning(f"Element not found: {selector} - {e}")
            return None
    
    async def get_page_info(self) -> Dict[str, Any]:
        """Get current page information.
        
        Returns:
            Dictionary with page information
        """
        if not self.page:
            return {}
        
        try:
            return {
                "url": self.page.url,
                "title": await self.page.title(),
                "viewport": self.page.viewport_size
            }
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            return {"error": str(e)}
    
    def _handle_download(self, download: Download) -> None:
        """Handle download events.
        
        Args:
            download: Playwright download object
        """
        logger.info(f"Download started: {download.suggested_filename}")
        
        # This will be handled by the download action
        # Just log the event for now
    
    async def _execute_navigate(self, action: Action) -> None:
        """Execute navigation action."""
        url = action.parameters.get("url")
        if not url:
            raise ValueError("Navigation action missing URL parameter")
        
        logger.info(f"Navigating to: {url}")
        await navigate_to_page(self.page, url)
        
        # Wait for page load
        await self.page.wait_for_load_state("networkidle", timeout=30000)
    
    async def _execute_click(self, action: Action) -> None:
        """Execute click action."""
        selector = action.parameters.get("selector")
        if not selector:
            raise ValueError("Click action missing selector parameter")
        
        await click_element(self.page, selector)
    
    async def _execute_fill_form(self, action: Action) -> None:
        """Execute form filling action."""
        selector = action.parameters.get("selector")
        value = action.parameters.get("value", "")
        
        if not selector:
            raise ValueError("Fill form action missing selector parameter")
        
        await fill_text_field(self.page, selector, value)
    
    async def _execute_wait(self, action: Action) -> None:
        """Execute wait action."""
        duration = action.parameters.get("duration", 1)
        await asyncio.sleep(duration)
    
    async def _execute_wait_for_element(self, action: Action) -> None:
        """Execute wait for element action."""
        selector = action.parameters.get("selector")
        timeout = action.parameters.get("timeout", 30) * 1000  # Convert to ms
        
        if not selector:
            raise ValueError("Wait for element action missing selector parameter")
        
        await self.wait_for_element(selector, timeout)
    
    async def _execute_download(self, action: Action) -> None:
        """Execute download action."""
        await download_file(
            self.page,
            action.parameters.get("link_selector", ""),
            str(self.downloads_path)
        )
    
    async def _execute_screenshot(self, action: Action) -> str:
        """Execute screenshot action."""
        filename = action.parameters.get("filename", "screenshot")
        return await self.take_screenshot(filename)
    
    async def _execute_extract_data(self, action: Action) -> Dict[str, Any]:
        """Execute data extraction action."""
        selector = action.parameters.get("selector", "body")
        
        try:
            # Extract text content
            element = await self.page.query_selector(selector)
            if element:
                text = await element.inner_text()
                return {"extracted_text": text.strip()}
            else:
                return {"error": f"Element not found: {selector}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _execute_scroll(self, action: Action) -> None:
        """Execute scroll action."""
        selector = action.parameters.get("selector")
        if selector:
            await scroll_to_element(self.page, selector)
        else:
            # Scroll to bottom of page
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    
    async def _execute_select_dropdown(self, action: Action) -> None:
        """Execute dropdown selection action."""
        selector = action.parameters.get("selector")
        value = action.parameters.get("value", "")
        
        if not selector:
            raise ValueError("Select dropdown action missing selector parameter")
        
        await select_dropdown_option(self.page, selector, value)
    
    async def _execute_upload_file(self, action: Action) -> None:
        """Execute file upload action."""
        selector = action.parameters.get("selector")
        file_path = action.parameters.get("file_path")
        
        if not selector or not file_path:
            raise ValueError("Upload file action missing selector or file_path parameter")
        
        await upload_file(self.page, selector, file_path)
    
    async def _execute_authenticate(self, action: Action) -> None:
        """Execute authentication action."""
        method = action.parameters.get("method", "form")
        
        if method == "form":
            # This is a placeholder for form-based authentication
            # In a real implementation, you would handle credentials securely
            logger.warning("Authentication action requires manual implementation")
            raise NotImplementedError("Form authentication not implemented")
        else:
            raise ValueError(f"Unsupported authentication method: {method}")