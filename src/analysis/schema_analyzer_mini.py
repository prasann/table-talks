"""Schema analyzer combining SQLAlchemy and Great Expectations."""

from typing import Dict, List, Optional, Any
from pathlib import Path
import functools

# Rich imports for beautiful terminal output
from rich.console import Console
from rich.panel import Panel

from src.utils.logger import get_logger
from src.metadata.sqlalchemy_inspector import create_inspector
from src.quality.expectations_analyzer import create_analyzer

# Initialize Rich console for output formatting
console = Console()


def handle_analyzer_errors(func):
    """A decorator to handle common exceptions and availability checks for analyzer methods."""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            # Check for SQLAlchemy availability for methods that need it
            if not self.sql_available and func.__name__ not in ['analyze_data_quality']:
                console.print(f"[red]SQLAlchemy not available - cannot perform '{func.__name__}'[/red]")
                return ""
            return func(self, *args, **kwargs)
        except Exception as e:
            self.logger.error(f"Failed to execute '{func.__name__}': {e}", exc_info=True)
            console.print(f"[red]An error occurred in {func.__name__}: {e}[/red]")
            return ""
    return wrapper


class SchemaAnalyzer:
    """Unified analyzer using SQLAlchemy + Great Expectations."""
    
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
    
    @handle_analyzer_errors
    def list_files(self) -> str:
        """List all available tables/files in the database."""
        tables = self.sql_inspector.get_tables()
        if not tables:
            console.print("[yellow]No tables found in the database[/yellow]")
            return ""

        console.print(Panel(f"[bold blue]Database Tables ({len(tables)} total)[/bold blue]", style="blue"))
        for table_name in tables:
            stats = self.sql_inspector.get_table_stats(table_name)
            console.print(f"- [cyan]{table_name}[/cyan]: {stats.get('column_count', 0)} columns, {stats.get('row_count', 0):,} rows")
        return ""
    
    @handle_analyzer_errors
    def get_file_schema(self, file_name: str) -> str:
        """Get detailed schema for a specific table."""
        if file_name not in self.sql_inspector.get_tables():
            console.print(f"[red]Table '{file_name}' not found[/red]")
            return ""

        columns = self.sql_inspector.get_columns(file_name)
        stats = self.sql_inspector.get_table_stats(file_name)
        
        console.print(Panel(f"[bold blue]Schema: {file_name}[/bold blue]", style="blue"))
        console.print(f"Rows: [green]{stats.get('row_count', 0):,}[/green], Columns: [magenta]{len(columns)}[/magenta]")

        for col in columns:
            constraints = []
            if col.get('primary_key'): constraints.append("PK")
            if col.get('default') is not None: constraints.append(f"DEFAULT {col['default']}")
            constraint_str = f" ([green]{', '.join(constraints)}[/green])" if constraints else ""
            nullable_str = "" if col['nullable'] else " [red]NOT NULL[/red]"
            console.print(f"- [cyan]{col['name']}[/cyan]: {col['type']}{nullable_str}{constraint_str}")
        
        foreign_keys = self.sql_inspector.get_foreign_keys(file_name)
        if foreign_keys:
            console.print("\n[bold blue]Foreign Keys:[/bold blue]")
            for fk in foreign_keys:
                console.print(f"  - {fk.get('constrained_columns')} -> {fk.get('referred_table')}({fk.get('referred_columns')})")
        return ""
    
    @handle_analyzer_errors
    def get_database_summary(self) -> str:
        """Get comprehensive database summary."""
        summary = self.sql_inspector.get_database_summary()
        if 'error' in summary:
            console.print(f"[red]Error generating database summary: {summary['error']}[/red]")
            return ""

        console.print(Panel("[bold blue]Database Summary[/bold blue]", style="blue"))
        console.print(f"Total tables: [green]{summary['total_tables']}[/green], Total rows: [yellow]{summary['total_rows']:,}[/yellow]")

        for name, info in summary.get('tables', {}).items():
            stats = info.get('stats', {})
            console.print(f"- [cyan]{name}[/cyan]: {stats.get('row_count', 0):,} rows, {len(info.get('columns', []))} cols")
        return ""
    
    # ===== Data Quality Operations =====
    
    @handle_analyzer_errors
    def analyze_data_quality(self) -> str:
        """Perform comprehensive data quality analysis."""
        if not self.gx_available:
            return self._basic_data_quality_analysis()
        
        try:
            analysis = self.expectations.analyze_data_quality()
            if 'error' in analysis:
                raise RuntimeError(analysis['error'])
        except Exception as gx_error:
            self.logger.warning(f"Great Expectations analysis failed: {gx_error}, falling back to basic analysis")
            return self._basic_data_quality_analysis()

        score = analysis.get('overall_quality_score', 0)
        color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
        console.print(Panel(f"[bold {color}]Data Quality Score: {score:.1f}%[/bold {color}]", style=color))

        for table, result in analysis.get('tables_analyzed', {}).items():
            if 'validation' in result:
                t_score = result['validation'].get('data_quality_score', 0)
                console.print(f"- [cyan]{table}[/cyan]: {t_score:.1f}%")
        return ""
    
    def _basic_data_quality_analysis(self) -> str:
        """Perform basic data quality analysis using SQLAlchemy only."""
        if not self.sql_available:
            console.print("[red]SQLAlchemy not available - data quality analysis disabled[/red]")
            return ""
        
        console.print(Panel("[bold blue]Basic Data Quality Analysis[/bold blue]", style="blue"))
        tables = self.sql_inspector.get_tables()
        total_issues = 0

        for table_name in tables:
            issues = []
            columns = self.sql_inspector.get_columns(table_name)
            row_count = self.sql_inspector.get_table_stats(table_name).get('row_count', 0)

            if row_count == 0:
                issues.append("Table is empty")
            else:
                with self.sql_inspector.engine.connect() as conn:
                    for col in columns:
                        non_null_count = conn.execute(f"SELECT COUNT({col['name']}) FROM {table_name}").scalar()
                        if non_null_count == 0:
                            issues.append(f"Column '{col['name']}' is all NULLs")
            
            if issues:
                console.print(f"- [cyan]{table_name}[/cyan]: [red]{len(issues)} issues found[/red] ({', '.join(issues[:2])})")
                total_issues += len(issues)

        if total_issues == 0:
            console.print("[green]No basic data quality issues found.[/green] ✨")
        return ""
    
    # ===== Column Analysis Operations =====
    
    @handle_analyzer_errors
    def search_columns(self, search_term: str) -> str:
        """Search for columns containing a specific term."""
        if not search_term.strip():
            console.print("[red]Please provide a search term[/red]")
            return ""
        
        matches = []
        for table in self.sql_inspector.get_tables():
            for col in self.sql_inspector.get_columns(table):
                if search_term.lower() in col['name'].lower():
                    matches.append(f"- [cyan]{table}[/cyan].[bright_cyan]{col['name']}[/bright_cyan] ({col['type']})")
        
        console.print(Panel(f"[bold blue]Column Search Results for '{search_term}'[/bold blue]", style="blue"))
        if matches:
            for match in matches:
                console.print(match)
        else:
            console.print(f"[yellow]No columns found containing '{search_term}'[/yellow]")
        return ""
    
    @handle_analyzer_errors
    def get_column_data_types(self, column_name: str) -> str:
        """Get data types for a column across all tables."""
        if not column_name.strip():
            console.print("[red]Please provide a column name[/red]")
            return ""

        column_info = []
        for table in self.sql_inspector.get_tables():
            for col in self.sql_inspector.get_columns(table):
                if col['name'].lower() == column_name.lower():
                    column_info.append(f"- [cyan]{table}[/cyan]: {col['type']}")

        console.print(Panel(f"[bold blue]Data Type Analysis for '{column_name}'[/bold blue]", style="blue"))
        if column_info:
            for info in column_info:
                console.print(info)
        else:
            console.print(f"[yellow]Column '{column_name}' not found in any table[/yellow]")
        return ""
    
    # ===== Comparative Analysis Operations =====
    
    @handle_analyzer_errors
    def analyze_column_consistency(self) -> str:
        """Find common columns and detect type mismatches across all tables."""
        tables = self.sql_inspector.get_tables()
        if len(tables) < 2:
            console.print("[yellow]Need at least 2 tables to analyze column consistency[/yellow]")
            return ""

        column_map = {}
        for table in tables:
            for col in self.sql_inspector.get_columns(table):
                if col['name'] not in column_map:
                    column_map[col['name']] = {}
                col_type = str(col['type'])
                if col_type not in column_map[col['name']]:
                    column_map[col['name']][col_type] = []
                column_map[col['name']][col_type].append(table)

        common_columns = {k: v for k, v in column_map.items() if sum(len(tables) for tables in v.values()) > 1}
        mismatches = {k: v for k, v in common_columns.items() if len(v) > 1}

        console.print(Panel("[bold blue]Column Consistency Analysis[/bold blue]", style="blue"))
        console.print(f"Found [green]{len(common_columns)}[/green] common columns and [red]{len(mismatches)}[/red] with type mismatches.")

        if mismatches:
            console.print("\n[bold red]Type Mismatches:[/bold red]")
            for name, types in list(mismatches.items())[:5]: # Limit output
                console.print(f"- [cyan]{name}[/cyan]:")
                for type_name, tables_using in types.items():
                    console.print(f"  - [magenta]{type_name}[/magenta] in tables: {', '.join(tables_using)}")
        return ""

    @handle_analyzer_errors
    def compare_two_files(self, file1: str, file2: str) -> str:
        """Compare schemas between two tables."""
        if not all([file1.strip(), file2.strip(), file1 in self.sql_inspector.get_tables(), file2 in self.sql_inspector.get_tables()]):
            console.print(f"[red]One or both tables not found. Ensure both '{file1}' and '{file2}' exist.[/red]")
            return ""

        cols1 = {c['name']: c for c in self.sql_inspector.get_columns(file1)}
        cols2 = {c['name']: c for c in self.sql_inspector.get_columns(file2)}
        
        common = set(cols1.keys()) & set(cols2.keys())
        only_in_1 = set(cols1.keys()) - set(cols2.keys())
        only_in_2 = set(cols2.keys()) - set(cols1.keys())

        console.print(Panel(f"[bold blue]Comparing [cyan]{file1}[/cyan] and [cyan]{file2}[/cyan][/bold blue]", style="blue"))
        console.print(f"Common Columns: [green]{len(common)}[/green]")
        console.print(f"Only in [cyan]{file1}[/cyan]: [yellow]{len(only_in_1)}[/yellow] ({', '.join(list(only_in_1)[:3])})")
        console.print(f"Only in [cyan]{file2}[/cyan]: [yellow]{len(only_in_2)}[/yellow] ({', '.join(list(only_in_2)[:3])})")

        if common:
            mismatches = sum(1 for c in common if str(cols1[c]['type']) != str(cols2[c]['type']))
            if mismatches:
                console.print(f"Type Mismatches in common columns: [red]{mismatches}[/red]")
            else:
                console.print("[green]Common columns have consistent types.[/green]")
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
