"""Comparison and utility tools for complex operations."""

from typing import Dict, List, Any
from .core.base_components import BaseTool
from .core.analyzers import RelationshipAnalyzer, ConsistencyChecker
from .core.formatters import TextFormatter
from .core.searchers import ColumnSearcher


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
