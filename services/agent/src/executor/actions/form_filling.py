"""Form filling and interaction actions."""

import logging
from typing import List, Optional, Union

from playwright.async_api import Page

from ...utils import retry_on_failure


logger = logging.getLogger(__name__)


@retry_on_failure(max_attempts=3, base_delay=1.0)
async def fill_text_field(
    page: Page, 
    selector: str, 
    value: str,
    clear_first: bool = True,
    timeout: int = 30000
) -> None:
    """Fill a text input field.
    
    Args:
        page: Playwright page object
        selector: CSS selector for the input field
        value: Value to fill
        clear_first: Whether to clear the field first
        timeout: Timeout in milliseconds
    """
    logger.info(f"Filling text field {selector} with value: {value}")
    
    try:
        # Wait for element to be visible
        await page.wait_for_selector(selector, state="visible", timeout=timeout)
        
        # Scroll into view
        await page.locator(selector).scroll_into_view_if_needed()
        
        # Focus the element
        await page.focus(selector)
        
        if clear_first:
            # Clear existing content
            await page.fill(selector, "")
        
        # Type the value
        await page.fill(selector, value)
        
        # Trigger change event
        await page.dispatch_event(selector, "change")
        
        # Wait a bit for any validation
        await page.wait_for_timeout(500)
        
    except Exception as e:
        logger.error(f"Failed to fill text field {selector}: {e}")
        raise


async def fill_text_field_slowly(
    page: Page, 
    selector: str, 
    value: str,
    delay: int = 100,
    timeout: int = 30000
) -> None:
    """Fill text field character by character (useful for avoiding bot detection).
    
    Args:
        page: Playwright page object
        selector: CSS selector for the input field
        value: Value to type
        delay: Delay between keystrokes in milliseconds
        timeout: Timeout in milliseconds
    """
    logger.info(f"Slowly filling text field {selector}")
    
    try:
        await page.wait_for_selector(selector, state="visible", timeout=timeout)
        await page.focus(selector)
        await page.fill(selector, "")  # Clear first
        await page.type(selector, value, delay=delay)
        
    except Exception as e:
        logger.error(f"Failed to slowly fill text field {selector}: {e}")
        raise


@retry_on_failure(max_attempts=3, base_delay=1.0)
async def select_dropdown_option(
    page: Page, 
    selector: str, 
    value: Union[str, int],
    by: str = "value",
    timeout: int = 30000
) -> None:
    """Select an option from a dropdown.
    
    Args:
        page: Playwright page object
        selector: CSS selector for the select element
        value: Value to select
        by: How to select - "value", "label", or "index"
        timeout: Timeout in milliseconds
    """
    logger.info(f"Selecting dropdown option {value} from {selector}")
    
    try:
        await page.wait_for_selector(selector, state="visible", timeout=timeout)
        await page.locator(selector).scroll_into_view_if_needed()
        
        if by == "value":
            await page.select_option(selector, value=str(value))
        elif by == "label":
            await page.select_option(selector, label=str(value))
        elif by == "index":
            await page.select_option(selector, index=int(value))
        else:
            raise ValueError(f"Invalid selection method: {by}")
        
        # Trigger change event
        await page.dispatch_event(selector, "change")
        await page.wait_for_timeout(500)
        
    except Exception as e:
        logger.error(f"Failed to select dropdown option: {e}")
        raise


async def check_checkbox(page: Page, selector: str, timeout: int = 30000) -> None:
    """Check a checkbox.
    
    Args:
        page: Playwright page object
        selector: CSS selector for the checkbox
        timeout: Timeout in milliseconds
    """
    logger.info(f"Checking checkbox: {selector}")
    
    try:
        await page.wait_for_selector(selector, state="visible", timeout=timeout)
        await page.locator(selector).scroll_into_view_if_needed()
        await page.check(selector)
        await page.wait_for_timeout(300)
        
    except Exception as e:
        logger.error(f"Failed to check checkbox {selector}: {e}")
        raise


async def uncheck_checkbox(page: Page, selector: str, timeout: int = 30000) -> None:
    """Uncheck a checkbox.
    
    Args:
        page: Playwright page object
        selector: CSS selector for the checkbox
        timeout: Timeout in milliseconds
    """
    logger.info(f"Unchecking checkbox: {selector}")
    
    try:
        await page.wait_for_selector(selector, state="visible", timeout=timeout)
        await page.locator(selector).scroll_into_view_if_needed()
        await page.uncheck(selector)
        await page.wait_for_timeout(300)
        
    except Exception as e:
        logger.error(f"Failed to uncheck checkbox {selector}: {e}")
        raise


async def select_radio_button(page: Page, selector: str, timeout: int = 30000) -> None:
    """Select a radio button.
    
    Args:
        page: Playwright page object
        selector: CSS selector for the radio button
        timeout: Timeout in milliseconds
    """
    logger.info(f"Selecting radio button: {selector}")
    
    try:
        await page.wait_for_selector(selector, state="visible", timeout=timeout)
        await page.locator(selector).scroll_into_view_if_needed()
        await page.check(selector)
        await page.wait_for_timeout(300)
        
    except Exception as e:
        logger.error(f"Failed to select radio button {selector}: {e}")
        raise


@retry_on_failure(max_attempts=2, base_delay=1.0)
async def upload_file(
    page: Page, 
    selector: str, 
    file_path: str,
    timeout: int = 30000
) -> None:
    """Upload a file through a file input.
    
    Args:
        page: Playwright page object
        selector: CSS selector for the file input
        file_path: Path to the file to upload
        timeout: Timeout in milliseconds
    """
    logger.info(f"Uploading file {file_path} to {selector}")
    
    try:
        await page.wait_for_selector(selector, state="attached", timeout=timeout)
        await page.set_input_files(selector, file_path)
        await page.wait_for_timeout(1000)  # Wait for upload to process
        
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise


async def submit_form(page: Page, form_selector: str = "form", timeout: int = 30000) -> None:
    """Submit a form.
    
    Args:
        page: Playwright page object
        form_selector: CSS selector for the form
        timeout: Timeout in milliseconds
    """
    logger.info(f"Submitting form: {form_selector}")
    
    try:
        await page.wait_for_selector(form_selector, state="visible", timeout=timeout)
        
        # Try to find submit button within the form
        submit_selectors = [
            f"{form_selector} input[type='submit']",
            f"{form_selector} button[type='submit']", 
            f"{form_selector} button:has-text('Submit')",
            f"{form_selector} button:has-text('Enviar')",
            f"{form_selector} .btn-submit"
        ]
        
        for submit_selector in submit_selectors:
            try:
                await page.click(submit_selector, timeout=5000)
                await page.wait_for_timeout(1000)
                return
            except:
                continue
        
        # If no submit button found, try pressing Enter on the form
        await page.press(form_selector, "Enter")
        await page.wait_for_timeout(1000)
        
    except Exception as e:
        logger.error(f"Failed to submit form: {e}")
        raise


async def clear_field(page: Page, selector: str, timeout: int = 30000) -> None:
    """Clear a form field.
    
    Args:
        page: Playwright page object
        selector: CSS selector for the field
        timeout: Timeout in milliseconds
    """
    logger.info(f"Clearing field: {selector}")
    
    try:
        await page.wait_for_selector(selector, state="visible", timeout=timeout)
        await page.focus(selector)
        await page.fill(selector, "")
        
    except Exception as e:
        logger.error(f"Failed to clear field {selector}: {e}")
        raise


async def get_field_value(page: Page, selector: str) -> Optional[str]:
    """Get the value of a form field.
    
    Args:
        page: Playwright page object
        selector: CSS selector for the field
        
    Returns:
        Field value or None if not found
    """
    try:
        element = await page.query_selector(selector)
        if element:
            return await element.input_value()
        return None
    except Exception as e:
        logger.error(f"Failed to get field value for {selector}: {e}")
        return None


async def is_field_required(page: Page, selector: str) -> bool:
    """Check if a field is required.
    
    Args:
        page: Playwright page object
        selector: CSS selector for the field
        
    Returns:
        True if field is required
    """
    try:
        element = await page.query_selector(selector)
        if element:
            required = await element.get_attribute("required")
            return required is not None
        return False
    except Exception as e:
        logger.error(f"Failed to check if field is required: {e}")
        return False


async def validate_field(page: Page, selector: str) -> bool:
    """Validate a form field (check for validation errors).
    
    Args:
        page: Playwright page object
        selector: CSS selector for the field
        
    Returns:
        True if field is valid
    """
    try:
        # Check for HTML5 validation
        is_valid = await page.evaluate("""
            (selector) => {
                const element = document.querySelector(selector);
                return element ? element.validity.valid : true;
            }
        """, selector)
        
        return is_valid
    except Exception as e:
        logger.error(f"Failed to validate field {selector}: {e}")
        return True  # Assume valid if we can't check