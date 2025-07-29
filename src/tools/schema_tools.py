"""Schema analysis tools for LangChain agent."""

from typing import List, Dict, Any, Optional
from langchain.tools import Tool
from langchain.pydantic_v1 import BaseModel, Field
import logging
import os
import sys

# Add src to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger
from metadata.metadata_store import MetadataStore


class SchemaTools:
    """Tools for schema analysis and querying."""
    
    def __init__(self, metadata_store: MetadataStore):
        """Initialize schema tools.
        
        Args:
            metadata_store: MetadataStore instance
        """
        self.store = metadata_store
        self.logger = get_logger("tabletalk.tools")
    
    def get_file_schema(self, file_name: str) -> str:
        """Get schema information for a specific file.
        
        Args:
            file_name: Name of the file
            
        Returns:
            Formatted string with schema information
        """
        try:
            schema = self.store.get_file_schema(file_name)
            
            if not schema:
                return f"No schema found for: {file_name}"
            
            total_rows = schema[0]['total_rows']
            result = [f"{file_name}: {total_rows} rows, {len(schema)} columns"]
            
            for col in schema:
                null_pct = (col['null_count'] / col['total_rows']) * 100 if col['total_rows'] > 0 else 0
                null_info = f", {col['null_count']} nulls" if col['null_count'] > 0 else ""
                
                result.append(f"  {col['column_name']} ({col['data_type']}): {col['unique_count']} unique{null_info}")
            
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error getting schema for {file_name}: {str(e)}")
            return f"Error retrieving schema for {file_name}: {str(e)}"
    
    def list_all_files(self, *args, **kwargs) -> str:
        """List all scanned files with basic information.
        
        Returns:
            Formatted string with file list
        """
        try:
            files = self.store.list_all_files()
            
            if not files:
                return "No files scanned yet. Use /scan <directory> to scan files."
            
            result = [f"Scanned files ({len(files)}):"]
            
            for file_info in files:
                size_str = f"{file_info['file_size_mb']:.1f}MB" if file_info['file_size_mb'] else "?"
                rows_str = f"{file_info['total_rows']}" if file_info['total_rows'] else "?"
                
                result.append(f"  {file_info['file_name']}: {file_info['column_count']} cols, {rows_str} rows, {size_str}")
            
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error listing files: {str(e)}")
            return f"Error listing files: {str(e)}"
    
    def find_columns_with_name(self, column_name: str) -> str:
        """Find all files containing a column with the specified name.
        
        Args:
            column_name: Name of the column to search for
            
        Returns:
            Formatted string with matching columns
        """
        try:
            matches = self.store.find_columns_by_name(column_name)
            
            if not matches:
                return f"No columns found matching: {column_name}"
            
            result = [f"Files with column '{column_name}' ({len(matches)} matches):"]
            
            for match in matches:
                null_info = f"{match['null_count']} nulls" if match['null_count'] else "no nulls"
                unique_info = f"{match['unique_count']} unique"
                
                result.append(
                    f"  - {match['file_name']}.{match['column_name']} "
                    f"({match['data_type']}): {unique_info}, {null_info}"
                )
            
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error finding columns with name {column_name}: {str(e)}")
            return f"Error searching for column {column_name}: {str(e)}"
    
    def detect_type_mismatches(self, *args, **kwargs) -> str:
        """Detect columns with same name but different types across files.
        
        Returns:
            Formatted string with type mismatch information
        """
        try:
            mismatches = self.store.detect_type_mismatches()
            
            if not mismatches:
                return "No type mismatches found across files."
            
            # Group by column name
            grouped = {}
            for mismatch in mismatches:
                col_name = mismatch['column_name']
                if col_name not in grouped:
                    grouped[col_name] = []
                grouped[col_name].append(mismatch)
            
            result = [f"Type mismatches found for {len(grouped)} columns:"]
            
            for col_name, types in grouped.items():
                result.append(f"\n  Column: {col_name}")
                for type_info in types:
                    result.append(
                        f"    - {type_info['data_type']}: {type_info['files']} "
                        f"({type_info['file_count']} files)"
                    )
            
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error detecting type mismatches: {str(e)}")
            return f"Error detecting type mismatches: {str(e)}"
    
    def find_common_columns(self, *args, **kwargs) -> str:
        """Find columns that appear in multiple files.
        
        Returns:
            Formatted string with common columns information
        """
        try:
            common = self.store.get_common_columns()
            
            if not common:
                return "No common columns found across files."
            
            result = [f"Common columns ({len(common)} found):"]
            
            for col in common:
                warning = " (type mismatch)" if col['type_variations'] > 1 else ""
                result.append(f"  {col['column_name']}: {col['file_count']} files, types: {col['data_types']}{warning}")
                result.append(f"    Files: {col['files']}")
            
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error finding common columns: {str(e)}")
            return f"Error finding common columns: {str(e)}"
    
    def get_database_summary(self, *args, **kwargs) -> str:
        """Get overall database statistics.
        
        Returns:
            Formatted string with database summary
        """
        try:
            stats = self.store.get_database_stats()
            
            result = [
                "Database Summary:",
                f"  - Total files scanned: {stats['total_files']}",
                f"  - Total columns: {stats['total_columns']}",
                f"  - Unique column names: {stats['unique_columns']}",
                f"  - Average file size: {stats['avg_file_size_mb']}MB"
            ]
            
            if stats['last_scan_time']:
                result.append(f"  - Last scan: {stats['last_scan_time']}")
            
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error getting database summary: {str(e)}")
            return f"Error getting database summary: {str(e)}"
    
    def detect_semantic_type_issues(self, *args, **kwargs) -> str:
        """Detect columns that likely have incorrect data types based on naming patterns.
        
        Returns:
            Formatted string with semantic type issues
        """
        try:
            files = self.store.list_all_files()
            issues = []
            
            # Common patterns that suggest expected data types
            type_patterns = {
                'integer': [
                    'id', '_id', 'count', 'quantity', 'qty', 'number', 'num', 'age', 'year',
                    'month', 'day', 'rank', 'position', 'index', 'version'
                ],
                'float': [
                    'amount', 'price', 'cost', 'value', 'rate', 'percentage', 'percent',
                    'score', 'rating', 'weight', 'height', 'distance', 'salary', 'revenue',
                    'profit', 'loss', 'balance', 'total', 'subtotal', 'tax', 'fee'
                ],
                'datetime': [
                    'date', 'time', 'created', 'updated', 'modified', 'timestamp',
                    'start', 'end', 'signup', 'login', 'expires', '_at', '_on'
                ],
                'boolean': [
                    'is_', 'has_', 'can_', 'should_', 'active', 'enabled', 'disabled',
                    'verified', 'confirmed', 'approved', 'deleted', 'published'
                ]
            }
            
            for file_info in files:
                schema = self.store.get_file_schema(file_info['file_name'])
                
                for col in schema:
                    col_name = col['column_name'].lower()
                    actual_type = col['data_type']
                    
                    # Check each pattern
                    for expected_type, patterns in type_patterns.items():
                        for pattern in patterns:
                            if pattern in col_name and actual_type != expected_type:
                                # Skip if it's a reasonable alternative
                                if self._is_acceptable_type_alternative(expected_type, actual_type):
                                    continue
                                    
                                issues.append({
                                    'file': file_info['file_name'],
                                    'column': col['column_name'],
                                    'actual_type': actual_type,
                                    'expected_type': expected_type,
                                    'reason': f"Column name contains '{pattern}'"
                                })
                                break
            
            if not issues:
                return "No semantic data type issues detected."
            
            result = [f"Potential data type issues ({len(issues)} found):"]
            result.append("")
            
            for issue in issues:
                result.append(f"🚨 {issue['file']} - {issue['column']}")
                result.append(f"   Expected: {issue['expected_type']} | Actual: {issue['actual_type']}")
                result.append(f"   Reason: {issue['reason']}")
                result.append("")
            
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error detecting semantic type issues: {str(e)}")
            return f"Error detecting semantic type issues: {str(e)}"
    
    def _is_acceptable_type_alternative(self, expected: str, actual: str) -> bool:
        """Check if actual type is an acceptable alternative to expected type."""
        acceptable_alternatives = {
            'integer': ['float'],  # float can represent integers
            'float': ['integer'],  # integers can be monetary values
            'datetime': ['string'], # dates often stored as strings initially
        }
        
        return actual in acceptable_alternatives.get(expected, [])
    
    def detect_column_name_variations(self, *args, **kwargs) -> str:
        """Detect columns that likely represent the same field but have different naming conventions.
        
        Returns:
            Formatted string with potential column name variations
        """
        try:
            files = self.store.list_all_files()
            
            if len(files) < 2:
                return "Need at least 2 files to detect column name variations."
            
            # Get all columns from all files
            all_columns = []
            for file_info in files:
                schema = self.store.get_file_schema(file_info['file_name'])
                for col in schema:
                    all_columns.append({
                        'file': file_info['file_name'],
                        'column': col['column_name'],
                        'type': col['data_type'],
                        'normalized': self._normalize_column_name(col['column_name'])
                    })
            
            # Group by normalized names
            grouped = {}
            for col in all_columns:
                norm_name = col['normalized']
                if norm_name not in grouped:
                    grouped[norm_name] = []
                grouped[norm_name].append(col)
            
            # Find variations (same normalized name, different actual names)
            variations = []
            for norm_name, cols in grouped.items():
                if len(cols) > 1:
                    # Check if they have different actual names
                    actual_names = set(col['column'] for col in cols)
                    if len(actual_names) > 1:
                        variations.append({
                            'normalized': norm_name,
                            'columns': cols,
                            'actual_names': actual_names
                        })
            
            if not variations:
                return "No column name variations detected."
            
            result = [f"Column name variations found ({len(variations)} groups):"]
            result.append("")
            
            for var in variations:
                result.append(f"🔄 Likely same field: {var['normalized']}")
                
                # Group by file for cleaner display
                by_file = {}
                for col in var['columns']:
                    if col['file'] not in by_file:
                        by_file[col['file']] = []
                    by_file[col['file']].append(col)
                
                for file_name, file_cols in by_file.items():
                    for col in file_cols:
                        type_info = f" ({col['type']})" if col['type'] else ""
                        result.append(f"   📁 {file_name}: {col['column']}{type_info}")
                
                # Add suggestion
                most_common = max(var['actual_names'], key=len)  # Longest name as suggestion
                result.append(f"   💡 Suggestion: Standardize to '{most_common}'")
                result.append("")
            
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error detecting column name variations: {str(e)}")
            return f"Error detecting column name variations: {str(e)}"
    
    def _normalize_column_name(self, name: str) -> str:
        """Normalize column name for comparison by removing common variations.
        
        Args:
            name: Original column name
            
        Returns:
            Normalized column name
        """
        import re
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common prefixes/suffixes
        normalized = re.sub(r'^(tbl_|col_|fld_)', '', normalized)
        normalized = re.sub(r'(_id|_key|_ref|_code)$', '_id', normalized)
        
        # Convert camelCase to snake_case
        # customerId -> customer_id
        normalized = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', normalized).lower()
        
        # Remove underscores and spaces for core comparison
        core = re.sub(r'[_\s-]', '', normalized)
        
        # Standardize common variations
        replacements = {
            'cust': 'customer',
            'usr': 'user', 
            'uid': 'user_id',
            'cid': 'customer_id',
            'oid': 'order_id',
            'pid': 'product_id',
            'amt': 'amount',
            'qty': 'quantity',
            'num': 'number',
            'dt': 'date',
            'tm': 'time',
            'addr': 'address',
            'desc': 'description',
            'info': 'information',
        }
        
        for abbrev, full in replacements.items():
            if abbrev in core:
                core = core.replace(abbrev, full)
        
        return core

    def get_langchain_tools(self) -> List[Tool]:
        """Get LangChain Tool objects for use with agents.
        
        Returns:
            List of LangChain Tool objects
        """
        tools = [
            Tool(
                name="get_file_schema",
                description="Get detailed schema information for a specific file. Use this when user asks about a specific file's structure, columns, or data types.",
                func=self.get_file_schema,
            ),
            Tool(
                name="list_files",
                description="List all scanned files with basic statistics. Use this when user asks what files are available or wants an overview.",
                func=self.list_all_files,
            ),
            Tool(
                name="find_columns",
                description="Find all files that contain a column with a specific name. Use this when user asks about a specific column across files.",
                func=self.find_columns_with_name,
            ),
            Tool(
                name="detect_type_mismatches",
                description="Find columns with the same name but different data types across files. Use this when user asks about inconsistencies or data type problems.",
                func=self.detect_type_mismatches,
            ),
            Tool(
                name="find_common_columns",
                description="Find columns that appear in multiple files. Use this when user asks about shared columns or commonalities across files.",
                func=self.find_common_columns,
            ),
            Tool(
                name="database_summary",
                description="Get overall statistics about the scanned files and database. Use this for general overview questions.",
                func=self.get_database_summary,
            ),
            Tool(
                name="detect_semantic_type_issues",
                description="Detect columns that likely have incorrect data types based on column naming patterns (e.g., 'amount' should be numeric, 'id' should be integer). Use when user asks about data type problems or semantic validation.",
                func=self.detect_semantic_type_issues,
            ),
            Tool(
                name="detect_column_name_variations",
                description="Detect columns that likely represent the same field but have different naming conventions (e.g., customerId vs customer_id). Use when user asks about column naming inconsistencies or standardization.",
                func=self.detect_column_name_variations,
            ),
        ]
        
        return tools
