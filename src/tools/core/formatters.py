"""Output formatting strategies for different presentation needs."""
from tabulate import tabulate
from typing import List, Dict, Any, Optional
from .base_components import BaseFormatter

class TextFormatter(BaseFormatter):
    """Text-based formatter for current text-style output."""
    
    def format(self, data: List[Dict[str, Any]], context: Optional[Dict] = None) -> str:
        """Format data as human-readable text."""
        if not data:
            return "No results found."
        
        context = context or {}
        format_type = context.get('format_type', 'search_results')
        
        if format_type == 'search_results':
            return self._format_search_results(data, context)
        elif format_type == 'schema_info':
            return self._format_schema_info(data, context)
        elif format_type == 'analysis_results':
            return self._format_analysis_results(data, context)
        elif format_type == 'file_list':
            return self._format_file_list(data, context)
        else:
            return self._format_generic(data, context)
    
    def _format_search_results(self, matches: List[Dict], context: Dict) -> str:
        """Format search results (columns, files, types)."""
        search_term = context.get('search_term', 'search')
        search_type = context.get('search_type', 'item')
        
        if not matches:
            return f"No {search_type}s found containing: {search_term}"
        
        result = [f"Found {len(matches)} {search_type}(s) containing '{search_term}':", ""]
        
        if search_type == 'column':
            for match in matches:
                result.append(f"[FILE] {match['file_name']}")
                result.append(f"  └─ {match['column_name']} ({match['data_type']})")
                result.append(f"     Nulls: {match.get('null_count', 'N/A')}, "
                            f"Unique: {match.get('unique_count', 'N/A')}")
                result.append("")
        
        elif search_type == 'file':
            for match in matches:
                result.append(f"[FILE] {match['file_name']}")
                result.append(f"  Rows: {match.get('total_rows', 'N/A')}, "
                            f"Columns: {match.get('column_count', 'N/A')}")
                if match.get('columns'):
                    result.append(f"  Columns: {', '.join(match['columns'][:5])}"
                                f"{'...' if len(match['columns']) > 5 else ''}")
                result.append("")
        
        else:  # type search
            for match in matches:
                result.append(f"[FILE] {match['file_name']}")
                result.append(f"  └─ {match['column_name']} ({match['data_type']})")
                result.append("")
        
        return "\n".join(result)
    
    def _format_schema_info(self, schemas: List[Dict], context: Dict) -> str:
        """Format schema information."""
        if not schemas:
            return "No schema information found."
        
        if len(schemas) == 1:
            # Single file schema
            schema = schemas[0]
            file_name = context.get('file_name', 'file')
            
            result = [f"Schema for {file_name}:", ""]
            
            if 'columns' in schema:
                result.append(f"Columns ({len(schema['columns'])}):")
                for col in schema['columns']:
                    result.append(f"  • {col['column_name']} ({col['data_type']})")
                    result.append(f"    Nulls: {col.get('null_count', 'N/A')}, "
                                f"Unique: {col.get('unique_count', 'N/A')}")
                result.append("")
            
            if 'total_rows' in schema:
                result.append(f"Total rows: {schema['total_rows']}")
        
        else:
            # Multiple file schemas summary
            result = [f"Schema information for {len(schemas)} files:", ""]
            
            for schema in schemas:
                file_name = schema.get('file_name', 'Unknown')
                column_count = len(schema.get('columns', []))
                total_rows = schema.get('total_rows', 'N/A')
                
                result.append(f"[FILE] {file_name}")
                result.append(f"  Columns: {column_count}, Rows: {total_rows}")
                result.append("")
        
        return "\n".join(result)
    
    def _format_analysis_results(self, results: List[Dict], context: Dict) -> str:
        """Format analysis results (relationships, inconsistencies)."""
        analysis_type = context.get('analysis_type', 'analysis')
        
        if not results:
            return f"No {analysis_type} found."
        
        result = [f"{analysis_type.replace('_', ' ').title()} Results:", ""]
        
        if analysis_type == 'common_columns':
            for item in results:
                result.append(f"[COL] {item['column_name']}")
                result.append(f"  Found in {item['file_count']} files: "
                            f"{', '.join(item['files'][:3])}"
                            f"{'...' if len(item['files']) > 3 else ''}")
                if len(item['data_types']) > 1:
                    result.append(f"  [!] Multiple data types: {', '.join(item['data_types'])}")
                result.append("")
        
        elif analysis_type == 'similar_schemas':
            for item in results:
                if 'group_files' in item:
                    # Handle new format with group_files
                    files = item['group_files']
                    if len(files) >= 2:
                        result.append(f"[LINK] {' <-> '.join(files)}")
                        result.append(f"  Common columns ({item.get('common_column_count', len(item.get('common_columns', [])))}): {', '.join(item.get('common_columns', []))}")
                        result.append(f"  Similarity score: {item.get('similarity_score', 'N/A')}")
                    else:
                        result.append(f"[LINK] Group: {', '.join(files)}")
                        result.append(f"  Common columns: {', '.join(item.get('common_columns', []))}")
                else:
                    # Handle legacy format with file1/file2 (for backward compatibility)
                    result.append(f"[LINK] {item['file1']} <-> {item['file2']}")
                    result.append(f"  Common columns: {item['common_columns']}")
                    result.append(f"  Files have {item['file1_total']} and {item['file2_total']} columns total")
                result.append("")
        
        elif analysis_type == 'data_types':
            for item in results:
                result.append(f"[!] {item['column_name']}")
                result.append(f"  Found {len(item['type_variations'])} different data types:")
                for data_type, files in item['type_variations'].items():
                    result.append(f"    • {data_type}: {', '.join(files[:2])}"
                                f"{'...' if len(files) > 2 else ''}")
                result.append("")
        
        return "\n".join(result)
    
    def _format_file_list(self, files: List[Dict], context: Dict) -> str:
        """Format file listing."""
        if not files:
            return "No files found."
        
        result = [f"Found {len(files)} files:", ""]
        
        for file_info in files:
            result.append(f"[FILE] {file_info['file_name']}")
            result.append(f"  Size: {file_info.get('file_size', 'N/A')} bytes, "
                         f"Rows: {file_info.get('total_rows', 'N/A')}")
            result.append(f"  Last modified: {file_info.get('last_modified', 'N/A')}")
            result.append("")
        
        return "\n".join(result)
    
    def _format_generic(self, data: List[Dict], context: Dict) -> str:
        """Generic formatting for any data structure."""
        if not data:
            return "No data found."
        
        result = [f"Results ({len(data)} items):", ""]
        
        for i, item in enumerate(data, 1):
            result.append(f"{i}. {item}")
            result.append("")
        
        return "\n".join(result)


class TableFormatter(BaseFormatter):
    """Table-based formatter using tabulate when available."""
    
    def format(self, data: List[Dict[str, Any]], context: Optional[Dict] = None) -> str:
        """Format data as a table."""
        if not data:
            return "No results found."
        
        context = context or {}
        table_format = context.get('table_format', 'simple')
        
        try:
            # Convert data to table format
            if all(isinstance(item, dict) for item in data):
                return tabulate(data, headers="keys", tablefmt=table_format)
            else:
                # Handle non-dict data
                return tabulate([{'item': item} for item in data], 
                              headers="keys", tablefmt=table_format)
        
        except Exception as e:
            # Fallback to text formatter on any error
            text_formatter = TextFormatter()
            return text_formatter.format(data, context)
