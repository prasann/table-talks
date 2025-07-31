#!/usr/bin/env python3
"""Test Rich integration with schema analyzer."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

def demo_rich_output():
    """Demonstrate what the Rich output will look like."""
    console = Console()
    
    print("=== RICH SCHEMA ANALYZER DEMO ===\n")
    
    # Simulate list_files output
    console.print("[bold green]Demo: list_files() output[/bold green]")
    table = Table(title="Database Tables (3 total)")
    table.add_column("Table", style="cyan", no_wrap=True)
    table.add_column("Columns", justify="right", style="magenta")
    table.add_column("Rows", justify="right", style="green")
    table.add_column("Sample Columns", style="dim")
    
    table.add_row("customers", "8", "15,420", "id, name, email, ... +5 more")
    table.add_row("orders", "12", "89,333", "order_id, customer_id, total, ... +9 more")
    table.add_row("products", "6", "1,250", "product_id, name, price, ... +3 more")
    
    console.print(table)
    print()
    
    # Simulate get_file_schema output
    console.print("[bold green]Demo: get_file_schema('customers') output[/bold green]")
    title_panel = Panel("[bold blue]Schema: customers[/bold blue]", style="blue")
    console.print(title_panel)
    
    console.print("Rows: [green]15,420[/green] | "
                  "Columns: [magenta]8[/magenta] | "
                  "Size: [yellow]2.1 MB[/yellow]")
    console.print()
    
    col_table = Table(title="Columns", show_header=True, header_style="bold magenta")
    col_table.add_column("Column", style="cyan")
    col_table.add_column("Type", style="yellow")
    col_table.add_column("Nullable", justify="center", style="dim")
    col_table.add_column("Constraints", style="green")
    
    col_table.add_row("id", "INTEGER", "✗", "PK")
    col_table.add_row("name", "VARCHAR(100)", "✗", "")
    col_table.add_row("email", "VARCHAR(255)", "✓", "")
    col_table.add_row("created_at", "TIMESTAMP", "✗", "DEFAULT NOW()")
    
    console.print(col_table)
    console.print("\n[bold green]Primary Keys:[/bold green] id")
    print()
    
    # Simulate search_columns output
    console.print("[bold green]Demo: search_columns('id') output[/bold green]")
    search_table = Table(title="Search Results for 'id' (4 found)")
    search_table.add_column("Table", style="cyan")
    search_table.add_column("Column", style="bright_cyan")
    search_table.add_column("Type", style="yellow")
    search_table.add_column("Nullable", justify="center", style="dim")
    
    search_table.add_row("customers", "id", "INTEGER", "✗")
    search_table.add_row("orders", "order_id", "INTEGER", "✗")
    search_table.add_row("orders", "customer_id", "INTEGER", "✗")
    search_table.add_row("products", "product_id", "INTEGER", "✗")
    
    console.print(search_table)
    print()
    
    # Benefits summary
    console.print("[bold yellow]Benefits of Rich Integration:[/bold yellow]")
    console.print("• [cyan]Clean, professional tables[/cyan]")
    console.print("• [green]Color-coded information[/green]")
    console.print("• [magenta]Easy to scan and read[/magenta]")
    console.print("• [blue]Consistent formatting[/blue]")
    console.print("• [red]Much simpler code than emojis/markdown[/red]")

if __name__ == "__main__":
    demo_rich_output()
