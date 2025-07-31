"""Schema analyzer combining SQLAlchemy and Great Expectations."""

import os
import sys
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

# Ensure src is in Python path for consistent imports
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from utils.logger import get_logger
from metadata.sqlalchemy_inspector import SQLAlchemyInspector, create_inspector
from quality.expectations_analyzer import ExpectationsAnalyzer, create_analyzer


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
                return "❌ SQLAlchemy not available - cannot list tables"
            
            tables = self.sql_inspector.get_tables()
            
            if not tables:
                return "📋 No tables found in the database."
            
            result = f"📋 **Available Tables ({len(tables)} total):**\n\n"
            
            for i, table in enumerate(tables, 1):
                # Get basic table info
                columns = self.sql_inspector.get_columns(table)
                stats = self.sql_inspector.get_table_stats(table)
                
                result += f"{i}. **{table}**\n"
                result += f"   - Columns: {len(columns)}\n"
                result += f"   - Rows: {stats.get('row_count', 'Unknown')}\n"
                
                # Show first few column names
                if columns:
                    col_names = [col['name'] for col in columns[:3]]
                    if len(columns) > 3:
                        col_names.append(f"... and {len(columns) - 3} more")
                    result += f"   - Sample columns: {', '.join(col_names)}\n"
                
                result += "\n"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to list files: {e}")
            return f"❌ Error listing tables: {e}"
    
    def get_file_schema(self, file_name: str) -> str:
        """Get detailed schema for a specific table.
        
        Args:
            file_name: Name of the table
            
        Returns:
            Formatted string with detailed schema information
        """
        try:
            if not self.sql_available:
                return f"❌ SQLAlchemy not available - cannot get schema for '{file_name}'"
            
            # Check if table exists
            tables = self.sql_inspector.get_tables()
            if file_name not in tables:
                available = ", ".join(tables) if tables else "none"
                return f"❌ Table '{file_name}' not found. Available tables: {available}"
            
            # Get comprehensive schema information
            columns = self.sql_inspector.get_columns(file_name)
            primary_keys = self.sql_inspector.get_primary_keys(file_name)
            foreign_keys = self.sql_inspector.get_foreign_keys(file_name)
            indexes = self.sql_inspector.get_indexes(file_name)
            stats = self.sql_inspector.get_table_stats(file_name)
            
            result = f"📊 **Schema for table: {file_name}**\n\n"
            
            # Basic statistics
            result += "**📈 Table Statistics:**\n"
            result += f"- Rows: {stats.get('row_count', 'Unknown')}\n"
            result += f"- Columns: {len(columns)}\n"
            result += f"- Estimated size: {stats.get('estimated_size_bytes', 0):,} bytes\n\n"
            
            # Column details
            result += "**📋 Columns:**\n"
            for i, col in enumerate(columns, 1):
                result += f"{i:2d}. **{col['name']}**\n"
                result += f"    - Type: {col['type']}\n"
                result += f"    - Nullable: {'Yes' if col['nullable'] else 'No'}\n"
                
                if col.get('primary_key'):
                    result += f"    - 🔑 Primary Key\n"
                
                if col.get('default') is not None:
                    result += f"    - Default: {col['default']}\n"
                
                result += "\n"
            
            # Primary keys
            if primary_keys:
                result += f"**🔑 Primary Keys:** {', '.join(primary_keys)}\n\n"
            
            # Foreign keys
            if foreign_keys:
                result += "**🔗 Foreign Keys:**\n"
                for fk in foreign_keys:
                    constrained_cols = ', '.join(fk.get('constrained_columns', []))
                    referred_table = fk.get('referred_table', 'unknown')
                    referred_cols = ', '.join(fk.get('referred_columns', []))
                    result += f"- {constrained_cols} → {referred_table}({referred_cols})\n"
                result += "\n"
            
            # Indexes
            if indexes:
                result += "**📇 Indexes:**\n"
                for idx in indexes:
                    idx_name = idx.get('name', 'unnamed')
                    idx_cols = ', '.join(idx.get('column_names', []))
                    unique_str = " (UNIQUE)" if idx.get('unique') else ""
                    result += f"- {idx_name}: {idx_cols}{unique_str}\n"
                result += "\n"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get schema for '{file_name}': {e}")
            return f"❌ Error getting schema for '{file_name}': {e}"
    
    def get_database_summary(self) -> str:
        """Get comprehensive database summary.
        
        Returns:
            Formatted string with database-wide statistics
        """
        try:
            if not self.sql_available:
                return "❌ SQLAlchemy not available - cannot generate database summary"
            
            summary = self.sql_inspector.get_database_summary()
            
            if 'error' in summary:
                return f"❌ Error generating database summary: {summary['error']}"
            
            result = "🗃️ **Database Summary**\n\n"
            
            # Overall statistics
            result += "**📊 Overall Statistics:**\n"
            result += f"- Database: {summary['database_path']}\n"
            result += f"- Total tables: {summary['total_tables']}\n"
            result += f"- Total rows: {summary['total_rows']:,}\n"
            result += f"- Total columns: {summary['total_columns']}\n\n"
            
            # Table-by-table breakdown
            if summary['tables']:
                result += "**📋 Tables Breakdown:**\n"
                
                for table_name, table_info in summary['tables'].items():
                    stats = table_info.get('stats', {})
                    columns = table_info.get('columns', [])
                    
                    result += f"- **{table_name}**\n"
                    result += f"  - Rows: {stats.get('row_count', 0):,}\n"
                    result += f"  - Columns: {len(columns)}\n"
                    
                    # Show data types distribution
                    type_counts = {}
                    for col in columns:
                        col_type = str(col.get('type', 'unknown')).split('(')[0]  # Remove length info
                        type_counts[col_type] = type_counts.get(col_type, 0) + 1
                    
                    if type_counts:
                        types_str = ', '.join([f"{t}({c})" for t, c in type_counts.items()])
                        result += f"  - Types: {types_str}\n"
                    
                    result += "\n"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate database summary: {e}")
            return f"❌ Error generating database summary: {e}"
    
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
            
            result = "🔍 **Data Quality Analysis**\n\n"
            
            # Overall quality score
            overall_score = analysis.get('overall_quality_score', 0)
            score_emoji = "🟢" if overall_score >= 80 else "🟡" if overall_score >= 60 else "🔴"
            result += f"**{score_emoji} Overall Quality Score: {overall_score:.1f}%**\n\n"
            
            # Summary statistics
            total_tables = analysis.get('total_tables', 0)
            result += f"📊 **Summary:**\n"
            result += f"- Tables analyzed: {total_tables}\n"
            
            # Issues summary
            issues = analysis.get('issues_summary', [])
            if issues:
                result += f"- Total issues found: {len(issues)}\n\n"
                
                result += "⚠️ **Issues Found:**\n"
                for i, issue in enumerate(issues[:10], 1):  # Show first 10 issues
                    result += f"{i}. {issue}\n"
                
                if len(issues) > 10:
                    result += f"... and {len(issues) - 10} more issues\n"
                result += "\n"
            else:
                result += "- No issues found! 🎉\n\n"
            
            # Table-by-table quality scores
            tables_analyzed = analysis.get('tables_analyzed', {})
            if tables_analyzed:
                result += "📋 **Quality by Table:**\n"
                
                for table_name, table_analysis in tables_analyzed.items():
                    if 'error' in table_analysis:
                        result += f"- **{table_name}**: ❌ Analysis failed\n"
                        continue
                    
                    validation = table_analysis.get('validation', {})
                    quality_score = validation.get('data_quality_score', 0)
                    
                    score_emoji = "🟢" if quality_score >= 80 else "🟡" if quality_score >= 60 else "🔴"
                    result += f"- **{table_name}**: {score_emoji} {quality_score:.1f}%\n"
                    
                    # Show key metrics
                    profile = table_analysis.get('profile', {})
                    if profile and 'error' not in profile:
                        result += f"  - Rows: {profile.get('row_count', 0):,}\n"
                        result += f"  - Columns: {profile.get('column_count', 0)}\n"
                    
                    # Show specific issues for this table
                    failed_expectations = validation.get('failed_expectations', [])
                    if failed_expectations:
                        result += f"  - Issues: {len(failed_expectations)}\n"
                    
                    result += "\n"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to analyze data quality: {e}")
            return f"❌ Error analyzing data quality: {e}"
    
    def _basic_data_quality_analysis(self) -> str:
        """Perform basic data quality analysis using SQLAlchemy only.
        
        Returns:
            Formatted string with basic data quality results
        """
        try:
            if not self.sql_available:
                return "❌ SQLAlchemy not available - data quality analysis disabled"
            
            tables = self.sql_inspector.get_tables()
            result = "🔍 **Data Quality Analysis** (Basic Mode)\n\n"
            
            # Overall statistics
            total_tables = len(tables)
            total_issues = 0
            table_results = []
            
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
            
            # Format results
            score_emoji = "🟢" if overall_score >= 80 else "🟡" if overall_score >= 60 else "🔴"
            result += f"**{score_emoji} Overall Quality Score: {overall_score:.1f}%**\n\n"
            
            result += f"📊 **Summary:**\n"
            result += f"- Tables analyzed: {total_tables}\n"
            
            if total_issues > 0:
                result += f"- Total issues found: {total_issues}\n\n"
            else:
                result += "- No issues found! 🎉\n\n"
            
            # Table-by-table results
            result += "📋 **Quality by Table:**\n"
            for table_result in table_results:
                if 'error' in table_result:
                    result += f"- **{table_result['name']}**: ❌ Analysis failed\n"
                    continue
                
                quality_score = table_result['quality_score']
                score_emoji = "🟢" if quality_score >= 80 else "🟡" if quality_score >= 60 else "🔴"
                
                result += f"- **{table_result['name']}**: {score_emoji} {quality_score:.1f}%\n"
                result += f"  - Rows: {table_result['row_count']:,}\n"
                result += f"  - Columns: {table_result['column_count']}\n"
                
                if table_result['issues']:
                    result += f"  - Issues: {len(table_result['issues'])}\n"
                    for issue in table_result['issues'][:3]:  # Show first 3 issues
                        result += f"    • {issue}\n"
                    if len(table_result['issues']) > 3:
                        result += f"    • ... and {len(table_result['issues']) - 3} more\n"
                
                result += "\n"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to perform basic data quality analysis: {e}")
            return f"❌ Error in basic data quality analysis: {e}"
    
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
                return f"❌ SQLAlchemy not available - cannot search columns for '{search_term}'"
            
            if not search_term.strip():
                return "❌ Please provide a search term"
            
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
                return f"🔍 No columns found containing '{search_term}'"
            
            result = f"🔍 **Columns containing '{search_term}' ({len(matches)} found):**\n\n"
            
            # Group by table
            tables_with_matches = {}
            for match in matches:
                table = match['table']
                if table not in tables_with_matches:
                    tables_with_matches[table] = []
                tables_with_matches[table].append(match)
            
            for table, table_matches in tables_with_matches.items():
                result += f"**📋 {table}:**\n"
                for match in table_matches:
                    nullable_str = " (nullable)" if match['nullable'] else " (not null)"
                    result += f"  - {match['column']} ({match['type']}){nullable_str}\n"
                result += "\n"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to search columns for '{search_term}': {e}")
            return f"❌ Error searching columns: {e}"
    
    def get_column_data_types(self, column_name: str) -> str:
        """Get data types for a column across all tables.
        
        Args:
            column_name: Name of the column to analyze
            
        Returns:
            Formatted string with column type information across tables
        """
        try:
            if not self.sql_available:
                return f"❌ SQLAlchemy not available - cannot analyze column '{column_name}'"
            
            if not column_name.strip():
                return "❌ Please provide a column name"
            
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
                return f"🔍 Column '{column_name}' not found in any table"
            
            result = f"📊 **Column '{column_name}' Analysis ({len(column_info)} tables):**\n\n"
            
            # Group by data type
            type_groups = {}
            for info in column_info:
                col_type = str(info['type'])
                if col_type not in type_groups:
                    type_groups[col_type] = []
                type_groups[col_type].append(info)
            
            # Show type consistency
            if len(type_groups) == 1:
                result += "✅ **Type Consistency: GOOD** - All tables use the same type\n\n"
            else:
                result += f"⚠️ **Type Consistency: INCONSISTENT** - {len(type_groups)} different types found\n\n"
            
            # Detail by type
            for col_type, infos in type_groups.items():
                result += f"**Type: {col_type}** ({len(infos)} tables)\n"
                
                for info in infos:
                    result += f"  - **{info['table']}**"
                    
                    details = []
                    if info['primary_key']:
                        details.append("🔑 Primary Key")
                    if not info['nullable']:
                        details.append("🚫 Not Null")
                    if info['default'] is not None:
                        details.append(f"Default: {info['default']}")
                    
                    if details:
                        result += f" ({', '.join(details)})"
                    
                    result += f" - {info['table_rows']:,} rows\n"
                
                result += "\n"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to analyze column '{column_name}': {e}")
            return f"❌ Error analyzing column '{column_name}': {e}"
    
    # ===== Comparative Analysis Operations =====
    
    def find_common_columns(self) -> str:
        """Find columns that appear in multiple tables.
        
        Returns:
            Formatted string with common columns analysis
        """
        try:
            if not self.sql_available:
                return "❌ SQLAlchemy not available - cannot find common columns"
            
            tables = self.sql_inspector.get_tables()
            
            if len(tables) < 2:
                return "📋 Need at least 2 tables to find common columns"
            
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
                return "🔍 No columns found that appear in multiple tables"
            
            result = f"🔗 **Common Columns ({len(common_columns)} found):**\n\n"
            
            # Sort by number of occurrences (most common first)
            sorted_columns = sorted(
                common_columns.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )
            
            for col_name, occurrences in sorted_columns:
                result += f"**📊 {col_name}** (appears in {len(occurrences)} tables)\n"
                
                # Check type consistency
                types = set(str(occ['type']) for occ in occurrences)
                if len(types) == 1:
                    result += f"  ✅ Type consistent: {list(types)[0]}\n"
                else:
                    result += f"  ⚠️ Type inconsistent: {', '.join(types)}\n"
                
                # List tables
                result += "  📋 Found in:\n"
                for occ in occurrences:
                    nullable_str = " (nullable)" if occ['nullable'] else " (not null)"
                    result += f"    - {occ['table']} ({occ['type']}){nullable_str}\n"
                
                result += "\n"
            
            # Summary recommendations
            result += "💡 **Recommendations:**\n"
            inconsistent_types = [
                name for name, occs in common_columns.items() 
                if len(set(str(occ['type']) for occ in occs)) > 1
            ]
            
            if inconsistent_types:
                result += f"- Consider standardizing types for: {', '.join(inconsistent_types[:3])}\n"
            
            potential_joins = [
                name for name, occs in common_columns.items() 
                if len(occs) >= 2 and name.lower() in ['id', 'user_id', 'customer_id']
            ]
            
            if potential_joins:
                result += f"- Potential join columns: {', '.join(potential_joins[:3])}\n"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to find common columns: {e}")
            return f"❌ Error finding common columns: {e}"
    
    def detect_type_mismatches(self) -> str:
        """Detect columns with inconsistent types across tables.
        
        Returns:
            Formatted string with type mismatch analysis
        """
        try:
            if not self.sql_available:
                return "❌ SQLAlchemy not available - cannot detect type mismatches"
            
            tables = self.sql_inspector.get_tables()
            
            if len(tables) < 2:
                return "📋 Need at least 2 tables to detect type mismatches"
            
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
                return "✅ No type mismatches found! All common columns have consistent types."
            
            result = f"⚠️ **Type Mismatches Found ({len(mismatches)} columns):**\n\n"
            
            for col_name, type_tables in mismatches.items():
                result += f"**🔄 Column: {col_name}**\n"
                
                for col_type, tables_with_type in type_tables.items():
                    table_list = ', '.join(tables_with_type)
                    result += f"  - **{col_type}**: {table_list}\n"
                
                result += "\n"
            
            # Provide recommendations
            result += "💡 **Recommendations:**\n"
            result += "- Review data loading processes for type consistency\n"
            result += "- Consider explicit type casting during data import\n"
            result += "- Standardize column types across related tables\n"
            
            # Severity assessment
            high_impact = [
                name for name, types in mismatches.items() 
                if any('id' in name.lower() or name.lower() in ['date', 'time', 'amount'] for name in [name])
            ]
            
            if high_impact:
                result += f"- ⚠️ High priority columns to fix: {', '.join(high_impact[:3])}\n"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to detect type mismatches: {e}")
            return f"❌ Error detecting type mismatches: {e}"
    
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
                return f"❌ SQLAlchemy not available - cannot compare '{file1}' and '{file2}'"
            
            if not file1.strip() or not file2.strip():
                return "❌ Please provide both table names"
            
            tables = self.sql_inspector.get_tables()
            
            if file1 not in tables:
                return f"❌ Table '{file1}' not found"
            
            if file2 not in tables:
                return f"❌ Table '{file2}' not found"
            
            # Get schemas for both tables
            columns1 = self.sql_inspector.get_columns(file1)
            columns2 = self.sql_inspector.get_columns(file2)
            stats1 = self.sql_inspector.get_table_stats(file1)
            stats2 = self.sql_inspector.get_table_stats(file2)
            
            result = f"🔄 **Schema Comparison: {file1} vs {file2}**\n\n"
            
            # Basic statistics comparison
            result += "**📊 Basic Statistics:**\n"
            result += f"- **{file1}**: {stats1.get('row_count', 0):,} rows, {len(columns1)} columns\n"
            result += f"- **{file2}**: {stats2.get('row_count', 0):,} rows, {len(columns2)} columns\n\n"
            
            # Column comparison
            cols1_dict = {col['name']: col for col in columns1}
            cols2_dict = {col['name']: col for col in columns2}
            
            all_columns = set(cols1_dict.keys()) | set(cols2_dict.keys())
            common_columns = set(cols1_dict.keys()) & set(cols2_dict.keys())
            only_in_1 = set(cols1_dict.keys()) - set(cols2_dict.keys())
            only_in_2 = set(cols2_dict.keys()) - set(cols1_dict.keys())
            
            # Summary
            result += "**📋 Column Summary:**\n"
            result += f"- Common columns: {len(common_columns)}\n"
            result += f"- Only in {file1}: {len(only_in_1)}\n"
            result += f"- Only in {file2}: {len(only_in_2)}\n\n"
            
            # Common columns analysis
            if common_columns:
                result += f"**✅ Common Columns ({len(common_columns)}):**\n"
                
                type_matches = 0
                for col_name in sorted(common_columns):
                    col1 = cols1_dict[col_name]
                    col2 = cols2_dict[col_name]
                    
                    type1 = str(col1['type'])
                    type2 = str(col2['type'])
                    
                    if type1 == type2:
                        result += f"  ✅ **{col_name}**: {type1}\n"
                        type_matches += 1
                    else:
                        result += f"  ⚠️ **{col_name}**: {type1} vs {type2}\n"
                
                result += f"\n  📊 Type consistency: {type_matches}/{len(common_columns)} columns match\n\n"
            
            # Unique columns
            if only_in_1:
                result += f"**🔵 Only in {file1} ({len(only_in_1)}):**\n"
                for col_name in sorted(only_in_1):
                    col = cols1_dict[col_name]
                    result += f"  - {col_name} ({col['type']})\n"
                result += "\n"
            
            if only_in_2:
                result += f"**🟡 Only in {file2} ({len(only_in_2)}):**\n"
                for col_name in sorted(only_in_2):
                    col = cols2_dict[col_name]
                    result += f"  - {col_name} ({col['type']})\n"
                result += "\n"
            
            # Compatibility assessment
            result += "**🎯 Compatibility Assessment:**\n"
            
            if len(common_columns) == 0:
                result += "❌ No common columns - tables are completely different\n"
            elif len(common_columns) == len(all_columns):
                if type_matches == len(common_columns):
                    result += "✅ Schemas are identical\n"
                else:
                    result += "⚠️ Same columns but some type differences\n"
            else:
                compatibility = len(common_columns) / len(all_columns) * 100
                if compatibility >= 80:
                    result += f"✅ High compatibility ({compatibility:.1f}%)\n"
                elif compatibility >= 50:
                    result += f"⚠️ Moderate compatibility ({compatibility:.1f}%)\n"
                else:
                    result += f"❌ Low compatibility ({compatibility:.1f}%)\n"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to compare '{file1}' and '{file2}': {e}")
            return f"❌ Error comparing tables: {e}"
    
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
