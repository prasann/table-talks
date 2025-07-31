"""Rich-based formatter for schema analyzer output."""

from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .templates import TEMPLATES, MESSAGES


class RichFormatter:
    """Handles all Rich-based formatting for schema analyzer output."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the formatter.
        
        Args:
            console: Rich console instance, creates new one if None
        """
        self.console = console or Console()
    
    def format_message(self, message_type: str, message_key: str, **kwargs) -> str:
        """Format a message using templates.
        
        Args:
            message_type: Type of message (errors, warnings, info)
            message_key: Specific message key
            **kwargs: Template variables
            
        Returns:
            Empty string (prints directly to console)
        """
        template = MESSAGES.get(message_type, {}).get(message_key, "")
        if template:
            self.console.print(template.format(**kwargs))
        return ""
    
    def format_table(self, template_name: str, data: Dict[str, Any]) -> str:
        """Format data using a table template.
        
        Args:
            template_name: Name of template to use
            data: Data to format
            
        Returns:
            Empty string (prints directly to console)
        """
        template = TEMPLATES.get(template_name)
        if not template:
            self.console.print(f"[red]Template '{template_name}' not found[/red]")
            return ""
        
        # Handle nested table templates (e.g., columns_table within schema_detail)
        if 'template_key' in data and data['template_key'] in template:
            table_template = template[data['template_key']]
        else:
            table_template = template
        
        # Handle empty data
        if not data.get('items') and template.get('empty_message'):
            style = template.get('empty_style', 'yellow')
            message = template['empty_message'].format(**data)
            self.console.print(f"[{style}]{message}[/{style}]")
            return ""
        
        # Create table
        title = table_template.get('title', '').format(**data)
        show_header = table_template.get('show_header', True)
        header_style = table_template.get('header_style', 'bold')
        
        table = Table(title=title, show_header=show_header, header_style=header_style)
        
        # Add columns
        for col_def in table_template['columns']:
            # Extract name and other properties
            col_def_copy = col_def.copy()
            col_name = col_def_copy.pop('name', '')
            table.add_column(col_name, **col_def_copy)
        
        # Add rows
        row_mapper = table_template['row_mapper']
        for item in data.get('items', []):
            row = row_mapper(item)
            table.add_row(*row)
        
        self.console.print(table)
        return ""
    
    def format_panel(self, template_name: str, panel_key: str, data: Dict[str, Any]) -> str:
        """Format a panel using templates.
        
        Args:
            template_name: Name of template
            panel_key: Specific panel key within template
            data: Data for formatting
            
        Returns:
            Empty string (prints directly to console)
        """
        template = TEMPLATES.get(template_name, {}).get(panel_key, {})
        if not template:
            return ""
        
        title = template.get('title', '').format(**data)
        subtitle = template.get('subtitle', '').format(**data) if template.get('subtitle') else None
        style = template.get('style', 'blue')
        
        panel = Panel(f"[bold {style}]{title}[/bold {style}]", style=style, subtitle=subtitle)
        self.console.print(panel)
        return ""
    
    def format_stats(self, template_name: str, data: Dict[str, Any]) -> str:
        """Format statistics using templates.
        
        Args:
            template_name: Name of template
            data: Data for formatting
            
        Returns:
            Empty string (prints directly to console)
        """
        template = TEMPLATES.get(template_name, {})
        
        # Handle single stat format
        if 'stats_format' in template:
            self.console.print(template['stats_format'].format(**data))
            self.console.print()
            return ""
        
        # Handle multiple stats
        stats = template.get('stats', [])
        for stat in stats:
            formatted_stat = stat.format(**data)
            self.console.print(formatted_stat)
        
        if stats:
            self.console.print()
        return ""
    
    def format_sections(self, template_name: str, data: Dict[str, Any]) -> str:
        """Format additional sections using templates.
        
        Args:
            template_name: Name of template
            data: Data for formatting
            
        Returns:
            Empty string (prints directly to console)
        """
        template = TEMPLATES.get(template_name, {})
        sections = template.get('sections', {})
        
        for section_key, section_data in data.get('sections', {}).items():
            if section_key in sections and section_data:
                section_template = sections[section_key]
                
                # Print section title
                self.console.print(f"\n{section_template['title']}")
                
                # Print section content
                if isinstance(section_data, list):
                    for item in section_data:
                        formatted_item = section_template['format'].format(**item)
                        self.console.print(formatted_item)
                else:
                    formatted_content = section_template['format'].format(**section_data)
                    self.console.print(formatted_content)
        
        return ""
    
    def format_quality_panel(self, data: Dict[str, Any]) -> str:
        """Format data quality panel with score-based styling.
        
        Args:
            data: Data containing score and other info
            
        Returns:
            Empty string (prints directly to console)
        """
        score = data.get('score', 0)
        
        if score >= 80:
            panel_key = 'panel_good'
        elif score >= 60:
            panel_key = 'panel_fair'
        else:
            panel_key = 'panel_poor'
        
        return self.format_panel('data_quality', panel_key, data)
    
    def format_data_quality_basic(self, data: Dict[str, Any]) -> str:
        """Format basic data quality analysis results.
        
        Args:
            data: Quality data with score and table results
            
        Returns:
            Empty string (prints directly to console)
        """
        score = data.get('score', 0)
        
        # Format panel based on score
        if score >= 80:
            panel_key = 'panel_good'
        elif score >= 60:
            panel_key = 'panel_fair'
        else:
            panel_key = 'panel_poor'
        
        self.format_panel('data_quality_basic', panel_key, data)
        
        # Format stats
        total_tables = data.get('total_tables', 0)
        total_issues = data.get('total_issues', 0)
        
        self.console.print(f"Tables analyzed: [cyan]{total_tables}[/cyan]")
        
        if total_issues > 0:
            self.console.print(f"Total issues found: [red]{total_issues}[/red]")
        else:
            self.console.print("Total issues found: [green]0[/green] ✨")
        
        # Format table results if available
        table_results = data.get('table_results', [])
        if table_results:
            self.console.print(f"\n[bold magenta]Quality by Table:[/bold magenta]")
            
            # Transform data for template
            table_data = []
            for result in table_results:
                if 'error' in result:
                    table_data.append({
                        'name': result['name'],
                        'row_count': 0,
                        'column_count': 0,
                        'quality_score': 0,
                        'issue_count': 0,
                        'status': '[red]Failed[/red]'
                    })
                else:
                    quality_score = result.get('quality_score', 0)
                    issue_count = len(result.get('issues', []))
                    
                    if quality_score >= 80:
                        status = "[green]Good[/green]"
                    elif quality_score >= 60:
                        status = "[yellow]Fair[/yellow]"
                    else:
                        status = "[red]Poor[/red]"
                    
                    table_data.append({
                        'name': result['name'],
                        'row_count': result.get('row_count', 0),
                        'column_count': result.get('column_count', 0),
                        'quality_score': quality_score,
                        'issue_count': issue_count,
                        'status': status
                    })
            
            # Use the formatter to create the quality table
            template = TEMPLATES.get('data_quality_basic', {}).get('quality_table', {})
            if template:
                table = Table()
                
                # Add columns
                for col_def in template['columns']:
                    # Extract name and other properties
                    col_def_copy = col_def.copy()
                    col_name = col_def_copy.pop('name', '')
                    table.add_column(col_name, **col_def_copy)
                
                # Add rows
                row_mapper = template['row_mapper']
                for item in table_data:
                    row = row_mapper(item)
                    table.add_row(*row)
                
                self.console.print(table)
        
        # Show sample issues if any
        if total_issues > 0 and table_results:
            self.console.print(f"\n[bold red]Sample Issues:[/bold red]")
            issue_count = 0
            for table_result in table_results:
                if 'issues' in table_result and table_result['issues']:
                    for issue in table_result['issues'][:2]:  # Show max 2 per table
                        self.console.print(f"  • {table_result['name']}: {issue}")
                        issue_count += 1
                        if issue_count >= 5:  # Show max 5 total
                            break
                if issue_count >= 5:
                    break
            
            if total_issues > 5:
                self.console.print(f"  ... and {total_issues - 5} more issues")
        
        return ""


def create_formatter(console: Optional[Console] = None) -> RichFormatter:
    """Factory function to create a formatter instance.
    
    Args:
        console: Rich console instance
        
    Returns:
        RichFormatter instance
    """
    return RichFormatter(console)
