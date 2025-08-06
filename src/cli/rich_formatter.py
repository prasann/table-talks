"""Rich-based CLI formatting for TableTalk.

Centralized Rich formatting for CLI - keeps rich isolated to CLI layer.
This allows easy replacement with UI layer in the future.
"""

import threading
import time

# Third-party imports
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
from rich.markup import escape
from rich.syntax import Syntax
from rich.rule import Rule
from rich.status import Status


class CLIFormatter:
    """Centralized Rich formatting for CLI - keeps rich isolated to CLI layer."""
    
    def __init__(self):
        """Initialize the formatter."""
        self.console = Console()
        self._status_context = None
        self._status_lock = threading.Lock()
    
    def print_startup(self, message):
        """Format startup messages."""
        self.console.print(Panel(
            f"[bold blue]{message}[/bold blue]",
            title="[bold]TableTalk[/bold]",
            border_style="blue"
        ))
    
    def print_status(self, status_data):
        """Format system/agent status information."""
        table = Table(title="System Status", show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        
        # Add rows based on status data
        if 'mode' in status_data:
            table.add_row("Agent Mode", status_data['mode'], "")
        
        if 'llm_available' in status_data:
            llm_status = "[+] Available" if status_data['llm_available'] else "[-] Not Available"
            table.add_row("LLM", llm_status, status_data.get('model_name', ''))
        
        if 'function_calling' in status_data:
            fc_status = "[+] Enabled" if status_data['function_calling'] else "[-] Disabled"
            table.add_row("Function Calling", fc_status, "")
        
        if 'tools_count' in status_data:
            tools_info = f"{status_data['tools_count']} tools"
            if 'tools_list' in status_data:
                tools_preview = ', '.join(status_data['tools_list'][:3])
                if len(status_data['tools_list']) > 3:
                    tools_preview += "..."
                tools_info = f"{tools_info}: {tools_preview}"
            table.add_row("Tools Available", str(status_data['tools_count']), tools_info)
        
        if 'files_scanned' in status_data:
            table.add_row("Files Scanned", str(status_data['files_scanned']), "")
        
        self.console.print(table)
    
    def print_scan_progress(self, file_path, columns_count):
        """Format file scanning progress."""
        self.console.print(f"[green][+][/green] [cyan]{file_path}[/cyan]: [yellow]{columns_count}[/yellow] columns")
    
    def print_scan_error(self, file_path, error):
        """Format file scanning errors."""
        self.console.print(f"[red][-][/red] [cyan]{file_path}[/cyan]: [red]{escape(str(error))}[/red]")
    
    def print_scan_start(self, directory_path):
        """Format scan start message."""
        self.console.print(Panel(
            f"[bold cyan]Scanning:[/bold cyan] [yellow]{directory_path}[/yellow]",
            border_style="cyan"
        ))
    
    def print_scan_complete(self, file_count):
        """Format scan completion message."""
        self.console.print(Panel(
            f"[bold green]Scan complete:[/bold green] [yellow]{file_count}[/yellow] files processed",
            border_style="green"
        ))
    
    def print_command_help(self):
        """Format help text."""
        help_text = """
[bold cyan]TableTalk Commands:[/bold cyan]
  [yellow]/scan <directory>[/yellow]  - Scan files for schema information
  [yellow]/status[/yellow]            - Show system status
  [yellow]/strategy[/yellow]          - Show agent information
  [yellow]/exports[/yellow]           - Show export status and statistics
  [yellow]/help[/yellow]              - Show this help
  [yellow]/exit[/yellow]              - Exit TableTalk

[bold green]Start by scanning a directory:[/bold green] [cyan]/scan data/[/cyan]

[bold magenta]Query Examples:[/bold magenta]
  [italic]"Show me the customers table"[/italic]
  [italic]"What columns are in orders?"[/italic]
  [italic]"How many rows are in each file?"[/italic]
  [italic]"Show me tables with email addresses"[/italic]
  [italic]"Find schema differences between all files"[/italic]

[bold blue]Export Info:[/bold blue]
  Large results (>100 lines) are automatically exported to [cyan]./exports/YYYY-MM-DD/[/cyan]
        """.strip()
        
        self.console.print(Panel(help_text, title="Help", border_style="blue"))
    
    def print_agent_response(self, response):
        """Format LLM/agent responses."""
        # Try to detect if response looks like code/data and highlight it
        if any(keyword in response.lower() for keyword in ['select', 'table', 'column', 'schema']):
            # Likely contains SQL or data structure info
            self.console.print(Panel(response, border_style="green", title="Response"))
        else:
            self.console.print(response)
    
    def print_error(self, message, details=None):
        """Format error messages."""
        error_panel = Panel(
            f"[bold red]Error:[/bold red] {escape(str(message))}" + 
            (f"\n[dim]{escape(str(details))}[/dim]" if details else ""),
            border_style="red",
            title="Error"
        )
        self.console.print(error_panel)
    
    def print_warning(self, message):
        """Format warning messages."""
        self.console.print(f"[yellow][!] {escape(str(message))}[/yellow]")
    
    def print_info(self, message):
        """Format info messages."""
        self.console.print(f"[blue][i] {escape(str(message))}[/blue]")
    
    def print_success(self, message):
        """Format success messages."""
        self.console.print(f"[green][+] {escape(str(message))}[/green]")
    
    def print_welcome(self):
        """Format welcome message."""
        welcome_text = Text()
        welcome_text.append("TableTalk", style="bold blue")
        welcome_text.append(" - Conversational data exploration", style="cyan")
        
        panel = Panel(
            welcome_text,
            subtitle="[CLI] Commands: /scan <dir>, /help, /status, /exit",
            border_style="bright_green"
        )
        self.console.print(panel)
    
    def print_mode_info(self, intelligent_mode=False):
        """Format mode information."""
        if intelligent_mode:
            self.console.print("[green][*] Intelligent mode: Ask complex questions and get smart insights![/green]")
    
    def print_goodbye(self):
        """Format goodbye messages."""
        self.console.print(Panel(
            "[bold yellow]Thanks for using TableTalk![/bold yellow]",
            title="[bold]Goodbye[/bold]",
            border_style="yellow"
        ))
    
    def print_rule(self, title=None):
        """Print a separator rule."""
        self.console.print(Rule(title=title))
    
    def create_scan_progress(self):
        """Create a progress bar for scanning operations."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        )
    
    def create_loading_indicator(self, message):
        """Create a loading indicator context manager."""
        return self.console.status(message, spinner="dots")
