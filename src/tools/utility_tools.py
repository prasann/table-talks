"""Utility tools for comparisons and analysis."""

from typing import Dict, Any
from .core.base_components import BaseTool
from .core.analyzers import RelationshipAnalyzer, ConsistencyChecker
from .core.formatters import TextFormatter


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
            "required": ["item1", "item2"],
            "additionalProperties": False
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
            "required": ["description"],
            "additionalProperties": False
        }
    
    def execute(self, description: str) -> str:
        """Handle complex analysis requests."""
        try:
            desc_lower = description.lower()
            
            # Map common patterns to specific tools - actually execute analysis
            if any(word in desc_lower for word in ["similar", "comparison", "compare"]) and any(word in desc_lower for word in ["schema", "column", "table"]):
                # Execute similarity analysis
                analyzer = RelationshipAnalyzer(self.store)
                results = analyzer.analyze("similar_schemas", threshold=3)
                formatter = TextFormatter()
                context = {'format_type': 'analysis_results', 'analysis_type': 'similar_schemas'}
                return formatter.format(results, context)
            
            elif any(word in desc_lower for word in ["most columns", "largest", "biggest", "column count"]):
                # Execute file size analysis
                return self._find_largest_files()
            
            elif any(word in desc_lower for word in ["type mismatch", "inconsistent", "data type", "quality"]):
                # Execute consistency check
                checker = ConsistencyChecker(self.store)
                results = checker.analyze("data_types")
                formatter = TextFormatter()
                context = {'format_type': 'analysis_results', 'analysis_type': 'data_types'}
                return formatter.format(results, context)
            
            elif any(word in desc_lower for word in ["relationship", "connection", "related", "common"]):
                # Execute relationship analysis
                analyzer = RelationshipAnalyzer(self.store)
                results = analyzer.analyze("common_columns", threshold=2)
                formatter = TextFormatter()
                context = {'format_type': 'analysis_results', 'analysis_type': 'common_columns'}
                return formatter.format(results, context)
            
            elif any(word in desc_lower for word in ["statistics", "stats", "summary", "overview"]):
                # Execute statistical analysis
                return self._generate_statistics_summary()
            
            elif any(word in desc_lower for word in ["anomal", "outlier", "unusual", "suspicious"]):
                # Execute anomaly detection
                return self._detect_anomalies()
            
            else:
                # For unrecognized patterns, try to infer the best analysis approach
                return self._infer_and_execute_analysis(description)
                
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
    
    def _generate_statistics_summary(self) -> str:
        """Generate overall statistics summary."""
        try:
            files = self.store.list_all_files()
            total_files = len(files)
            total_rows = sum(f.get('total_rows', 0) for f in files if f.get('total_rows'))
            
            # Schema information
            total_columns = 0
            data_types = {}
            
            for file_info in files:
                schema = self.store.get_file_schema(file_info['file_name'])
                if schema:
                    total_columns += len(schema)
                    for col in schema:
                        dt = col.get('data_type', 'unknown')
                        data_types[dt] = data_types.get(dt, 0) + 1
            
            result = [
                "Dataset Statistics Summary:",
                f"  Total Files: {total_files}",
                f"  Total Rows: {total_rows:,}" if total_rows else "  Total Rows: Unknown",
                f"  Total Columns: {total_columns}",
                "",
                "Data Type Distribution:"
            ]
            
            for dtype, count in sorted(data_types.items(), key=lambda x: x[1], reverse=True):
                result.append(f"  {dtype}: {count} columns")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"Error generating statistics: {str(e)}"
    
    def _detect_anomalies(self) -> str:
        """Detect potential anomalies in the data."""
        try:
            checker = ConsistencyChecker(self.store)
            
            # Check for various types of anomalies
            anomalies = []
            
            # Data type inconsistencies
            try:
                type_issues = checker.analyze("data_types")
                if type_issues:
                    anomalies.append("Data Type Inconsistencies:")
                    anomalies.append(str(type_issues))
            except Exception:
                pass  # Skip if data_types analysis fails
                
            # Naming inconsistencies  
            try:
                naming_issues = checker.analyze("naming_patterns")
                if naming_issues:
                    anomalies.append("\nNaming Pattern Issues:")
                    anomalies.append(str(naming_issues))
            except Exception:
                pass  # Skip if naming_patterns analysis fails
            
            if not anomalies:
                return "No significant anomalies detected in the dataset."
            
            return "\n".join(anomalies)
            
        except Exception as e:
            return f"Error detecting anomalies: {str(e)}"
    
    def _infer_and_execute_analysis(self, description: str) -> str:
        """Infer the best analysis approach for unclear requests."""
        try:
            # Try to extract meaningful keywords and map to analysis
            keywords = description.lower().split()
            
            # Look for data-related keywords
            if any(word in keywords for word in ['data', 'dataset', 'information']):
                return self._generate_statistics_summary()
            
            # Look for schema-related keywords
            elif any(word in keywords for word in ['structure', 'format', 'schema']):
                analyzer = RelationshipAnalyzer(self.store)
                results = analyzer.analyze("similar_schemas", threshold=2)
                formatter = TextFormatter()
                context = {'format_type': 'analysis_results', 'analysis_type': 'similar_schemas'}
                return formatter.format(results, context)
            
            # Look for problem-related keywords
            elif any(word in keywords for word in ['problem', 'issue', 'error', 'wrong']):
                return self._detect_anomalies()
            
            # Default to general overview
            else:
                return self._generate_statistics_summary()
                
        except Exception as e:
            return f"Error inferring analysis type: {str(e)}"
