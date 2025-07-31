"""Atomic schema tools - simple, single-purpose operations with smart fuzzy matching."""

import re
from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from metadata.metadata_store import MetadataStore


class AtomicSchemaTools:
    """Atomic tools that perform single, focused operations with built-in smart matching."""
    
    def __init__(self, metadata_store: MetadataStore):
        """Initialize atomic schema tools.
        
        Args:
            metadata_store: MetadataStore instance
        """
        self.store = metadata_store
        self.logger = get_logger("tabletalk.atomic_tools")
    
    # ============================================================================
    # File Operations - Basic file-level queries
    # ============================================================================
    
    def list_files(self) -> str:
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
    
    
    def get_file_schema(self, file_name: str) -> str:
        """Get detailed schema information for a specific file (smart file matching).
        
        Args:
            file_name: Name of the file (can be partial, fuzzy matching applied)
            
        Returns:
            Formatted string with schema information
        """
        try:
            files = self.store.list_all_files()
            
            if not files:
                return "No files have been scanned yet. Use /scan <directory> to scan files."
            
            # Smart file matching
            actual_file_name = self._find_best_file_match(file_name, files)
            
            if not actual_file_name:
                available_files = [f['file_name'] for f in files]
                return f"No files match '{file_name}'. Available files: {', '.join(available_files)}"
            
            schema = self.store.get_file_schema(actual_file_name)
            
            if not schema:
                return f"Schema data not found for: {actual_file_name}"
            
            return self._format_file_schema(schema, actual_file_name)
            
        except Exception as e:
            self.logger.error(f"Error getting schema for {file_name}: {str(e)}")
            return f"Error retrieving schema for {file_name}: {str(e)}"
    
    # ============================================================================
    # Column Search - One smart method that handles all cases
    # ============================================================================
    
    def search_columns(self, search_term: str) -> str:
        """Smart column search with fuzzy matching.
        
        Uses simple partial matching - exact matches will be found automatically.
        For complex variations, let the LLM make multiple calls with different terms.
        
        Args:
            search_term: Term to search for in column names
            
        Returns:
            Formatted string with all relevant matches
        """
        try:
            # Simple approach: search for partial matches (case-insensitive)
            files = self.store.list_all_files()
            matches = []
            
            search_lower = search_term.lower()
            
            for file_info in files:
                schema = self.store.get_file_schema(file_info['file_name'])
                if schema:
                    for col in schema:
                        if search_lower in col['column_name'].lower():
                            matches.append({
                                'file_name': file_info['file_name'],
                                'column_name': col['column_name'],
                                'data_type': col['data_type'],
                                'null_count': col['null_count'],
                                'unique_count': col['unique_count']
                            })
            
            if not matches:
                return f"No columns found containing: {search_term}"
            
            return self._format_column_search_results(matches, search_term)
            
        except Exception as e:
            self.logger.error(f"Error searching columns for {search_term}: {str(e)}")
            return f"Error searching for columns: {str(e)}"
    
    
    # ============================================================================
    # Simple Data Operations - Basic data retrieval
    # ============================================================================
    
    def get_column_data_types(self, column_name: str) -> str:
        """Get all data types used for a specific column name across files.
        
        Uses simple partial matching for column names.
        
        Args:
            column_name: Name of the column (partial matching applied)
            
        Returns:
            Formatted string with data type information
        """
        try:
            # Simple partial matching approach
            files = self.store.list_all_files()
            matches = []
            
            search_lower = column_name.lower()
            
            for file_info in files:
                schema = self.store.get_file_schema(file_info['file_name'])
                if schema:
                    for col in schema:
                        if search_lower in col['column_name'].lower():
                            matches.append({
                                'file_name': file_info['file_name'],
                                'column_name': col['column_name'],
                                'data_type': col['data_type']
                            })
            
            if not matches:
                return f"No columns found containing: {column_name}"
            
            # Group by data type
            type_groups = {}
            for match in matches:
                data_type = match['data_type']
                if data_type not in type_groups:
                    type_groups[data_type] = []
                type_groups[data_type].append(f"{match['file_name']}.{match['column_name']}")
            
            result = [f"Data types for columns containing '{column_name}':"]
            for data_type, column_refs in type_groups.items():
                result.append(f"  {data_type}: {', '.join(column_refs)}")
            
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error getting data types for {column_name}: {str(e)}")
            return f"Error retrieving data types for {column_name}: {str(e)}"
    
    def get_database_summary(self) -> str:
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
                f"  - Average file size: {stats['avg_file_size_mb']:.1f}MB"
            ]
            
            if stats['last_scan_time']:
                result.append(f"  - Last scan: {stats['last_scan_time']}")
            
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error getting database summary: {str(e)}")
            return f"Error getting database summary: {str(e)}"
    
    
    # ============================================================================
    # Helper Methods - Smart matching and formatting utilities
    # ============================================================================
    
    def _find_best_file_match(self, file_name: str, files: List[Dict]) -> Optional[str]:
        """Find the best matching file using simple partial matching.
        
        Args:
            file_name: File name to search for
            files: List of file dictionaries
            
        Returns:
            Best matching file name or None if not found
        """
        file_name_lower = file_name.lower()
        
        # 1. Exact match first
        for f in files:
            if f['file_name'].lower() == file_name_lower:
                return f['file_name']
        
        # 2. Partial match (must be unique)
        partial_matches = [f for f in files if file_name_lower in f['file_name'].lower()]
        if len(partial_matches) == 1:
            return partial_matches[0]['file_name']
        elif len(partial_matches) > 1:
            # If multiple matches, try without extension
            name_without_ext = file_name_lower.split('.')[0]
            exact_without_ext = [f for f in partial_matches if name_without_ext == f['file_name'].lower().split('.')[0]]
            if len(exact_without_ext) == 1:
                return exact_without_ext[0]['file_name']
        
        return None
    
    def _format_file_schema(self, schema: List[Dict], file_name: str) -> str:
        """Format schema information for display.
        
        Args:
            schema: Schema data
            file_name: Name of the file
            
        Returns:
            Formatted schema string
        """
        if not schema:
            return f"No schema data found for {file_name}"
        
        total_rows = schema[0]['total_rows']
        result = [f"{file_name}: {total_rows} rows, {len(schema)} columns"]
        
        for col in schema:
            null_info = f", {col['null_count']} nulls" if col['null_count'] > 0 else ""
            result.append(f"  {col['column_name']} ({col['data_type']}): {col['unique_count']} unique{null_info}")
        
        return "\n".join(result)
    
    def _format_column_search_results(self, matches: List[Dict], search_term: str) -> str:
        """Format column search results in a simple, clean way.
        
        Args:
            matches: List of match dictionaries
            search_term: Original search term
            
        Returns:
            Formatted results string
        """
        result = [f"Columns containing '{search_term}' ({len(matches)} matches):"]
        
        for match in matches:
            null_info = f", {match['null_count']} nulls" if match.get('null_count', 0) > 0 else ""
            unique_info = f", {match['unique_count']} unique" if match.get('unique_count') else ""
            result.append(f"  - {match['file_name']}.{match['column_name']} ({match['data_type']}){unique_info}{null_info}")
        
        return "\n".join(result)
