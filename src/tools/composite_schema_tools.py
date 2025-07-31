"""Composite schema tools - simple multi-step operations, let LLM handle complex reasoning."""

from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from metadata.metadata_store import MetadataStore
from tools.atomic_schema_tools import AtomicSchemaTools


class CompositeSchemaTools:
    """Simple composite tools that perform basic multi-step operations.
    
    Complex analysis and reasoning is delegated to the LLM through multi-turn tool calling.
    """
    
    def __init__(self, metadata_store: MetadataStore, atomic_tools: AtomicSchemaTools):
        """Initialize composite schema tools.
        
        Args:
            metadata_store: MetadataStore instance
            atomic_tools: AtomicSchemaTools instance for basic operations
        """
        self.store = metadata_store
        self.atomic = atomic_tools
        self.logger = get_logger("tabletalk.composite_tools")
    
    # ============================================================================
    # Simple Database Queries - Direct data retrieval without complex logic
    # ============================================================================
    
    def detect_type_mismatches(self) -> str:
        """Find columns with same name but different types across files.
        
        Simple database query - LLM can analyze results for recommendations.
        
        Returns:
            Formatted string with type mismatch information
        """
        try:
            mismatches = self.store.detect_type_mismatches()
            
            if not mismatches:
                return "No type mismatches found across files."
            
            # Simple grouping and formatting
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
    
    def find_common_columns(self) -> str:
        """Find columns that appear in multiple files.
        
        Simple database query - LLM can analyze for relationships and recommendations.
        
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
    
    def compare_two_files(self, file1: str, file2: str) -> str:
        """Compare schemas between two specific files.
        
        Simple comparison - LLM can interpret results and suggest actions.
        
        Args:
            file1: First file name
            file2: Second file name
            
        Returns:
            Formatted string with schema comparison
        """
        try:
            # Use atomic tools to get schemas
            schema1_result = self.atomic.get_file_schema(file1)
            schema2_result = self.atomic.get_file_schema(file2)
            
            # Check for errors
            if "error" in schema1_result.lower() or "not found" in schema1_result.lower():
                return f"Could not get schema for {file1}: {schema1_result}"
            if "error" in schema2_result.lower() or "not found" in schema2_result.lower():
                return f"Could not get schema for {file2}: {schema2_result}"
            
            # Get actual file names and schema data
            files = self.store.list_all_files()
            actual_file1 = self._find_file_name(file1, files)
            actual_file2 = self._find_file_name(file2, files)
            
            if not actual_file1 or not actual_file2:
                return f"Could not find files: {file1}, {file2}"
            
            schema1 = self.store.get_file_schema(actual_file1)
            schema2 = self.store.get_file_schema(actual_file2)
            
            # Simple comparison
            cols1 = {col['column_name']: col for col in schema1}
            cols2 = {col['column_name']: col for col in schema2}
            
            common_cols = set(cols1.keys()) & set(cols2.keys())
            unique_to_file1 = set(cols1.keys()) - set(cols2.keys())
            unique_to_file2 = set(cols2.keys()) - set(cols1.keys())
            
            result = [f"Schema Comparison: {actual_file1} vs {actual_file2}"]
            result.append("")
            
            if common_cols:
                result.append(f"Common columns ({len(common_cols)}):") 
                type_mismatches = []
                for col_name in sorted(common_cols):
                    col1, col2 = cols1[col_name], cols2[col_name]
                    if col1['data_type'] == col2['data_type']:
                        status = "✓"
                        type_info = col1['data_type']
                    else:
                        status = "✗ TYPE MISMATCH"
                        type_info = f"{col1['data_type']} vs {col2['data_type']}"
                        type_mismatches.append(col_name)
                    result.append(f"  {status} {col_name}: {type_info}")
                
                if type_mismatches:
                    result.append(f"\n⚠️  Type mismatch detected in {len(type_mismatches)} column(s): {', '.join(type_mismatches)}")
                result.append("")
            
            if unique_to_file1:
                result.append(f"Only in {actual_file1} ({len(unique_to_file1)}):") 
                for col_name in sorted(unique_to_file1):
                    result.append(f"  - {col_name} ({cols1[col_name]['data_type']})")
                result.append("")
            
            if unique_to_file2:
                result.append(f"Only in {actual_file2} ({len(unique_to_file2)}):") 
                for col_name in sorted(unique_to_file2):
                    result.append(f"  - {col_name} ({cols2[col_name]['data_type']})")
            
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error comparing {file1} and {file2}: {str(e)}")
            return f"Error comparing schemas: {str(e)}"
    
    def analyze_data_quality(self) -> str:
        """Comprehensive data quality analysis combining multiple checks.
        
        Aggregates type mismatches, common column analysis, and basic quality insights.
        For complex semantic analysis, LLM should use atomic tools for deeper investigation.
        
        Returns:
            Formatted string with comprehensive data quality report
        """
        try:
            result = ["🔍 Data Quality Analysis Report"]
            result.append("=" * 50)
            
            # 1. Type Mismatches
            result.append("\n📊 Type Consistency Check:")
            type_mismatches = self.detect_type_mismatches()
            if "No type mismatches found" in type_mismatches:
                result.append("✅ No type mismatches detected across files")
            else:
                result.append(type_mismatches)
            
            # 2. Common Columns Analysis
            result.append("\n🔗 Column Relationships:")
            common_cols = self.find_common_columns()
            if "No common columns found" in common_cols:
                result.append("⚠️  No common columns found - files may not be related")
            else:
                result.append(common_cols)
            
            # 3. Basic Quality Checks
            result.append("\n📋 File Summary:")
            files = self.store.list_all_files()
            total_files = len(files)
            total_columns = sum(f.get('column_count', 0) for f in files)
            
            result.append(f"Total files analyzed: {total_files}")
            result.append(f"Total columns across all files: {total_columns}")
            
            # Check for suspicious patterns
            suspicious_files = []
            for file_info in files:
                if file_info.get('column_count', 0) < 2:
                    suspicious_files.append(f"{file_info['file_name']} (only {file_info.get('column_count', 0)} columns)")
                elif file_info.get('row_count', 0) == 0:
                    suspicious_files.append(f"{file_info['file_name']} (empty file)")
            
            if suspicious_files:
                result.append("\n⚠️  Potential Issues:")
                for issue in suspicious_files:
                    result.append(f"  - {issue}")
            
            # 4. Recommendations
            result.append("\n💡 Recommendations:")
            if "type mismatches found" in type_mismatches.lower():
                result.append("  - Review type mismatches and standardize data types")
            if total_files > 1 and "No common columns found" in common_cols:
                result.append("  - Consider adding relationship keys between files")
            if suspicious_files:
                result.append("  - Review files with structural issues")
            else:
                result.append("  - Data structure appears well-organized")
            
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error in data quality analysis: {str(e)}")
            return f"Error performing data quality analysis: {str(e)}"
    
    # ============================================================================
    # Helper Methods - Simple utilities
    # ============================================================================
    
    def _find_file_name(self, file_name: str, files: List[Dict]) -> Optional[str]:
        """Find actual file name from partial match.
        
        Args:
            file_name: Partial file name
            files: List of file dictionaries
            
        Returns:
            Actual file name or None if not found
        """
        file_name_lower = file_name.lower()
        
        # Try exact match first
        for f in files:
            if f['file_name'].lower() == file_name_lower:
                return f['file_name']
        
        # Try partial match
        matches = [f for f in files if file_name_lower in f['file_name'].lower()]
        if len(matches) == 1:
            return matches[0]['file_name']
        
        return None
