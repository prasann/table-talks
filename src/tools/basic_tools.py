"""Basic information tools for files, schemas, and statistics."""

from typing import Dict
from .core.base_components import BaseTool
from .core.searchers import ColumnSearcher
from .core.formatters import TextFormatter


class GetFilesTool(BaseTool):
    """Tool for listing files with optional pattern filtering."""
    
    description = "List all files, optionally filtered by pattern"
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Optional pattern to filter file names"
                }
            },
            "required": [],
            "additionalProperties": False
        }
    
    def execute(self, pattern: str = None) -> str:
        """List files, optionally filtered by pattern."""
        try:
            files = self.store.list_all_files()
            
            if pattern:
                pattern_lower = pattern.lower()
                files = [f for f in files if pattern_lower in f['file_name'].lower()]
            
            formatter = TextFormatter()
            return formatter.format(files, {'format_type': 'file_list'})
            
        except Exception as e:
            self.logger.error(f"Error listing files: {str(e)}")
            return f"Error listing files: {str(e)}"


class GetSchemasTool(BaseTool):
    """Tool for getting schema information for files."""
    
    description = "Get detailed schema information for specific files or all files. Use file_pattern parameter to filter for specific tables/files (e.g., 'orders', 'customers'). Without file_pattern, returns summary of all files."
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "file_pattern": {
                    "type": "string",
                    "description": "File name or pattern to filter for specific table/file (e.g., 'orders' for orders.csv, 'customer' for customer files). Leave empty to get all files."
                },
                "detailed": {
                    "type": "boolean", 
                    "description": "Include detailed column information",
                    "default": True
                }
            },
            "required": [],
            "additionalProperties": False
        }
    
    def execute(self, file_pattern: str = None, detailed: bool = True) -> str:
        """Get schema information for files."""
        try:
            if file_pattern:
                # Get schema for specific file(s) matching pattern
                files = self.store.list_all_files()
                matching_files = []
                pattern_lower = file_pattern.lower()
                
                for file_info in files:
                    if pattern_lower in file_info['file_name'].lower():
                        schema = self.store.get_file_schema(file_info['file_name'])
                        if schema:
                            matching_files.append({
                                'file_name': file_info['file_name'],
                                'columns': schema,
                                'total_rows': file_info.get('total_rows', 'N/A')
                            })
                
                if not matching_files:
                    return f"No files found matching pattern: {file_pattern}"
                
                formatter = TextFormatter()
                context = {'format_type': 'schema_info', 'file_name': file_pattern}
                return formatter.format(matching_files, context)
            
            else:
                # Get summary of all schemas
                files = self.store.list_all_files()
                all_schemas = []
                
                for file_info in files:
                    schema = self.store.get_file_schema(file_info['file_name'])
                    if schema:
                        all_schemas.append({
                            'file_name': file_info['file_name'],
                            'columns': schema if detailed else [],
                            'column_count': len(schema),
                            'total_rows': file_info.get('total_rows', 'N/A')
                        })
                
                formatter = TextFormatter()
                return formatter.format(all_schemas, {'format_type': 'schema_info'})
            
        except Exception as e:
            self.logger.error(f"Error getting schemas: {str(e)}")
            return f"Error getting schemas: {str(e)}"


class GetStatisticsTool(BaseTool):
    """Tool for getting statistics at various levels."""
    
    description = "Get stats at database, file, or column level"
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["database", "file", "column"],
                    "description": "Scope of statistics to retrieve",
                    "default": "database"
                },
                "target": {
                    "type": "string",
                    "description": "Specific target (file name, column name) when scope is not database"
                }
            },
            "required": [],
            "additionalProperties": False
        }
    
    def execute(self, scope: str = "database", target: str = None) -> str:
        """Get statistics based on scope."""
        try:
            if scope == "database":
                return self._get_database_statistics()
            elif scope == "file" and target:
                return self._get_file_statistics(target)
            elif scope == "column" and target:
                return self._get_column_statistics(target)
            else:
                return f"Invalid scope '{scope}' or missing target for file/column scope"
                
        except Exception as e:
            self.logger.error(f"Error getting statistics: {str(e)}")
            return f"Error getting statistics: {str(e)}"
    
    def _get_database_statistics(self) -> str:
        """Get overall database statistics."""
        files = self.store.list_all_files()
        total_files = len(files)
        total_rows = sum(f.get('total_rows', 0) for f in files)
        
        # Get unique column names
        all_columns = set()
        all_data_types = set()
        
        for file_info in files:
            schema = self.store.get_file_schema(file_info['file_name'])
            if schema:
                for col in schema:
                    all_columns.add(col['column_name'])
                    all_data_types.add(col['data_type'])
        
        result = [
            "Database Statistics:",
            "",
            f"Files: {total_files}",
            f"Total rows: {total_rows:,}",
            f"Unique column names: {len(all_columns)}",
            f"Data types used: {len(all_data_types)}",
            "",
            f"Data types: {', '.join(sorted(all_data_types))}",
        ]
        
        return "\n".join(result)
    
    def _get_file_statistics(self, file_pattern: str) -> str:
        """Get statistics for specific file(s)."""
        files = self.store.list_all_files()
        matching_files = [f for f in files if file_pattern.lower() in f['file_name'].lower()]
        
        if not matching_files:
            return f"No files found matching: {file_pattern}"
        
        result = [f"File Statistics for pattern '{file_pattern}':", ""]
        
        for file_info in matching_files:
            schema = self.store.get_file_schema(file_info['file_name'])
            result.append(f"[FILE] {file_info['file_name']}")
            result.append(f"  Rows: {file_info.get('total_rows', 'N/A'):,}")
            result.append(f"  Columns: {len(schema) if schema else 0}")
            result.append(f"  File size: {file_info.get('file_size', 'N/A')} bytes")
            result.append("")
        
        return "\n".join(result)
    
    def _get_column_statistics(self, column_pattern: str) -> str:
        """Get statistics for columns matching pattern."""
        searcher = ColumnSearcher(self.store)
        matches = searcher.search(column_pattern)
        
        if not matches:
            return f"No columns found matching: {column_pattern}"
        
        # Aggregate statistics
        total_files = len(set(m['file_name'] for m in matches))
        data_types = set(m['data_type'] for m in matches)
        
        result = [
            f"Column Statistics for pattern '{column_pattern}':",
            "",
            f"Matching columns: {len(matches)}",
            f"Files containing matches: {total_files}",
            f"Data types: {', '.join(sorted(data_types))}",
            ""
        ]
        
        # Show sample matches
        result.append("Sample matches:")
        for match in matches[:5]:
            result.append(f"  • {match['file_name']}: {match['column_name']} ({match['data_type']})")
        
        if len(matches) > 5:
            result.append(f"  ... and {len(matches) - 5} more")
        
        return "\n".join(result)
