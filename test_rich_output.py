#!/usr/bin/env python3
"""Simple test to demonstrate Rich-based output."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def demo_rich_output():
    """Demonstrate the new Rich-based output format."""
    
    # Title
    title_panel = Panel(
        "[bold cyan]Schema Analyzer - Rich Output Demo[/bold cyan]",
        subtitle="[dim]Professional terminal formatting[/dim]"
    )
    console.print(title_panel)
    
    # Sample database files table
    console.print(f"\n[bold magenta]Database Files:[/bold magenta]")
    
    files_table = Table()
    files_table.add_column("File", style="cyan")
    files_table.add_column("Size", justify="right", style="green")
    files_table.add_column("Rows", justify="right", style="magenta")
    files_table.add_column("Columns", justify="right", style="yellow")
    files_table.add_column("Status", justify="center")
    
    files_table.add_row("customers.csv", "2.1 MB", "10,500", "8", "[green]Ready[/green]")
    files_table.add_row("orders.csv", "5.3 MB", "25,400", "12", "[green]Ready[/green]")
    files_table.add_row("reviews.csv", "1.8 MB", "8,200", "6", "[yellow]Processing[/yellow]")
    files_table.add_row("legacy_users.csv", "850 KB", "3,100", "15", "[red]Issues[/red]")
    
    console.print(files_table)
    
    # Sample schema details
    console.print(f"\n[bold green]Column Details for 'customers':[/bold green]")
    
    schema_table = Table()
    schema_table.add_column("Column", style="cyan")
    schema_table.add_column("Data Type", style="magenta")
    schema_table.add_column("Nullable", justify="center")
    schema_table.add_column("Primary Key", justify="center")
    
    schema_table.add_row("customer_id", "INTEGER", "[dim]No[/dim]", "[green]Yes[/green]")
    schema_table.add_row("email", "VARCHAR(255)", "[dim]No[/dim]", "[dim]No[/dim]")
    schema_table.add_row("first_name", "VARCHAR(100)", "[green]Yes[/green]", "[dim]No[/dim]")
    schema_table.add_row("last_name", "VARCHAR(100)", "[green]Yes[/green]", "[dim]No[/dim]")
    schema_table.add_row("created_at", "TIMESTAMP", "[dim]No[/dim]", "[dim]No[/dim]")
    
    console.print(schema_table)
    
    # Success message
    console.print(f"\n[green]Analysis complete![/green] ✨")
    console.print(f"[dim]Professional output with Rich library - no more emoji clutter![/dim]")

if __name__ == "__main__":
    demo_rich_output()
