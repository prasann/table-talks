"""Schema analyzer combining SQLAlchemy and Great Expectations."""

import os
import sys
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

# Rich imports for beautiful terminal output
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.utils.logger import get_logger
from src.metadata.sqlalchemy_inspector import SQLAlchemyInspector, create_inspector
from quality.expectations_analyzer import ExpectationsAnalyzer, create_analyzer

# Initialize Rich console for output formatting
console = Console()


class SchemaAnalyzer:
    """Unified analyzer using SQLAlchemy + Great Expectations.
    
    Combines the power of SQLAlchemy's database introspection with
    Great Expectations' data quality validation capabilities to provide
    comprehensive schema analysis and data quality assessment.
    """
    
    def __init__(self, database_path: str):
        """Initialize the schema analyzer.
        
        Args:
            database_path: Path to DuckDB database file
        """
        self.database_path = Path(database_path)
        self.logger = get_logger("tabletalk.schema_analyzer")
        
        # Initialize components
        self.sql_inspector = create_inspector(str(database_path))
        self.expectations = create_analyzer(str(database_path))
        
        # Check if components initialized successfully
        self.sql_available = self.sql_inspector is not None
        self.gx_available = self.expectations is not None
        
        if not self.sql_available:
            self.logger.warning("SQLAlchemy inspector not available - schema introspection disabled")
        
        if not self.gx_available:
            self.logger.warning("Great Expectations analyzer not available - data quality analysis disabled")
        
        if not (self.sql_available or self.gx_available):
            raise RuntimeError("Neither SQLAlchemy nor Great Expectations are available")
        
        self.logger.info(f"Schema analyzer initialized (SQL: {self.sql_available}, GX: {self.gx_available})")
    
    def refresh(self):
        """Refresh the analyzer to pick up newly created tables."""
        if self.sql_inspector:
            # Force refresh the SQLAlchemy inspector
            self.sql_inspector.inspector = self.sql_inspector.inspector.__class__(self.sql_inspector.engine)
            self.logger.debug("SQLAlchemy inspector refreshed")
    
    # ===== Core Table Operations =====
    
    def list_files(self) -> str:
        """List all available tables/files in the database.
        
        Returns:
            Formatted string with table information
        """
        try:
            if not self.sql_available:
                console.print("[red]SQLAlchemy not available - cannot list tables[/red]")
                return ""
            
            tables = self.sql_inspector.get_tables()
            
            if not tables:
                console.print("[yellow]No tables found in the database[/yellow]")
                return ""
            
            # Create a table for better formatting
            table = Table(title=f"Database Tables ({len(tables)} total)")
            table.add_column("Table", style="cyan", no_wrap=True)
            table.add_column("Columns", justify="right", style="magenta")
            table.add_column("Rows", justify="right", style="green")
            table.add_column("Sample Columns", style="dim")
            
            for table_name in tables:
                # Get basic table info
                columns = self.sql_inspector.get_columns(table_name)
                stats = self.sql_inspector.get_table_stats(table_name)
                
                # Show first few column names
                col_names = [col['name'] for col in columns[:3]]
                if len(columns) > 3:
                    col_names.append(f"... +{len(columns) - 3} more")
                sample_cols = ", ".join(col_names) if col_names else "None"
                
                row_count = stats.get('row_count', 0)
                row_display = f"{row_count:,}" if isinstance(row_count, int) else str(row_count)
                
                table.add_row(table_name, str(len(columns)), row_display, sample_cols)
            
            console.print(table)
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to list files: {e}")
            console.print(f"[red]Error listing tables: {e}[/red]")
            return ""
    
    def get_file_schema(self, file_name: str) -> str:
        """Get detailed schema for a specific table.
        
        Args:
            file_name: Name of the table
            
        Returns:
            Formatted string with detailed schema information
        """
        try:
            if not self.sql_available:
                console.print(f"[red]SQLAlchemy not available - cannot get schema for '{file_name}'[/red]")
                return ""
            
            # Check if table exists
            tables = self.sql_inspector.get_tables()
            if file_name not in tables:
                available = ", ".join(tables) if tables else "none"
                console.print(f"[red]Table '{file_name}' not found[/red]")
                console.print(f"[dim]Available tables: {available}[/dim]")
                return ""
            
            # Get comprehensive schema information
            columns = self.sql_inspector.get_columns(file_name)
            primary_keys = self.sql_inspector.get_primary_keys(file_name)
            foreign_keys = self.sql_inspector.get_foreign_keys(file_name)
            indexes = self.sql_inspector.get_indexes(file_name)
            stats = self.sql_inspector.get_table_stats(file_name)
            
            # Title panel
            title_panel = Panel(f"[bold blue]Schema: {file_name}[/bold blue]", style="blue")
            console.print(title_panel)
            
            # Basic statistics
            row_count = stats.get('row_count', 0)
            size_bytes = stats.get('estimated_size_bytes', 0)
            size_mb = size_bytes / (1024 * 1024) if size_bytes > 0 else 0
            
            console.print(f"Rows: [green]{row_count:,}[/green] | "
                         f"Columns: [magenta]{len(columns)}[/magenta] | "
                         f"Size: [yellow]{size_mb:.1f} MB[/yellow]")
            console.print()
            
            # Columns table
            col_table = Table(title="Columns", show_header=True, header_style="bold magenta")
            col_table.add_column("Column", style="cyan")
            col_table.add_column("Type", style="yellow")
            col_table.add_column("Nullable", justify="center", style="dim")
            col_table.add_column("Constraints", style="green")
            
            for col in columns:
                constraints = []
                if col.get('primary_key'):
                    constraints.append("PK")
                if col.get('default') is not None:
                    constraints.append(f"DEFAULT {col['default']}")
                
                nullable = "✓" if col['nullable'] else "✗"
                constraint_str = ", ".join(constraints) if constraints else ""
                
                col_table.add_row(col['name'], str(col['type']), nullable, constraint_str)
            
            console.print(col_table)
            
            # Additional info if present
            if primary_keys:
                console.print(f"\n[bold green]Primary Keys:[/bold green] {', '.join(primary_keys)}")
            
            if foreign_keys:
                console.print(f"\n[bold blue]Foreign Keys:[/bold blue]")
                for fk in foreign_keys:
                    constrained_cols = ', '.join(fk.get('constrained_columns', []))
                    referred_table = fk.get('referred_table', 'unknown')
                    referred_cols = ', '.join(fk.get('referred_columns', []))
                    console.print(f"  • {constrained_cols} → {referred_table}({referred_cols})")
            
            if indexes:
                console.print(f"\n[bold yellow]Indexes:[/bold yellow]")
                for idx in indexes:
                    idx_name = idx.get('name', 'unnamed')
                    idx_cols = ', '.join(idx.get('column_names', []))
                    unique_str = " (UNIQUE)" if idx.get('unique') else ""
                    console.print(f"  • {idx_name}: {idx_cols}{unique_str}")
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to get schema for '{file_name}': {e}")
            console.print(f"[red]Error getting schema for '{file_name}': {e}[/red]")
            return ""
    
    def get_database_summary(self) -> str:
        """Get comprehensive database summary.
        
        Returns:
            Formatted string with database-wide statistics
        """
        try:
            if not self.sql_available:
                console.print("[red]SQLAlchemy not available - cannot generate database summary[/red]")
                return ""
            
            summary = self.sql_inspector.get_database_summary()
            
            if 'error' in summary:
                console.print(f"[red]Error generating database summary: {summary['error']}[/red]")
                return ""
            
            # Database summary panel
            title_panel = Panel(f"[bold blue]Database Summary[/bold blue]", style="blue")
            console.print(title_panel)
            
            # Overall statistics
            console.print(f"Database: [cyan]{summary['database_path']}[/cyan]")
            console.print(f"Total tables: [green]{summary['total_tables']}[/green]")
            console.print(f"Total rows: [yellow]{summary['total_rows']:,}[/yellow]")
            console.print(f"Total columns: [magenta]{summary['total_columns']}[/magenta]")
            console.print()
            
            # Table-by-table breakdown
            if summary['tables']:
                db_table = Table(title="Tables Breakdown")
                db_table.add_column("Table", style="cyan")
                db_table.add_column("Rows", justify="right", style="green")
                db_table.add_column("Columns", justify="right", style="magenta")
                db_table.add_column("Data Types", style="dim")
                
                for table_name, table_info in summary['tables'].items():
                    stats = table_info.get('stats', {})
                    columns = table_info.get('columns', [])
                    
                    # Show data types distribution
                    type_counts = {}
                    for col in columns:
                        col_type = str(col.get('type', 'unknown')).split('(')[0]  # Remove length info
                        type_counts[col_type] = type_counts.get(col_type, 0) + 1
                    
                    types_str = ', '.join([f"{t}({c})" for t, c in type_counts.items()]) if type_counts else "None"
                    row_count = stats.get('row_count', 0)
                    
                    db_table.add_row(
                        table_name,
                        f"{row_count:,}",
                        str(len(columns)),
                        types_str
                    )
                
                console.print(db_table)
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to generate database summary: {e}")
            console.print(f"[red]Error generating database summary: {e}[/red]")
            return ""
    
    # ===== Data Quality Operations =====
    
    def analyze_data_quality(self) -> str:
        """Perform comprehensive data quality analysis.
        
        Returns:
            Formatted string with data quality results
        """
        try:
            if not self.gx_available:
                # Fallback to basic data quality analysis without Great Expectations
                return self._basic_data_quality_analysis()
            
            try:
                analysis = self.expectations.analyze_data_quality()
            except Exception as gx_error:
                self.logger.warning(f"Great Expectations analysis failed: {gx_error}, falling back to basic analysis")
                return self._basic_data_quality_analysis()
            
            if 'error' in analysis:
                self.logger.warning(f"Great Expectations analysis error: {analysis['error']}, falling back to basic analysis")
                return self._basic_data_quality_analysis()
            
            # Display results using Rich
            overall_score = analysis.get('overall_quality_score', 0)
            total_tables = analysis.get('total_tables', 0)
            
            # Quality score panel with color coding
            if overall_score >= 80:
                score_color = "green"
                status = "Excellent"
            elif overall_score >= 60:
                score_color = "yellow"
                status = "Good"
            else:
                score_color = "red"
                status = "Needs Attention"
            
            title_panel = Panel(
                f"[bold {score_color}]Data Quality: {overall_score:.1f}% ({status})[/bold {score_color}]",
                style=score_color
            )
            console.print(title_panel)
            
            console.print(f"Tables analyzed: [cyan]{total_tables}[/cyan]")
            
            # Issues summary
            issues = analysis.get('issues_summary', [])
            if issues:
                console.print(f"Issues found: [red]{len(issues)}[/red]")
                console.print("\n[bold red]Top Issues:[/bold red]")
                for i, issue in enumerate(issues[:5], 1):
                    console.print(f"  {i}. {issue}")
                if len(issues) > 5:
                    console.print(f"  ... and {len(issues) - 5} more issues")
            else:
                console.print("Issues found: [green]0[/green] ✨")
            
            # Table-by-table results
            tables_analyzed = analysis.get('tables_analyzed', {})
            if tables_analyzed:
                console.print(f"\n[bold magenta]Quality by Table:[/bold magenta]")
                
                quality_table = Table()
                quality_table.add_column("Table", style="cyan")
                quality_table.add_column("Quality Score", justify="right")
                quality_table.add_column("Status", justify="center")
                
                for table_name, table_analysis in tables_analyzed.items():
                    if 'error' in table_analysis:
                        quality_table.add_row(table_name, "—", "[red]Failed[/red]")
                        continue
                    
                    validation = table_analysis.get('validation', {})
                    table_score = validation.get('data_quality_score', 0)
                    
                    if table_score >= 80:
                        status = "[green]Good[/green]"
                    elif table_score >= 60:
                        status = "[yellow]Fair[/yellow]"
                    else:
                        status = "[red]Poor[/red]"
                    
                    quality_table.add_row(table_name, f"{table_score:.1f}%", status)
                
                console.print(quality_table)
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to analyze data quality: {e}")
            console.print(f"[red]Error analyzing data quality: {e}[/red]")
            return ""
    
    def _basic_data_quality_analysis(self) -> str:
        """Perform basic data quality analysis using SQLAlchemy only.
        
        Returns:
            Formatted string with basic data quality results
        """
        try:
            if not self.sql_available:
                console.print("[red]SQLAlchemy not available - data quality analysis disabled[/red]")
                return ""
            
            tables = self.sql_inspector.get_tables()
            
            # Overall statistics
            total_tables = len(tables)
            total_issues = 0
            table_results = []
            
            # Progress indication
            console.print(f"[dim]Analyzing {total_tables} tables...[/dim]")
            
            for table_name in tables:
                try:
                    table_issues = []
                    
                    # Basic checks using SQL
                    with self.sql_inspector.engine.connect() as conn:
                        # Check if table is empty
                        row_count_result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                        row_count = row_count_result.fetchone()[0]
                        
                        if row_count == 0:
                            table_issues.append("Table is empty")
                        
                        # Get column info
                        columns = self.sql_inspector.get_columns(table_name)
                        
                        # Check for columns with all NULL values (if table has data)
                        if row_count > 0:
                            for col in columns:
                                col_name = col['name']
                                null_check = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NOT NULL")
                                non_null_count = null_check.fetchone()[0]
                                
                                if non_null_count == 0:
                                    table_issues.append(f"Column '{col_name}' has all NULL values")
                        
                        # Basic quality score calculation
                        total_checks = 1 + len(columns)  # empty table check + null checks
                        failed_checks = len(table_issues)
                        quality_score = ((total_checks - failed_checks) / total_checks) * 100 if total_checks > 0 else 100
                        
                        table_results.append({
                            'name': table_name,
                            'row_count': row_count,
                            'column_count': len(columns),
                            'issues': table_issues,
                            'quality_score': quality_score
                        })
                        
                        total_issues += len(table_issues)
                
                except Exception as e:
                    self.logger.warning(f"Failed to analyze table {table_name}: {e}")
                    table_results.append({
                        'name': table_name,
                        'error': str(e)
                    })
            
            # Calculate overall score
            if table_results:
                valid_scores = [t['quality_score'] for t in table_results if 'quality_score' in t]
                overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
            else:
                overall_score = 0
            
            # Display results using Rich
            if overall_score >= 80:
                score_color = "green"
                status = "Good"
            elif overall_score >= 60:
                score_color = "yellow"
                status = "Fair"
            else:
                score_color = "red"
                status = "Poor"
            
            title_panel = Panel(
                f"[bold {score_color}]Data Quality (Basic): {overall_score:.1f}% ({status})[/bold {score_color}]",
                style=score_color
            )
            console.print(title_panel)
            
            console.print(f"Tables analyzed: [cyan]{total_tables}[/cyan]")
            
            if total_issues > 0:
                console.print(f"Total issues found: [red]{total_issues}[/red]")
            else:
                console.print("Total issues found: [green]0[/green] ✨")
            
            # Table-by-table results
            if table_results:
                console.print(f"\n[bold magenta]Quality by Table:[/bold magenta]")
                
                quality_table = Table()
                quality_table.add_column("Table", style="cyan")
                quality_table.add_column("Rows", justify="right", style="dim")
                quality_table.add_column("Columns", justify="right", style="dim")
                quality_table.add_column("Quality Score", justify="right")
                quality_table.add_column("Issues", justify="right")
                quality_table.add_column("Status", justify="center")
                
                for table_result in table_results:
                    if 'error' in table_result:
                        quality_table.add_row(
                            table_result['name'], 
                            "—", "—", "—", "—", 
                            "[red]Failed[/red]"
                        )
                        continue
                    
                    quality_score = table_result['quality_score']
                    issue_count = len(table_result.get('issues', []))
                    
                    if quality_score >= 80:
                        status = "[green]Good[/green]"
                    elif quality_score >= 60:
                        status = "[yellow]Fair[/yellow]"
                    else:
                        status = "[red]Poor[/red]"
                    
                    quality_table.add_row(
                        table_result['name'],
                        f"{table_result['row_count']:,}",
                        str(table_result['column_count']),
                        f"{quality_score:.1f}%",
                        str(issue_count),
                        status
                    )
                
                console.print(quality_table)
                
                # Show some sample issues if any
                if total_issues > 0:
                    console.print(f"\n[bold red]Sample Issues:[/bold red]")
                    issue_count = 0
                    for table_result in table_results:
                        if 'issues' in table_result and table_result['issues']:
                            for issue in table_result['issues'][:2]:  # Show max 2 per table
                                console.print(f"  • {table_result['name']}: {issue}")
                                issue_count += 1
                                if issue_count >= 5:  # Show max 5 total
                                    break
                        if issue_count >= 5:
                            break
                    
                    if total_issues > 5:
                        console.print(f"  ... and {total_issues - 5} more issues")
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to perform basic data quality analysis: {e}")
            console.print(f"[red]Error in basic data quality analysis: {e}[/red]")
            return ""
    
    # ===== Column Analysis Operations =====
    
    def search_columns(self, search_term: str) -> str:
        """Search for columns containing a specific term.
        
        Args:
            search_term: Term to search for in column names
            
        Returns:
            Formatted string with search results
        """
        try:
            if not self.sql_available:
                console.print(f"[red]SQLAlchemy not available - cannot search columns for '{search_term}'[/red]")
                return ""
            
            if not search_term.strip():
                console.print("[red]Please provide a search term[/red]")
                return ""
            
            tables = self.sql_inspector.get_tables()
            matches = []
            
            for table in tables:
                columns = self.sql_inspector.get_columns(table)
                
                for col in columns:
                    if search_term.lower() in col['name'].lower():
                        matches.append({
                            'table': table,
                            'column': col['name'],
                            'type': col['type'],
                            'nullable': col['nullable']
                        })
            
            if not matches:
                console.print(f"[yellow]No columns found containing '{search_term}'[/yellow]")
                return ""
            
            # Display results in a nice table
            search_table = Table(title=f"Search Results for '{search_term}' ({len(matches)} found)")
            search_table.add_column("Table", style="cyan")
            search_table.add_column("Column", style="bright_cyan")
            search_table.add_column("Type", style="yellow")
            search_table.add_column("Nullable", justify="center", style="dim")
            
            for match in matches:
                nullable = "✓" if match['nullable'] else "✗"
                search_table.add_row(
                    match['table'], 
                    match['column'], 
                    str(match['type']), 
                    nullable
                )
            
            console.print(search_table)
            return ""
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to search columns for '{search_term}': {e}")
            console.print(f"[red]Error searching columns: {e}[/red]")
            return ""
    
    def get_column_data_types(self, column_name: str) -> str:
        """Get data types for a column across all tables.
        
        Args:
            column_name: Name of the column to analyze
            
        Returns:
            Formatted string with column type information across tables
        """
        try:
            if not self.sql_available:
                console.print(f"[red]SQLAlchemy not available - cannot analyze column '{column_name}'[/red]")
                return ""
            
            if not column_name.strip():
                console.print("[red]Please provide a column name[/red]")
                return ""
            
            tables = self.sql_inspector.get_tables()
            column_info = []
            
            for table in tables:
                columns = self.sql_inspector.get_columns(table)
                
                for col in columns:
                    if col['name'].lower() == column_name.lower():
                        stats = self.sql_inspector.get_table_stats(table)
                        column_info.append({
                            'table': table,
                            'type': col['type'],
                            'nullable': col['nullable'],
                            'primary_key': col.get('primary_key', False),
                            'default': col.get('default'),
                            'table_rows': stats.get('row_count', 0)
                        })
            
            if not column_info:
                console.print(f"[yellow]Column '{column_name}' not found in any table[/yellow]")
                return ""
            
            # Create title panel
            title_panel = Panel(
                f"[bold cyan]Column '{column_name}' Analysis[/bold cyan]",
                subtitle=f"[dim]Found in {len(column_info)} tables[/dim]"
            )
            console.print(title_panel)
            
            # Group by data type
            type_groups = {}
            for info in column_info:
                col_type = str(info['type'])
                if col_type not in type_groups:
                    type_groups[col_type] = []
                type_groups[col_type].append(info)
            
            # Show type consistency
            if len(type_groups) == 1:
                console.print("[green]Type Consistency: GOOD[/green] - All tables use the same type\n")
            else:
                console.print(f"[yellow]Type Consistency: INCONSISTENT[/yellow] - {len(type_groups)} different types found\n")
            
            # Create table for column details
            column_table = Table()
            column_table.add_column("Table", style="cyan")
            column_table.add_column("Data Type", style="magenta")
            column_table.add_column("Nullable", justify="center")
            column_table.add_column("Primary Key", justify="center")
            column_table.add_column("Default", style="dim")
            column_table.add_column("Rows", justify="right", style="dim")
            
            for col_type, infos in sorted(type_groups.items()):
                # Add a separator row for each type if multiple types
                if len(type_groups) > 1:
                    column_table.add_row(f"[bold]{col_type}[/bold]", "", "", "", "", "")
                
                for info in infos:
                    nullable = "Yes" if info['nullable'] else "No"
                    pk = "Yes" if info['primary_key'] else "No"
                    default = str(info['default']) if info['default'] is not None else "—"
                    
                    # Style the important columns
                    nullable_style = "dim" if nullable == "Yes" else "green"
                    pk_style = "green" if pk == "Yes" else "dim"
                    
                    if len(type_groups) == 1:
                        table_name = info['table']
                    else:
                        table_name = f"  {info['table']}"  # Indent under type
                    
                    column_table.add_row(
                        table_name,
                        col_type if len(type_groups) == 1 else "",
                        f"[{nullable_style}]{nullable}[/{nullable_style}]",
                        f"[{pk_style}]{pk}[/{pk_style}]",
                        default,
                        f"{info['table_rows']:,}"
                    )
            
            console.print(column_table)
            
            # Summary statistics
            total_rows = sum(info['table_rows'] for info in column_info)
            primary_keys = sum(1 for info in column_info if info['primary_key'])
            nullable_count = sum(1 for info in column_info if info['nullable'])
            
            console.print(f"\n[dim]Summary: {len(column_info)} instances, {total_rows:,} total rows across all tables[/dim]")
            
            if primary_keys > 0:
                console.print(f"[dim]Primary key in {primary_keys} table(s)[/dim]")
            
            if nullable_count > 0:
                console.print(f"[dim]Nullable in {nullable_count} table(s)[/dim]")
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to analyze column '{column_name}': {e}")
            console.print(f"[red]Error analyzing column '{column_name}': {e}[/red]")
            return ""
    
    # ===== Comparative Analysis Operations =====
    
    def find_common_columns(self) -> str:
        """Find columns that appear in multiple tables.
        
        Returns:
            Formatted string with common columns analysis
        """
        try:
            if not self.sql_available:
                console.print("[red]SQLAlchemy not available - cannot find common columns[/red]")
                return ""
            
            tables = self.sql_inspector.get_tables()
            
            if len(tables) < 2:
                console.print("[yellow]Need at least 2 tables to find common columns[/yellow]")
                return ""
            
            # Collect all columns with their tables
            column_tables = {}
            
            for table in tables:
                columns = self.sql_inspector.get_columns(table)
                
                for col in columns:
                    col_name = col['name']
                    if col_name not in column_tables:
                        column_tables[col_name] = []
                    
                    column_tables[col_name].append({
                        'table': table,
                        'type': col['type'],
                        'nullable': col['nullable']
                    })
            
            # Find columns that appear in multiple tables
            common_columns = {
                name: info for name, info in column_tables.items() 
                if len(info) > 1
            }
            
            if not common_columns:
                console.print("[yellow]No columns found that appear in multiple tables[/yellow]")
                return ""
            
            # Create title panel
            title_panel = Panel(
                f"[bold cyan]Common Columns[/bold cyan]",
                subtitle=f"[dim]{len(common_columns)} columns found in multiple tables[/dim]"
            )
            console.print(title_panel)
            
            # Sort by number of occurrences (most common first)
            sorted_columns = sorted(
                common_columns.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )
            
            # Create table for common columns
            common_table = Table()
            common_table.add_column("Column", style="cyan")
            common_table.add_column("Tables", justify="right", style="dim")
            common_table.add_column("Type Consistency", justify="center")
            common_table.add_column("Tables Found In", style="dim")
            
            inconsistent_types = []
            potential_joins = []
            
            for col_name, occurrences in sorted_columns:
                # Check type consistency
                types = set(str(occ['type']) for occ in occurrences)
                type_consistent = len(types) == 1
                
                if type_consistent:
                    consistency = "[green]Consistent[/green]"
                    type_info = f"({list(types)[0]})"
                else:
                    consistency = "[red]Inconsistent[/red]"
                    type_info = f"({len(types)} types)"
                    inconsistent_types.append(col_name)
                
                # Check if potential join column
                if (len(occurrences) >= 2 and 
                    col_name.lower() in ['id', 'user_id', 'customer_id', 'order_id']):
                    potential_joins.append(col_name)
                
                tables_list = ", ".join(occ['table'] for occ in occurrences[:3])
                if len(occurrences) > 3:
                    tables_list += f", +{len(occurrences)-3} more"
                
                common_table.add_row(
                    col_name,
                    str(len(occurrences)),
                    f"{consistency} {type_info}",
                    tables_list
                )
            
            console.print(common_table)
            
            # Show detailed analysis for inconsistent types
            if inconsistent_types:
                console.print(f"\n[bold red]Type Inconsistencies:[/bold red]")
                
                detail_table = Table()
                detail_table.add_column("Column", style="cyan")
                detail_table.add_column("Table", style="yellow")
                detail_table.add_column("Data Type", style="magenta")
                detail_table.add_column("Nullable", justify="center")
                
                for col_name in inconsistent_types[:3]:  # Show first 3
                    occurrences = common_columns[col_name]
                    for i, occ in enumerate(occurrences):
                        nullable = "Yes" if occ['nullable'] else "No"
                        nullable_style = "dim" if nullable == "Yes" else "green"
                        
                        detail_table.add_row(
                            col_name if i == 0 else "",
                            occ['table'],
                            str(occ['type']),
                            f"[{nullable_style}]{nullable}[/{nullable_style}]"
                        )
                    
                    if col_name != inconsistent_types[-1] and len(inconsistent_types) > 1:
                        detail_table.add_row("", "", "", "")  # Separator
                
                console.print(detail_table)
            
            # Summary recommendations
            console.print(f"\n[bold magenta]Recommendations:[/bold magenta]")
            
            if inconsistent_types:
                console.print(f"• Consider standardizing types for: [yellow]{', '.join(inconsistent_types[:3])}[/yellow]")
                if len(inconsistent_types) > 3:
                    console.print(f"  and {len(inconsistent_types)-3} more columns")
            
            if potential_joins:
                console.print(f"• Potential join columns: [green]{', '.join(potential_joins[:3])}[/green]")
            
            high_frequency_cols = [name for name, occs in sorted_columns if len(occs) >= len(tables) * 0.7]
            if high_frequency_cols:
                console.print(f"• High-frequency columns (consider as schema standards): [cyan]{', '.join(high_frequency_cols[:3])}[/cyan]")
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to find common columns: {e}")
            console.print(f"[red]Error finding common columns: {e}[/red]")
            return ""
    
    def detect_type_mismatches(self) -> str:
        """Detect columns with inconsistent types across tables.
        
        Returns:
            Formatted string with type mismatch analysis
        """
        try:
            if not self.sql_available:
                console.print("[red]SQLAlchemy not available - cannot detect type mismatches[/red]")
                return ""
            
            tables = self.sql_inspector.get_tables()
            
            if len(tables) < 2:
                console.print("[yellow]Need at least 2 tables to detect type mismatches[/yellow]")
                return ""
            
            # Collect columns with same name across tables
            column_types = {}
            
            for table in tables:
                columns = self.sql_inspector.get_columns(table)
                
                for col in columns:
                    col_name = col['name']
                    col_type = str(col['type'])
                    
                    if col_name not in column_types:
                        column_types[col_name] = {}
                    
                    if col_type not in column_types[col_name]:
                        column_types[col_name][col_type] = []
                    
                    column_types[col_name][col_type].append(table)
            
            # Find mismatches (columns with multiple types)
            mismatches = {
                name: types for name, types in column_types.items() 
                if len(types) > 1
            }
            
            if not mismatches:
                console.print("[green]No type mismatches found! All common columns have consistent types.[/green] ✨")
                return ""
            
            # Create title panel
            title_panel = Panel(
                f"[bold red]Type Mismatches Found[/bold red]",
                subtitle=f"[dim]{len(mismatches)} columns with inconsistent types[/dim]",
                style="red"
            )
            console.print(title_panel)
            
            # Create table for mismatches
            mismatch_table = Table()
            mismatch_table.add_column("Column", style="cyan")
            mismatch_table.add_column("Data Type", style="magenta")
            mismatch_table.add_column("Tables Using This Type", style="dim")
            
            high_impact = []
            
            for col_name, type_tables in mismatches.items():
                # Check if high impact column
                if any(keyword in col_name.lower() for keyword in ['id', 'date', 'time', 'amount', 'price', 'count']):
                    high_impact.append(col_name)
                
                # Add rows for each type variant
                for i, (col_type, tables_with_type) in enumerate(type_tables.items()):
                    table_list = ', '.join(tables_with_type)
                    
                    # Show column name only on first row
                    column_display = col_name if i == 0 else ""
                    
                    mismatch_table.add_row(
                        column_display,
                        col_type,
                        table_list
                    )
                
                # Add separator between different columns
                if col_name != list(mismatches.keys())[-1]:
                    mismatch_table.add_row("", "", "")
            
            console.print(mismatch_table)
            
            # Show recommendations
            console.print(f"\n[bold magenta]Recommendations:[/bold magenta]")
            console.print("• Review data loading processes for type consistency")
            console.print("• Consider explicit type casting during data import")
            console.print("• Standardize column types across related tables")
            
            if high_impact:
                console.print(f"• [red]High priority columns to fix:[/red] [yellow]{', '.join(high_impact[:3])}[/yellow]")
                if len(high_impact) > 3:
                    console.print(f"  and {len(high_impact)-3} more critical columns")
            
            # Statistics
            total_variants = sum(len(types) for types in mismatches.values())
            console.print(f"\n[dim]Summary: {len(mismatches)} columns with {total_variants} total type variants[/dim]")
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to detect type mismatches: {e}")
            console.print(f"[red]Error detecting type mismatches: {e}[/red]")
            return ""
    
    def compare_two_files(self, file1: str, file2: str) -> str:
        """Compare schemas between two tables.
        
        Args:
            file1: Name of first table
            file2: Name of second table
            
        Returns:
            Formatted string with comparison results
        """
        try:
            if not self.sql_available:
                console.print(f"[red]SQLAlchemy not available - cannot compare '{file1}' and '{file2}'[/red]")
                return ""
            
            if not file1.strip() or not file2.strip():
                console.print("[red]Please provide both table names[/red]")
                return ""
            
            tables = self.sql_inspector.get_tables()
            
            if file1 not in tables:
                console.print(f"[red]Table '{file1}' not found[/red]")
                return ""
            
            if file2 not in tables:
                console.print(f"[red]Table '{file2}' not found[/red]")
                return ""
            
            # Get schemas for both tables
            columns1 = self.sql_inspector.get_columns(file1)
            columns2 = self.sql_inspector.get_columns(file2)
            stats1 = self.sql_inspector.get_table_stats(file1)
            stats2 = self.sql_inspector.get_table_stats(file2)
            
            # Create title panel
            title_panel = Panel(
                f"[bold cyan]Schema Comparison[/bold cyan]",
                subtitle=f"[dim]{file1} vs {file2}[/dim]"
            )
            console.print(title_panel)
            
            # Basic statistics comparison
            stats_table = Table()
            stats_table.add_column("Table", style="cyan")
            stats_table.add_column("Rows", justify="right", style="green")
            stats_table.add_column("Columns", justify="right", style="magenta")
            
            stats_table.add_row(
                file1,
                f"{stats1.get('row_count', 0):,}",
                str(len(columns1))
            )
            stats_table.add_row(
                file2,
                f"{stats2.get('row_count', 0):,}",
                str(len(columns2))
            )
            
            console.print(stats_table)
            
            # Column comparison
            cols1_dict = {col['name']: col for col in columns1}
            cols2_dict = {col['name']: col for col in columns2}
            
            all_columns = set(cols1_dict.keys()) | set(cols2_dict.keys())
            common_columns = set(cols1_dict.keys()) & set(cols2_dict.keys())
            only_in_1 = set(cols1_dict.keys()) - set(cols2_dict.keys())
            only_in_2 = set(cols2_dict.keys()) - set(cols1_dict.keys())
            
            # Column summary
            console.print(f"\n[bold magenta]Column Summary:[/bold magenta]")
            console.print(f"Common columns: [green]{len(common_columns)}[/green]")
            console.print(f"Only in {file1}: [yellow]{len(only_in_1)}[/yellow]")
            console.print(f"Only in {file2}: [blue]{len(only_in_2)}[/blue]")
            
            # Common columns analysis
            if common_columns:
                console.print(f"\n[bold green]Common Columns ({len(common_columns)}):[/bold green]")
                
                common_table = Table()
                common_table.add_column("Column", style="cyan")
                common_table.add_column(f"{file1} Type", style="magenta")
                common_table.add_column(f"{file2} Type", style="magenta")
                common_table.add_column("Match", justify="center")
                
                type_matches = 0
                for col_name in sorted(common_columns):
                    col1 = cols1_dict[col_name]
                    col2 = cols2_dict[col_name]
                    
                    type1 = str(col1['type'])
                    type2 = str(col2['type'])
                    
                    if type1 == type2:
                        match_status = "[green]Yes[/green]"
                        type_matches += 1
                    else:
                        match_status = "[red]No[/red]"
                    
                    common_table.add_row(col_name, type1, type2, match_status)
                
                console.print(common_table)
                console.print(f"[dim]Type consistency: {type_matches}/{len(common_columns)} columns match[/dim]")
            
            # Unique columns
            if only_in_1:
                console.print(f"\n[bold yellow]Only in {file1} ({len(only_in_1)}):[/bold yellow]")
                
                unique1_table = Table()
                unique1_table.add_column("Column", style="cyan")
                unique1_table.add_column("Type", style="magenta")
                
                for col_name in sorted(only_in_1):
                    col = cols1_dict[col_name]
                    unique1_table.add_row(col_name, str(col['type']))
                
                console.print(unique1_table)
            
            if only_in_2:
                console.print(f"\n[bold blue]Only in {file2} ({len(only_in_2)}):[/bold blue]")
                
                unique2_table = Table()
                unique2_table.add_column("Column", style="cyan")
                unique2_table.add_column("Type", style="magenta")
                
                for col_name in sorted(only_in_2):
                    col = cols2_dict[col_name]
                    unique2_table.add_row(col_name, str(col['type']))
                
                console.print(unique2_table)
            
            # Compatibility assessment
            console.print(f"\n[bold magenta]Compatibility Assessment:[/bold magenta]")
            
            if len(common_columns) == 0:
                console.print("[red]No common columns - tables are completely different[/red]")
            elif len(common_columns) == len(all_columns):
                if type_matches == len(common_columns):
                    console.print("[green]Schemas are identical[/green] ✨")
                else:
                    console.print("[yellow]Same columns but some type differences[/yellow]")
            else:
                compatibility = len(common_columns) / len(all_columns) * 100
                if compatibility >= 80:
                    console.print(f"[green]High compatibility ({compatibility:.1f}%)[/green]")
                elif compatibility >= 50:
                    console.print(f"[yellow]Moderate compatibility ({compatibility:.1f}%)[/yellow]")
                else:
                    console.print(f"[red]Low compatibility ({compatibility:.1f}%)[/red]")
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to compare '{file1}' and '{file2}': {e}")
            console.print(f"[red]Error comparing tables: {e}[/red]")
            return ""
    
    # ===== Status and Utility Methods =====
    
    def get_status(self) -> Dict[str, Any]:
        """Get analyzer status information.
        
        Returns:
            Dictionary with status information
        """
        return {
            'analyzer_type': 'SchemaAnalyzer',
            'database_path': str(self.database_path),
            'sqlalchemy_available': self.sql_available,
            'great_expectations_available': self.gx_available,
            'capabilities': self._get_capabilities()
        }
    
    def _get_capabilities(self) -> List[str]:
        """Get list of available capabilities.
        
        Returns:
            List of capability strings
        """
        capabilities = []
        
        if self.sql_available:
            capabilities.extend([
                'schema_introspection',
                'table_listing',
                'column_analysis',
                'type_detection',
                'constraint_analysis',
                'relationship_discovery'
            ])
        
        if self.gx_available:
            capabilities.extend([
                'data_quality_validation',
                'data_profiling',
                'expectation_management',
                'quality_scoring'
            ])
        
        return capabilities
    
    def close(self):
        """Clean up resources."""
        if self.sql_inspector:
            self.sql_inspector.close()
        
        self.logger.debug("Schema analyzer closed")


# ===== Factory Functions =====

def create_schema_analyzer(database_path: str) -> Optional[SchemaAnalyzer]:
    """Factory function to create schema analyzer.
    
    Args:
        database_path: Path to DuckDB database
        
    Returns:
        SchemaAnalyzer instance or None if creation fails
    """
    try:
        return SchemaAnalyzer(database_path)
    except Exception as e:
        logger = get_logger("tabletalk.schema_analyzer")
        logger.error(f"Failed to create schema analyzer: {e}")
        return None
