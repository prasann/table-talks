"""Unified tools for schema metadata operations."""

from typing import Dict, List, Any
from .core.base_components import BaseTool
from .core.searchers import ColumnSearcher, FileSearcher, TypeSearcher
from .core.analyzers import RelationshipAnalyzer, ConsistencyChecker
from .core.formatters import TextFormatter, TableFormatter


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
            "required": []
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
    
    description = "Get schema info for files, optionally filtered by pattern"
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "file_pattern": {
                    "type": "string",
                    "description": "Optional file pattern to filter"
                },
                "detailed": {
                    "type": "boolean", 
                    "description": "Include detailed column information",
                    "default": True
                }
            },
            "required": []
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


class SearchMetadataTool(BaseTool):
    """Tool for searching across metadata."""
    
    description = "Search across metadata. search_type: 'column', 'file', 'type'"
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string", 
                    "description": "Term to search for"
                },
                "search_type": {
                    "type": "string",
                    "enum": ["column", "file", "type"],
                    "description": "Type of search to perform",
                    "default": "column"
                }
            },
            "required": ["search_term"]
        }
    
    def execute(self, search_term: str, search_type: str = "column") -> str:
        """Search across metadata."""
        try:
            searchers = {
                "column": ColumnSearcher(self.store),
                "file": FileSearcher(self.store),
                "type": TypeSearcher(self.store)
            }
            
            if search_type not in searchers:
                return f"Invalid search type: {search_type}. Use: column, file, or type"
            
            results = searchers[search_type].search(search_term)
            
            formatter = TextFormatter()
            context = {
                'format_type': 'search_results',
                'search_term': search_term,
                'search_type': search_type
            }
            return formatter.format(results, context)
            
        except Exception as e:
            self.logger.error(f"Error searching metadata: {str(e)}")
            return f"Error searching metadata: {str(e)}"


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
            "required": []
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
            result.append(f"📄 {file_info['file_name']}")
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


class FindRelationshipsTool(BaseTool):
    """Tool for finding relationships between files and columns."""
    
    description = "Find relationships like common columns or similar schemas"
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "analysis_type": {
                    "type": "string",
                    "enum": ["common_columns", "similar_schemas"],
                    "description": "Type of relationship analysis to perform",
                    "default": "common_columns"
                },
                "threshold": {
                    "type": "integer",
                    "description": "Minimum threshold for relationships (e.g., min common columns)",
                    "default": 2
                }
            },
            "required": []
        }
    
    def execute(self, analysis_type: str = "common_columns", threshold: int = 2) -> str:
        """Find relationships between files and columns."""
        try:
            analyzer = RelationshipAnalyzer(self.store)
            results = analyzer.analyze(analysis_type, threshold=threshold)
            
            formatter = TextFormatter()
            context = {
                'format_type': 'analysis_results',
                'analysis_type': analysis_type
            }
            return formatter.format(results, context)
            
        except Exception as e:
            self.logger.error(f"Error finding relationships: {str(e)}")
            return f"Error finding relationships: {str(e)}"


class DetectInconsistenciesTool(BaseTool):
    """Tool for detecting data inconsistencies."""
    
    description = "Detect inconsistencies like type mismatches or naming issues"
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "check_type": {
                    "type": "string",
                    "enum": ["data_types", "naming_patterns"],
                    "description": "Type of consistency check to perform",
                    "default": "data_types"
                }
            },
            "required": []
        }
    
    def execute(self, check_type: str = "data_types") -> str:
        """Detect data inconsistencies."""
        try:
            # Handle case where LLM passes a list instead of string
            if isinstance(check_type, list):
                check_type = check_type[0] if check_type else "data_types"
            
            checker = ConsistencyChecker(self.store)
            results = checker.analyze(check_type)
            
            formatter = TextFormatter()
            context = {
                'format_type': 'analysis_results',
                'analysis_type': check_type
            }
            return formatter.format(results, context)
            
        except Exception as e:
            self.logger.error(f"Error detecting inconsistencies: {str(e)}")
            return f"Error detecting inconsistencies: {str(e)}"


class CompareItemsTool(BaseTool):
    """Tool for comparing files, columns, or other items."""
    
    description = "Compare two items (files, columns, etc.)"
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "item1": {
                    "type": "string",
                    "description": "First item to compare"
                },
                "item2": {
                    "type": "string", 
                    "description": "Second item to compare"
                },
                "comparison_type": {
                    "type": "string",
                    "enum": ["schemas"],
                    "description": "Type of comparison to perform",
                    "default": "schemas"
                }
            },
            "required": ["item1", "item2"]
        }
    
    def execute(self, item1: str, item2: str, comparison_type: str = "schemas") -> str:
        """Compare two items."""
        try:
            if comparison_type == "schemas":
                return self._compare_schemas(item1, item2)
            else:
                return f"Unsupported comparison type: {comparison_type}"
                
        except Exception as e:
            self.logger.error(f"Error comparing items: {str(e)}")
            return f"Error comparing items: {str(e)}"
    
    def _compare_schemas(self, file1_pattern: str, file2_pattern: str) -> str:
        """Compare schemas of two files."""
        # Find files matching patterns
        files = self.store.list_all_files()
        
        file1_matches = [f for f in files if file1_pattern.lower() in f['file_name'].lower()]
        file2_matches = [f for f in files if file2_pattern.lower() in f['file_name'].lower()]
        
        if not file1_matches:
            return f"No files found matching: {file1_pattern}"
        if not file2_matches:
            return f"No files found matching: {file2_pattern}"
        
        # Use first match for each
        file1 = file1_matches[0]
        file2 = file2_matches[0]
        
        schema1 = self.store.get_file_schema(file1['file_name'])
        schema2 = self.store.get_file_schema(file2['file_name'])
        
        if not schema1:
            return f"No schema found for: {file1['file_name']}"
        if not schema2:
            return f"No schema found for: {file2['file_name']}"
        
        # Compare schemas
        cols1 = {col['column_name']: col['data_type'] for col in schema1}
        cols2 = {col['column_name']: col['data_type'] for col in schema2}
        
        common_columns = set(cols1.keys()) & set(cols2.keys())
        file1_only = set(cols1.keys()) - set(cols2.keys())
        file2_only = set(cols2.keys()) - set(cols1.keys())
        
        result = [
            f"Schema Comparison:",
            f"  {file1['file_name']} vs {file2['file_name']}",
            "",
            f"Common columns ({len(common_columns)}):"
        ]
        
        for col in sorted(common_columns):
            type_match = "✓" if cols1[col] == cols2[col] else "✗"
            result.append(f"  {type_match} {col}: {cols1[col]} vs {cols2[col]}")
        
        if file1_only:
            result.append(f"\nOnly in {file1['file_name']} ({len(file1_only)}):")
            for col in sorted(file1_only):
                result.append(f"  • {col} ({cols1[col]})")
        
        if file2_only:
            result.append(f"\nOnly in {file2['file_name']} ({len(file2_only)}):")
            for col in sorted(file2_only):
                result.append(f"  • {col} ({cols2[col]})")
        
        return "\n".join(result)


class RunAnalysisTool(BaseTool):
    """Tool for handling complex analysis requests."""
    
    description = "Handle complex analysis requests that don't fit standard patterns"
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Natural language description of the analysis needed"
                }
            },
            "required": ["description"]
        }
    
    def execute(self, description: str) -> str:
        """Handle complex analysis requests."""
        try:
            desc_lower = description.lower()
            
            # Map common patterns to specific tools
            if "similar" in desc_lower and ("schema" in desc_lower or "column" in desc_lower):
                analyzer = RelationshipAnalyzer(self.store)
                results = analyzer.analyze("similar_schemas", threshold=3)
                formatter = TextFormatter()
                context = {'format_type': 'analysis_results', 'analysis_type': 'similar_schemas'}
                return formatter.format(results, context)
            
            elif "most columns" in desc_lower or "largest" in desc_lower:
                return self._find_largest_files()
            
            elif "type mismatch" in desc_lower or "inconsistent" in desc_lower:
                checker = ConsistencyChecker(self.store)
                results = checker.analyze("data_types")
                formatter = TextFormatter()
                context = {'format_type': 'analysis_results', 'analysis_type': 'data_types'}
                return formatter.format(results, context)
            
            else:
                return (f"For this analysis: '{description}', try using these specific tools:\n"
                       f"• search_metadata() - for searching columns, files, or types\n"
                       f"• get_schemas() - for schema information\n"
                       f"• find_relationships() - for common columns or similar schemas\n"
                       f"• detect_inconsistencies() - for data type or naming issues\n"
                       f"• compare_items() - for comparing two specific files")
                
        except Exception as e:
            self.logger.error(f"Error in analysis: {str(e)}")
            return f"Error performing analysis: {str(e)}"
    
    def _find_largest_files(self) -> str:
        """Find files with the most columns."""
        files = self.store.list_all_files()
        file_sizes = []
        
        for file_info in files:
            schema = self.store.get_file_schema(file_info['file_name'])
            if schema:
                file_sizes.append({
                    'file_name': file_info['file_name'],
                    'column_count': len(schema),
                    'total_rows': file_info.get('total_rows', 'N/A')
                })
        
        # Sort by column count descending
        file_sizes.sort(key=lambda x: x['column_count'], reverse=True)
        
        result = ["Files with most columns:", ""]
        
        for i, file_info in enumerate(file_sizes[:10], 1):
            result.append(f"{i}. {file_info['file_name']}")
            result.append(f"   Columns: {file_info['column_count']}, "
                         f"Rows: {file_info['total_rows']}")
            result.append("")
        
        return "\n".join(result)
