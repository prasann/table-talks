"""Schema analyzer combining SQLAlchemy and Great Expectations - Refactored with Templates."""

from typing import Dict, List, Optional, Any
from pathlib import Path

from src.utils.logger import get_logger
from src.metadata.sqlalchemy_inspector import SQLAlchemyInspector, create_inspector
from src.quality.expectations_analyzer import ExpectationsAnalyzer, create_analyzer
from .formatter import create_formatter


class SchemaAnalyzer:
    """Unified analyzer using SQLAlchemy + Great Expectations.
    
    Combines the power of SQLAlchemy's database introspection with
    Great Expectations' data quality validation capabilities to provide
    comprehensive schema analysis and data quality assessment.
    
    Now uses template-based formatting for cleaner, more maintainable code.
    """
    
    def __init__(self, database_path: str):
        """Initialize the schema analyzer.
        
        Args:
            database_path: Path to DuckDB database file
        """
        self.database_path = Path(database_path)
        self.logger = get_logger("tabletalk.schema_analyzer")
        
        # Initialize formatter
        self.formatter = create_formatter()
        
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
                return self.formatter.format_message("errors", "sql_unavailable", operation="cannot list tables")
            
            tables = self.sql_inspector.get_tables()
            
            # Prepare data for template
            table_data = []
            for table_name in tables:
                columns = self.sql_inspector.get_columns(table_name)
                stats = self.sql_inspector.get_table_stats(table_name)
                
                # Create sample columns string
                col_names = [col['name'] for col in columns[:3]]
                if len(columns) > 3:
                    col_names.append(f"... +{len(columns) - 3} more")
                sample_cols = ", ".join(col_names) if col_names else "None"
                
                table_data.append({
                    'name': table_name,
                    'columns': len(columns),
                    'rows': stats.get('row_count', 0),
                    'sample_cols': sample_cols
                })
            
            # Format using template
            return self.formatter.format_table("table_list", {
                'total_count': len(tables),
                'items': table_data
            })
            
        except Exception as e:
            self.logger.error(f"Failed to list files: {e}")
            return self.formatter.format_message("errors", "general_error", operation="listing tables", error=str(e))
    
    def search_columns(self, search_term: str) -> str:
        """Search for columns containing a specific term.
        
        Args:
            search_term: Term to search for in column names
            
        Returns:
            Formatted string with search results
        """
        try:
            if not self.sql_available:
                return self.formatter.format_message("errors", "sql_unavailable", 
                                                   operation=f"cannot search columns for '{search_term}'")
            
            if not search_term.strip():
                return self.formatter.format_message("errors", "search_term_required")
            
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
            
            # Format using template
            return self.formatter.format_table("column_search", {
                'search_term': search_term,
                'count': len(matches),
                'items': matches
            })
            
        except Exception as e:
            self.logger.error(f"Failed to search columns for '{search_term}': {e}")
            return self.formatter.format_message("errors", "general_error", 
                                               operation="searching columns", error=str(e))
    
    def get_file_schema(self, file_name: str) -> str:
        """Get detailed schema for a specific table.
        
        Args:
            file_name: Name of the table to analyze
            
        Returns:
            Formatted string with schema details
        """
        try:
            if not self.sql_available:
                return self.formatter.format_message("errors", "sql_unavailable", 
                                                   operation=f"cannot get schema for '{file_name}'")
            
            tables = self.sql_inspector.get_tables()
            if file_name not in tables:
                return self.formatter.format_message("errors", "file_not_found", file_name=file_name)
            
            # Get schema information
            columns = self.sql_inspector.get_columns(file_name)
            stats = self.sql_inspector.get_table_stats(file_name)
            indexes = self.sql_inspector.get_indexes(file_name)
            constraints = self.sql_inspector.get_constraints(file_name)
            
            # Prepare data for template
            column_data = []
            for col in columns:
                col_info = {
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col['nullable'],
                    'default': col.get('default', 'None'),
                    'constraints_str': ''  # We'll add constraints info if needed
                }
                column_data.append(col_info)
            
            # Format header panel
            self.formatter.format_panel("schema_detail", "panel", {
                'file_name': file_name,
                'table_name': file_name,
                'total_columns': len(columns)
            })
            
            # Format stats
            self.formatter.format_stats("schema_detail", {
                'row_count': stats.get('row_count', 'Unknown'),
                'col_count': len(columns),
                'column_count': len(columns),
                'size_mb': 0.0  # DuckDB doesn't provide file size easily
            })
            
            # Format columns table
            self.formatter.format_table("schema_detail", {
                'template_key': 'columns_table',
                'file_name': file_name,
                'items': column_data
            })
            
            # Format additional sections
            sections_data = {}
            
            if indexes:
                sections_data['indexes'] = [{'name': idx.get('name', 'unnamed'), 
                                          'columns': ', '.join(idx.get('column_names', []))} 
                                         for idx in indexes]
            
            if constraints:
                # Process constraints dictionary properly
                constraint_items = []
                for constraint_type, constraint_list in constraints.items():
                    if constraint_list:  # Only add if there are constraints of this type
                        for constraint in constraint_list:
                            constraint_items.append({
                                'type': constraint_type.replace('_', ' ').title(),
                                'details': str(constraint)
                            })
                
                if constraint_items:
                    sections_data['constraints'] = constraint_items
            
            if sections_data:
                self.formatter.format_sections("schema_detail", {'sections': sections_data})
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to get schema for '{file_name}': {e}")
            return self.formatter.format_message("errors", "general_error", 
                                               operation="getting schema", error=str(e))
    
    def get_database_summary(self) -> str:
        """Get comprehensive database summary.
        
        Returns:
            Formatted string with database overview
        """
        try:
            if not self.sql_available:
                return self.formatter.format_message("errors", "sql_unavailable", 
                                                   operation="cannot get database summary")
            
            tables = self.sql_inspector.get_tables()
            
            if not tables:
                return self.formatter.format_message("warnings", "no_tables")
            
            # Collect summary data
            total_tables = len(tables)
            total_columns = 0
            total_rows = 0
            table_summaries = []
            
            for table_name in tables:
                try:
                    columns = self.sql_inspector.get_columns(table_name)
                    stats = self.sql_inspector.get_table_stats(table_name)
                    
                    col_count = len(columns)
                    row_count = stats.get('row_count', 0)
                    
                    total_columns += col_count
                    total_rows += row_count
                    
                    # Get column type summary
                    type_counts = {}
                    for col in columns:
                        col_type = str(col['type']).upper()
                        type_counts[col_type] = type_counts.get(col_type, 0) + 1
                    
                    # Create summary string for common types
                    type_summary = []
                    for col_type, count in sorted(type_counts.items()):
                        if count > 1:
                            type_summary.append(f"{col_type}({count})")
                        else:
                            type_summary.append(col_type)
                    
                    table_summaries.append({
                        'name': table_name,
                        'columns': col_count,
                        'rows': row_count,
                        'types': ', '.join(type_summary[:3]) + ('...' if len(type_summary) > 3 else '')
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Failed to get stats for table '{table_name}': {e}")
                    table_summaries.append({
                        'name': table_name,
                        'columns': 0,
                        'rows': 0,
                        'types': 'Error'
                    })
            
            # Format header panel
            self.formatter.format_panel("database_summary", "header", {
                'database_path': str(self.database_path.name)
            })
            
            # Format stats
            self.formatter.format_stats("database_summary", {
                'total_tables': total_tables,
                'total_columns': total_columns,
                'total_rows': total_rows
            })
            
            # Format tables summary
            self.formatter.format_table("database_summary", {
                'template_key': 'tables_table',
                'items': table_summaries
            })
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to get database summary: {e}")
            return self.formatter.format_message("errors", "general_error", 
                                               operation="getting database summary", error=str(e))
    
    def analyze_data_quality(self) -> str:
        """Perform comprehensive data quality analysis.
        
        Returns:
            Formatted string with data quality results
        """
        try:
            if not self.gx_available:
                return self.formatter.format_message("errors", "gx_unavailable", 
                                                   operation="cannot analyze data quality")
            
            # Get list of tables
            tables = []
            if self.sql_available:
                tables = self.sql_inspector.get_tables()
            else:
                # Fallback: try to get tables from Great Expectations
                try:
                    tables = list(self.expectations.get_available_tables())
                except:
                    pass
            
            if not tables:
                return self.formatter.format_message("warnings", "no_tables")
            
            # Analyze each table
            table_results = []
            total_issues = 0
            
            for table_name in tables:
                try:
                    result = self.expectations.analyze_table_quality(table_name)
                    
                    if 'error' not in result:
                        issues = result.get('issues', [])
                        total_issues += len(issues)
                    
                    table_results.append(result)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to analyze table '{table_name}': {e}")
                    table_results.append({
                        'name': table_name,
                        'error': str(e)
                    })
            
            # Calculate overall score
            valid_results = [r for r in table_results if 'error' not in r]
            if valid_results:
                scores = [r.get('quality_score', 0) for r in valid_results]
                overall_score = sum(scores) / len(scores)
            else:
                overall_score = 0
            
            # Format using template
            return self.formatter.format_data_quality_basic({
                'score': overall_score,
                'total_tables': len(tables),
                'total_issues': total_issues,
                'table_results': table_results
            })
            
        except Exception as e:
            self.logger.error(f"Failed to analyze data quality: {e}")
            return self.formatter.format_message("errors", "general_error", 
                                               operation="analyzing data quality", error=str(e))
    
    def get_column_data_types(self, column_name: str) -> str:
        """Get data types for a column across all tables.
        
        Args:
            column_name: Name of the column to analyze
            
        Returns:
            Formatted string with column type analysis
        """
        try:
            if not self.sql_available:
                return self.formatter.format_message("errors", "sql_unavailable", 
                                                   operation=f"cannot analyze column '{column_name}'")
            
            if not column_name.strip():
                return self.formatter.format_message("errors", "column_name_required")
            
            tables = self.sql_inspector.get_tables()
            matches = []
            
            for table in tables:
                columns = self.sql_inspector.get_columns(table)
                
                for col in columns:
                    if col['name'].lower() == column_name.lower():
                        matches.append({
                            'table': table,
                            'column': col['name'],
                            'type': str(col['type']),
                            'nullable': 'Yes' if col['nullable'] else 'No',
                            'default': col.get('default', 'None')
                        })
            
            if not matches:
                return self.formatter.format_message("warnings", "column_not_found", column_name=column_name)
            
            # Analyze type consistency
            types = [match['type'] for match in matches]
            unique_types = list(set(types))
            consistent = len(unique_types) == 1
            
            # Format header panel with consistency info
            if consistent:
                panel_key = 'header_consistent'
            else:
                panel_key = 'header_inconsistent'
            
            self.formatter.format_panel("column_types", panel_key, {
                'column_name': column_name,
                'table_count': len(matches),
                'type_count': len(unique_types)
            })
            
            # Format table with results
            self.formatter.format_table("column_types", {
                'column_name': column_name,
                'items': matches
            })
            
            # Show type summary if inconsistent
            if not consistent:
                type_counts = {}
                for col_type in types:
                    type_counts[col_type] = type_counts.get(col_type, 0) + 1
                
                self.formatter.format_message("warnings", "type_inconsistency", 
                                           column_name=column_name)
                
                for col_type, count in type_counts.items():
                    self.formatter.format_message("info", "type_count", 
                                                type=col_type, count=count)
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to analyze column '{column_name}': {e}")
            return self.formatter.format_message("errors", "general_error", 
                                               operation="analyzing column types", error=str(e))
    
    def find_common_columns(self) -> str:
        """Find columns that appear in multiple tables.
        
        Returns:
            Formatted string with common columns analysis
        """
        try:
            if not self.sql_available:
                return self.formatter.format_message("errors", "sql_unavailable", 
                                                   operation="cannot find common columns")
            
            tables = self.sql_inspector.get_tables()
            
            if len(tables) < 2:
                return self.formatter.format_message("warnings", "insufficient_tables", 
                                                   operation="find common columns")
            
            # Collect all columns with their table associations
            column_tables = {}  # {column_name: [table1, table2, ...]}
            
            for table in tables:
                columns = self.sql_inspector.get_columns(table)
                
                for col in columns:
                    col_name = col['name'].lower()
                    if col_name not in column_tables:
                        column_tables[col_name] = []
                    column_tables[col_name].append({
                        'table': table,
                        'type': str(col['type']),
                        'nullable': col['nullable']
                    })
            
            # Find columns appearing in multiple tables
            common_columns = []
            for col_name, table_list in column_tables.items():
                if len(table_list) > 1:
                    # Check type consistency
                    types = [item['type'] for item in table_list]
                    unique_types = list(set(types))
                    consistent = len(unique_types) == 1
                    
                    common_columns.append({
                        'column': col_name,
                        'table_count': len(table_list),
                        'tables': ', '.join([item['table'] for item in table_list]),
                        'types': ', '.join(unique_types),
                        'consistent': 'Yes' if consistent else 'No'
                    })
            
            if not common_columns:
                return self.formatter.format_message("info", "no_common_columns")
            
            # Sort by frequency (most common first)
            common_columns.sort(key=lambda x: x['table_count'], reverse=True)
            
            # Format header panel
            self.formatter.format_panel("common_columns", "header", {
                'total_columns': len(common_columns),
                'total_tables': len(tables)
            })
            
            # Format results table
            self.formatter.format_table("common_columns", {
                'items': common_columns
            })
            
            # Show type inconsistency warnings
            inconsistent = [col for col in common_columns if col['consistent'] == 'No']
            if inconsistent:
                self.formatter.format_message("warnings", "type_inconsistencies", 
                                           count=len(inconsistent))
                
                for col in inconsistent[:3]:  # Show first 3
                    self.formatter.format_message("warnings", "inconsistent_column", 
                                                column=col['column'], types=col['types'])
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to find common columns: {e}")
            return self.formatter.format_message("errors", "general_error", 
                                               operation="finding common columns", error=str(e))
    
    def detect_type_mismatches(self) -> str:
        """Detect columns with inconsistent types across tables.
        
        Returns:
            Formatted string with type mismatch analysis
        """
        try:
            if not self.sql_available:
                return self.formatter.format_message("errors", "sql_unavailable", 
                                                   operation="cannot detect type mismatches")
            
            tables = self.sql_inspector.get_tables()
            
            if len(tables) < 2:
                return self.formatter.format_message("warnings", "insufficient_tables", 
                                                   operation="detect type mismatches")
            
            # Collect columns with their types
            column_types = {}  # {column_name: {table: type}}
            
            for table in tables:
                columns = self.sql_inspector.get_columns(table)
                
                for col in columns:
                    col_name = col['name'].lower()
                    if col_name not in column_types:
                        column_types[col_name] = {}
                    column_types[col_name][table] = str(col['type'])
            
            # Find mismatches
            mismatches = []
            for col_name, table_types in column_types.items():
                if len(table_types) > 1:  # Column appears in multiple tables
                    unique_types = set(table_types.values())
                    if len(unique_types) > 1:  # Different types found
                        # Create detailed breakdown
                        type_details = []
                        for table, col_type in table_types.items():
                            type_details.append(f"{table}: {col_type}")
                        
                        mismatches.append({
                            'column': col_name,
                            'table_count': len(table_types),
                            'type_count': len(unique_types),
                            'details': '; '.join(type_details)
                        })
            
            if not mismatches:
                return self.formatter.format_message("info", "no_type_mismatches")
            
            # Sort by severity (more tables = more problematic)
            mismatches.sort(key=lambda x: x['table_count'], reverse=True)
            
            # Format header panel
            self.formatter.format_panel("type_mismatches", "panel", {
                'count': len(mismatches),
                'mismatch_count': len(mismatches),
                'total_tables': len(tables)
            })
            
            # Format results table
            self.formatter.format_table("type_mismatches", {
                'items': mismatches,
                'template_key': 'table'
            })
            
            # Show recommendations
            self.formatter.format_message("info", "type_mismatch_recommendations")
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to detect type mismatches: {e}")
            return self.formatter.format_message("errors", "general_error", 
                                               operation="detecting type mismatches", error=str(e))
    
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
                return self.formatter.format_message("errors", "sql_unavailable", 
                                                   operation=f"cannot compare '{file1}' and '{file2}'")
            
            tables = self.sql_inspector.get_tables()
            
            if file1 not in tables:
                return self.formatter.format_message("errors", "file_not_found", file_name=file1)
            
            if file2 not in tables:
                return self.formatter.format_message("errors", "file_not_found", file_name=file2)
            
            # Get schema information for both tables
            cols1 = self.sql_inspector.get_columns(file1)
            cols2 = self.sql_inspector.get_columns(file2)
            stats1 = self.sql_inspector.get_table_stats(file1)
            stats2 = self.sql_inspector.get_table_stats(file2)
            
            # Create column lookups
            cols1_dict = {col['name'].lower(): col for col in cols1}
            cols2_dict = {col['name'].lower(): col for col in cols2}
            
            # Find differences
            only_in_file1 = []
            only_in_file2 = []
            common_columns = []
            type_differences = []
            
            all_columns = set(cols1_dict.keys()) | set(cols2_dict.keys())
            
            for col_name in sorted(all_columns):
                if col_name in cols1_dict and col_name in cols2_dict:
                    # Common column
                    col1 = cols1_dict[col_name]
                    col2 = cols2_dict[col_name]
                    
                    type1 = str(col1['type'])
                    type2 = str(col2['type'])
                    
                    if type1 == type2:
                        common_columns.append({
                            'column': col_name,
                            'type': type1,
                            'nullable1': 'Yes' if col1['nullable'] else 'No',
                            'nullable2': 'Yes' if col2['nullable'] else 'No'
                        })
                    else:
                        type_differences.append({
                            'column': col_name,
                            'type1': type1,
                            'type2': type2,
                            'nullable1': 'Yes' if col1['nullable'] else 'No',
                            'nullable2': 'Yes' if col2['nullable'] else 'No'
                        })
                        
                elif col_name in cols1_dict:
                    # Only in file1
                    col = cols1_dict[col_name]
                    only_in_file1.append({
                        'column': col_name,
                        'type': str(col['type']),
                        'nullable': 'Yes' if col['nullable'] else 'No'
                    })
                else:
                    # Only in file2
                    col = cols2_dict[col_name]
                    only_in_file2.append({
                        'column': col_name,
                        'type': str(col['type']),
                        'nullable': 'Yes' if col['nullable'] else 'No'
                    })
            
            # Format header panel
            self.formatter.format_panel("file_comparison", "header", {
                'file1': file1,
                'file2': file2
            })
            
            # Format stats comparison
            self.formatter.format_stats("file_comparison", {
                'rows1': stats1.get('row_count', 'Unknown'),
                'rows2': stats2.get('row_count', 'Unknown'),
                'cols1': len(cols1),
                'cols2': len(cols2)
            })
            
            # Format common columns
            if common_columns:
                self.formatter.format_table("file_comparison", {
                    'template_key': 'common_table',
                    'file1': file1,
                    'file2': file2,
                    'items': common_columns
                })
            
            # Format type differences
            if type_differences:
                self.formatter.format_table("file_comparison", {
                    'template_key': 'differences_table',
                    'file1': file1,
                    'file2': file2,
                    'items': type_differences
                })
            
            # Format unique columns
            sections_data = {}
            
            if only_in_file1:
                sections_data['unique_file1'] = only_in_file1
            
            if only_in_file2:
                sections_data['unique_file2'] = only_in_file2
            
            if sections_data:
                self.formatter.format_sections("file_comparison", {
                    'file1': file1,
                    'file2': file2,
                    'sections': sections_data
                })
            
            # Summary message
            if not type_differences and not only_in_file1 and not only_in_file2:
                self.formatter.format_message("info", "identical_schemas", 
                                           file1=file1, file2=file2)
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to compare '{file1}' and '{file2}': {e}")
            return self.formatter.format_message("errors", "general_error", 
                                               operation="comparing files", error=str(e))
    
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
