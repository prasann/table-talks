"""Export manager for auto-exporting large query results."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from .logger import get_logger


class ExportManager:
    """Manages auto-export of large query results to date-based folders."""
    
    def __init__(self, base_path: str = "./exports", auto_export_threshold: int = 100):
        """Initialize export manager.
        
        Args:
            base_path: Base directory for exports
            auto_export_threshold: Line count threshold for auto-export
        """
        self.base_path = Path(base_path)
        self.auto_export_threshold = auto_export_threshold
        self.logger = get_logger("tabletalk.export")
        
        # Ensure base export directory exists
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def should_export(self, result: str) -> bool:
        """Check if result should be auto-exported based on size.
        
        Args:
            result: The query result string
            
        Returns:
            True if result should be exported
        """
        line_count = self._count_content_lines(result)
        return line_count > self.auto_export_threshold
    
    def export_result(self, query: str, result: str) -> Tuple[str, str]:
        """Export query result to file and return file path and summary.
        
        Args:
            query: The original query
            result: The query result
            
        Returns:
            Tuple of (file_path, summary_for_console)
        """
        try:
            # Create file path
            file_path = self._create_file_path(query)
            
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write export file
            content = self._format_export_content(query, result)
            file_path.write_text(content, encoding='utf-8')
            
            # Generate summary
            line_count = self._count_content_lines(result)
            summary = self._generate_summary(result, line_count)
            
            self.logger.info(f"Exported query result to: {file_path}")
            return str(file_path), summary
            
        except Exception as e:
            self.logger.error(f"Failed to export result: {e}")
            return "", result  # Fallback to original result
    
    def _create_file_path(self, query: str) -> Path:
        """Create file path based on current date and time.
        
        Args:
            query: The query string
            
        Returns:
            Path object for the export file
        """
        now = datetime.now()
        date_folder = now.strftime("%Y-%m-%d")
        time_prefix = now.strftime("%H-%M-%S")
        query_slug = self._create_query_slug(query)
        
        filename = f"{time_prefix}_{query_slug}.txt"
        return self.base_path / date_folder / filename
    
    def _create_query_slug(self, query: str) -> str:
        """Create a clean slug from query text.
        
        Args:
            query: The query string
            
        Returns:
            Clean slug for filename
        """
        # Take first 30 chars, clean up
        slug = query.lower()[:30]
        # Remove special characters except spaces
        slug = re.sub(r'[^a-z0-9\s]', '', slug)
        # Replace spaces with hyphens
        slug = re.sub(r'\s+', '-', slug.strip())
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        # Fallback if slug is empty
        if not slug:
            slug = "query"
            
        return slug
    
    def _count_content_lines(self, text: str) -> int:
        """Count actual content lines (excluding empty lines and simple formatting).
        
        Args:
            text: The text to count
            
        Returns:
            Number of content lines
        """
        lines = text.split('\n')
        content_lines = 0
        
        for line in lines:
            stripped = line.strip()
            # Skip empty lines and simple separators
            if stripped and not self._is_formatting_line(stripped):
                content_lines += 1
                
        return content_lines
    
    def _is_formatting_line(self, line: str) -> bool:
        """Check if line is just formatting (separators, etc.).
        
        Args:
            line: Line to check
            
        Returns:
            True if line is just formatting
        """
        # Lines that are just dashes, equals, or other separators
        if re.match(r'^[-=*_]{3,}$', line):
            return True
        # Empty brackets or simple markers
        if line in ['', '---', '===', '***']:
            return True
        return False
    
    def _format_export_content(self, query: str, result: str) -> str:
        """Format the complete export file content.
        
        Args:
            query: The original query
            result: The query result
            
        Returns:
            Formatted content for export file
        """
        now = datetime.now()
        line_count = self._count_content_lines(result)
        
        header = f"""================================================================================
TableTalk Export
================================================================================
Date: {now.strftime("%Y-%m-%d")}
Time: {now.strftime("%H:%M:%S")}
Query: "{query}"
Result Size: {line_count} lines (auto-exported due to size)

================================================================================
RESULT
================================================================================

{result}

================================================================================
END OF RESULT
================================================================================"""
        
        return header
    
    def _generate_summary(self, result: str, line_count: int) -> str:
        """Generate a summary of the exported result for console display.
        
        Args:
            result: The full result
            line_count: Number of lines in result
            
        Returns:
            Summary string for console
        """
        # Extract first few meaningful lines for summary
        lines = result.split('\n')
        summary_lines = []
        
        for line in lines[:10]:  # First 10 lines
            stripped = line.strip()
            if stripped and not self._is_formatting_line(stripped):
                summary_lines.append(line)
                if len(summary_lines) >= 5:  # Show up to 5 content lines
                    break
        
        summary = '\n'.join(summary_lines)
        
        # Add truncation notice if there's more content
        if line_count > 5:
            summary += f"\n\n[... {line_count - len(summary_lines)} more lines in export file ...]"
        
        return summary
    
    def get_export_stats(self) -> dict:
        """Get statistics about exports.
        
        Returns:
            Dictionary with export statistics
        """
        try:
            if not self.base_path.exists():
                return {"total_exports": 0, "export_folders": 0}
            
            export_count = 0
            folder_count = 0
            
            for date_folder in self.base_path.iterdir():
                if date_folder.is_dir():
                    folder_count += 1
                    export_count += len(list(date_folder.glob("*.txt")))
            
            return {
                "total_exports": export_count,
                "export_folders": folder_count,
                "export_path": str(self.base_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting export stats: {e}")
            return {"total_exports": 0, "export_folders": 0, "error": str(e)}
