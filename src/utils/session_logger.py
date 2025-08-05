"""Centralized session logging using Rich for clean, readable logs."""

import logging
import time
from typing import Optional, List
from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text


class QuerySessionLogger:
    """Centralized logger for user query sessions with Rich formatting."""
    
    def __init__(self, log_file: str = "logs/tabletalk.log", verbose: bool = False):
        """Initialize the session logger.
        
        Args:
            log_file: Path to log file
            verbose: If True, include detailed debug information
        """
        self.verbose = verbose
        self.console = Console()
        self.current_query = None
        self.query_start_time = None
        
        # Set up Rich-based logging
        self._setup_logger(log_file)
        
        # Log session start
        self.logger.info("=" * 50)
        self.logger.info("[*] TableTalk Session Started")
        self.logger.info("=" * 50)
    
    def _setup_logger(self, log_file: str):
        """Set up logger with Rich handler and file output."""
        # Create logger
        self.logger = logging.getLogger("tabletalk.session")
        self.logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        # Clear existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False
        
        # Rich console handler for beautiful terminal output (only in verbose mode)
        if self.verbose:
            rich_handler = RichHandler(
                console=self.console,
                show_time=True,
                show_path=False,
                markup=True
            )
            rich_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(rich_handler)
        
        # File handler for persistent logging
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        )
        file_handler.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        
        # Suppress noisy third-party loggers
        logging.getLogger("urllib3").setLevel(logging.ERROR)
        logging.getLogger("requests").setLevel(logging.ERROR)
    
    def log_query_start(self, query: str, user_id: Optional[str] = None):
        """Log the start of a user query."""
        self.current_query = query
        self.query_start_time = time.time()
        
        # Clean, user-focused log entry
        user_part = f"[User: {user_id}] " if user_id else ""
        self.logger.info(f"[?] QUERY START: {user_part}{query}")
    
    def log_tool_execution(self, tool_name: str, args: dict = None):
        """Log when a tool is executed (high-level only)."""
        args_str = f" with {args}" if args and self.verbose else ""
        self.logger.info(f"   [T] Tool: {tool_name}{args_str}")
    
    def log_query_success(self, response: str, tools_used: List[str] = None):
        """Log successful query completion."""
        duration = time.time() - self.query_start_time if self.query_start_time else 0
        
        # Response preview (first 100 chars)
        response_preview = response[:100] + "..." if len(response) > 100 else response
        response_preview = response_preview.replace('\n', ' ').strip()
        
        # Tools used summary
        tools_info = f" | Tools: {', '.join(tools_used)}" if tools_used else ""
        
        self.logger.info(f"[+] QUERY SUCCESS ({duration:.1f}s){tools_info}")
        self.logger.info(f"   [R] Response: {response_preview}")
        
        self._reset_query_state()
    
    def log_query_error(self, error: str):
        """Log query failure."""
        duration = time.time() - self.query_start_time if self.query_start_time else 0
        
        self.logger.error(f"[-] QUERY FAILED ({duration:.1f}s): {error}")
        self._reset_query_state()
    
    def log_scan_operation(self, directory: str, files_found: int):
        """Log file scanning operations."""
        self.logger.info(f"[S] SCAN: {directory} -> {files_found} files processed")
    
    def log_system_event(self, event: str, details: str = None):
        """Log system-level events (startup, connections, etc.)."""
        details_part = f" | {details}" if details else ""
        self.logger.info(f"[SYS] SYSTEM: {event}{details_part}")
    
    def log_error(self, component: str, error: str):
        """Log component errors."""
        self.logger.error(f"[ERR] ERROR [{component}]: {error}")
    
    def log_session_end(self):
        """Log session end."""
        self.logger.info("=" * 50)
        self.logger.info("[*] TableTalk Session Ended")
        self.logger.info("=" * 50)
    
    def _reset_query_state(self):
        """Reset query tracking state."""
        self.current_query = None
        self.query_start_time = None
    
    def debug(self, message: str):
        """Log debug information (only in verbose mode)."""
        if self.verbose:
            self.logger.debug(f"[DBG] DEBUG: {message}")
