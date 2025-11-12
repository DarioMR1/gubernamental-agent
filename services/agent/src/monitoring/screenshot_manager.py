"""Screenshot management system for the governmental agent."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont

from ..types import ActionResult
from ..config import AgentConfig
from ..utils import sanitize_filename, format_timestamp


logger = logging.getLogger(__name__)


class Screenshot:
    """Represents a screenshot with metadata."""
    
    def __init__(
        self,
        file_path: str,
        timestamp: datetime,
        action_name: str,
        session_id: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize screenshot object.
        
        Args:
            file_path: Path to screenshot file
            timestamp: When screenshot was taken
            action_name: Name of action when screenshot was taken
            session_id: Session identifier
            description: Optional description
            metadata: Additional metadata
        """
        self.file_path = file_path
        self.timestamp = timestamp
        self.action_name = action_name
        self.session_id = session_id
        self.description = description
        self.metadata = metadata or {}


class ScreenshotManager:
    """Manages screenshot capture and organization."""
    
    def __init__(self, config: AgentConfig):
        """Initialize screenshot manager.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.screenshots_path = Path(config.screenshots_path)
        self.screenshots_path.mkdir(parents=True, exist_ok=True)
        
        # Session-specific screenshot tracking
        self.session_screenshots: Dict[str, List[Screenshot]] = {}
    
    async def capture_on_action(
        self,
        session_id: str,
        action_name: str,
        page_title: str = "",
        page_url: str = "",
        description: str = ""
    ) -> str:
        """Capture screenshot during action execution.
        
        Args:
            session_id: Session identifier
            action_name: Name of action being performed
            page_title: Current page title
            page_url: Current page URL
            description: Optional description
            
        Returns:
            Path to captured screenshot
        """
        try:
            # Generate filename
            timestamp = datetime.now()
            safe_action_name = sanitize_filename(action_name)
            filename = f"{format_timestamp(timestamp, '%Y%m%d_%H%M%S')}_{safe_action_name}.png"
            
            # Create session directory
            session_dir = self.screenshots_path / f"session_{session_id}"
            session_dir.mkdir(exist_ok=True)
            
            screenshot_path = session_dir / filename
            
            # For now, create a placeholder screenshot
            # In a real implementation, this would capture from the browser
            await self._create_placeholder_screenshot(
                str(screenshot_path),
                action_name,
                page_title,
                page_url,
                description
            )
            
            # Create screenshot object
            screenshot = Screenshot(
                file_path=str(screenshot_path),
                timestamp=timestamp,
                action_name=action_name,
                session_id=session_id,
                description=description,
                metadata={
                    "page_title": page_title,
                    "page_url": page_url,
                    "capture_type": "action"
                }
            )
            
            # Track screenshot
            if session_id not in self.session_screenshots:
                self.session_screenshots[session_id] = []
            self.session_screenshots[session_id].append(screenshot)
            
            logger.debug(f"Screenshot captured: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"Failed to capture action screenshot: {e}")
            raise
    
    async def capture_on_error(
        self,
        session_id: str,
        error_context: str,
        error_message: str = "",
        page_title: str = "",
        page_url: str = ""
    ) -> str:
        """Capture screenshot when error occurs.
        
        Args:
            session_id: Session identifier
            error_context: Context where error occurred
            error_message: Error message
            page_title: Current page title
            page_url: Current page URL
            
        Returns:
            Path to captured screenshot
        """
        try:
            # Generate filename
            timestamp = datetime.now()
            safe_context = sanitize_filename(error_context)
            filename = f"{format_timestamp(timestamp, '%Y%m%d_%H%M%S')}_ERROR_{safe_context}.png"
            
            # Create session directory
            session_dir = self.screenshots_path / f"session_{session_id}"
            session_dir.mkdir(exist_ok=True)
            
            screenshot_path = session_dir / filename
            
            # Create error screenshot
            await self._create_error_screenshot(
                str(screenshot_path),
                error_context,
                error_message,
                page_title,
                page_url
            )
            
            # Create screenshot object
            screenshot = Screenshot(
                file_path=str(screenshot_path),
                timestamp=timestamp,
                action_name=f"ERROR_{error_context}",
                session_id=session_id,
                description=f"Error screenshot: {error_message}",
                metadata={
                    "page_title": page_title,
                    "page_url": page_url,
                    "capture_type": "error",
                    "error_message": error_message
                }
            )
            
            # Track screenshot
            if session_id not in self.session_screenshots:
                self.session_screenshots[session_id] = []
            self.session_screenshots[session_id].append(screenshot)
            
            logger.info(f"Error screenshot captured: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"Failed to capture error screenshot: {e}")
            raise
    
    async def create_session_timeline(self, session_id: str) -> List[Screenshot]:
        """Create chronological timeline of session screenshots.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of screenshots in chronological order
        """
        session_screenshots = self.session_screenshots.get(session_id, [])
        
        # Sort by timestamp
        timeline = sorted(session_screenshots, key=lambda s: s.timestamp)
        
        logger.info(f"Created timeline with {len(timeline)} screenshots for session {session_id}")
        return timeline
    
    async def create_session_collage(
        self,
        session_id: str,
        max_images: int = 12,
        image_size: tuple[int, int] = (300, 200)
    ) -> str:
        """Create a collage of session screenshots.
        
        Args:
            session_id: Session identifier
            max_images: Maximum number of images to include
            image_size: Size to resize each image to
            
        Returns:
            Path to created collage image
        """
        try:
            timeline = await self.create_session_timeline(session_id)
            
            if not timeline:
                raise ValueError(f"No screenshots found for session {session_id}")
            
            # Limit number of images
            selected_screenshots = timeline[:max_images]
            
            # Calculate collage dimensions
            cols = min(4, len(selected_screenshots))
            rows = (len(selected_screenshots) + cols - 1) // cols
            
            collage_width = cols * image_size[0]
            collage_height = rows * image_size[1]
            
            # Create collage image
            collage = Image.new('RGB', (collage_width, collage_height), 'white')
            
            for i, screenshot in enumerate(selected_screenshots):
                try:
                    # Load and resize image
                    img = Image.open(screenshot.file_path)
                    img = img.resize(image_size, Image.Resampling.LANCZOS)
                    
                    # Calculate position
                    col = i % cols
                    row = i // cols
                    x = col * image_size[0]
                    y = row * image_size[1]
                    
                    # Paste image
                    collage.paste(img, (x, y))
                    
                except Exception as e:
                    logger.warning(f"Failed to add screenshot to collage: {e}")
                    continue
            
            # Save collage
            session_dir = self.screenshots_path / f"session_{session_id}"
            session_dir.mkdir(exist_ok=True)
            
            collage_path = session_dir / f"session_collage_{session_id}.png"
            collage.save(collage_path)
            
            logger.info(f"Session collage created: {collage_path}")
            return str(collage_path)
            
        except Exception as e:
            logger.error(f"Failed to create session collage: {e}")
            raise
    
    def get_session_screenshots(self, session_id: str) -> List[Screenshot]:
        """Get all screenshots for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of screenshots for the session
        """
        return self.session_screenshots.get(session_id, [])
    
    def get_screenshot_metadata(self, screenshot_path: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific screenshot.
        
        Args:
            screenshot_path: Path to screenshot file
            
        Returns:
            Screenshot metadata or None if not found
        """
        for session_screenshots in self.session_screenshots.values():
            for screenshot in session_screenshots:
                if screenshot.file_path == screenshot_path:
                    return {
                        "timestamp": screenshot.timestamp.isoformat(),
                        "action_name": screenshot.action_name,
                        "session_id": screenshot.session_id,
                        "description": screenshot.description,
                        **screenshot.metadata
                    }
        return None
    
    async def cleanup_session_screenshots(
        self,
        session_id: str,
        keep_timeline: bool = True,
        keep_errors: bool = True
    ) -> None:
        """Clean up screenshots for a session.
        
        Args:
            session_id: Session identifier
            keep_timeline: Whether to keep timeline screenshots
            keep_errors: Whether to keep error screenshots
        """
        try:
            session_screenshots = self.session_screenshots.get(session_id, [])
            
            for screenshot in session_screenshots:
                should_delete = True
                
                if keep_timeline and screenshot.metadata.get("capture_type") == "action":
                    should_delete = False
                
                if keep_errors and screenshot.metadata.get("capture_type") == "error":
                    should_delete = False
                
                if should_delete:
                    try:
                        Path(screenshot.file_path).unlink(missing_ok=True)
                        logger.debug(f"Cleaned up screenshot: {screenshot.file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete screenshot {screenshot.file_path}: {e}")
            
            # Update tracking
            if not (keep_timeline or keep_errors):
                self.session_screenshots.pop(session_id, None)
            
            logger.info(f"Cleaned up screenshots for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup session screenshots: {e}")
    
    async def export_session_screenshots(
        self,
        session_id: str,
        export_format: str = "zip"
    ) -> str:
        """Export all screenshots for a session.
        
        Args:
            session_id: Session identifier
            export_format: Export format ("zip" or "tar")
            
        Returns:
            Path to exported archive
        """
        try:
            session_screenshots = self.session_screenshots.get(session_id, [])
            
            if not session_screenshots:
                raise ValueError(f"No screenshots found for session {session_id}")
            
            # Create export archive
            export_dir = self.screenshots_path / "exports"
            export_dir.mkdir(exist_ok=True)
            
            timestamp = format_timestamp(datetime.now(), "%Y%m%d_%H%M%S")
            archive_name = f"screenshots_{session_id}_{timestamp}"
            
            if export_format == "zip":
                import zipfile
                archive_path = export_dir / f"{archive_name}.zip"
                
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for screenshot in session_screenshots:
                        if Path(screenshot.file_path).exists():
                            arcname = Path(screenshot.file_path).name
                            zipf.write(screenshot.file_path, arcname)
            
            elif export_format == "tar":
                import tarfile
                archive_path = export_dir / f"{archive_name}.tar.gz"
                
                with tarfile.open(archive_path, 'w:gz') as tarf:
                    for screenshot in session_screenshots:
                        if Path(screenshot.file_path).exists():
                            arcname = Path(screenshot.file_path).name
                            tarf.add(screenshot.file_path, arcname=arcname)
            
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            logger.info(f"Screenshots exported to: {archive_path}")
            return str(archive_path)
            
        except Exception as e:
            logger.error(f"Failed to export session screenshots: {e}")
            raise
    
    async def _create_placeholder_screenshot(
        self,
        file_path: str,
        action_name: str,
        page_title: str,
        page_url: str,
        description: str
    ) -> None:
        """Create a placeholder screenshot for testing.
        
        Args:
            file_path: Path to save screenshot
            action_name: Name of action
            page_title: Page title
            page_url: Page URL
            description: Description
        """
        try:
            # Create a simple image with text
            img = Image.new('RGB', (1200, 800), 'lightblue')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font
            try:
                font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
                font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Add text
            y_offset = 50
            draw.text((50, y_offset), f"Action: {action_name}", fill='black', font=font_large)
            y_offset += 50
            
            if page_title:
                draw.text((50, y_offset), f"Page: {page_title}", fill='black', font=font_small)
                y_offset += 30
            
            if page_url:
                draw.text((50, y_offset), f"URL: {page_url[:80]}...", fill='black', font=font_small)
                y_offset += 30
            
            if description:
                draw.text((50, y_offset), f"Description: {description}", fill='black', font=font_small)
                y_offset += 30
            
            draw.text((50, y_offset), f"Timestamp: {datetime.now().isoformat()}", fill='gray', font=font_small)
            
            # Save image
            img.save(file_path)
            
        except Exception as e:
            logger.error(f"Failed to create placeholder screenshot: {e}")
            raise
    
    async def _create_error_screenshot(
        self,
        file_path: str,
        error_context: str,
        error_message: str,
        page_title: str,
        page_url: str
    ) -> None:
        """Create an error screenshot placeholder.
        
        Args:
            file_path: Path to save screenshot
            error_context: Error context
            error_message: Error message
            page_title: Page title
            page_url: Page URL
        """
        try:
            # Create a red-tinted error image
            img = Image.new('RGB', (1200, 800), 'mistyrose')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font
            try:
                font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
                font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Add error text
            y_offset = 50
            draw.text((50, y_offset), "ERROR SCREENSHOT", fill='red', font=font_large)
            y_offset += 60
            
            draw.text((50, y_offset), f"Context: {error_context}", fill='darkred', font=font_small)
            y_offset += 30
            
            if error_message:
                # Wrap long error messages
                max_width = 80
                wrapped_message = error_message[:max_width] + "..." if len(error_message) > max_width else error_message
                draw.text((50, y_offset), f"Error: {wrapped_message}", fill='darkred', font=font_small)
                y_offset += 30
            
            if page_title:
                draw.text((50, y_offset), f"Page: {page_title}", fill='black', font=font_small)
                y_offset += 30
            
            if page_url:
                draw.text((50, y_offset), f"URL: {page_url[:80]}...", fill='black', font=font_small)
                y_offset += 30
            
            draw.text((50, y_offset), f"Timestamp: {datetime.now().isoformat()}", fill='gray', font=font_small)
            
            # Save image
            img.save(file_path)
            
        except Exception as e:
            logger.error(f"Failed to create error screenshot: {e}")
            raise