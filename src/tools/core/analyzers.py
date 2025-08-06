"""Analysis strategy implementations for complex metadata operations."""

import pandas as pd
from typing import List, Dict, Any
from .base_components import BaseAnalyzer

class RelationshipAnalyzer(BaseAnalyzer):
    """Analyzer for finding relationships between files and columns."""
    
    def analyze(self, analysis_type: str, **kwargs) -> List[Dict[str, Any]]:
        """Perform relationship analysis based on type."""
        if analysis_type == "common_columns":
            return self._find_common_columns(**kwargs)
        elif analysis_type == "similar_schemas":
            return self._find_similar_schemas(**kwargs)
        elif analysis_type == "schema_differences":
            return self._find_schema_differences(**kwargs)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    def _find_common_columns(self, threshold: int = 2) -> List[Dict[str, Any]]:
        """Find columns that appear in multiple files."""
        try:
            return self._find_common_columns_pandas(threshold)                
        except Exception as e:
            self.logger.error(f"Error finding common columns: {str(e)}")
            raise
    

    def _find_common_columns_pandas(self, threshold: int) -> List[Dict[str, Any]]:
        """Pandas implementation for better performance."""
        # Get all metadata as DataFrame
        all_metadata = []
        files = self.store.list_all_files()
        
        for file_info in files:
            schema = self.store.get_file_schema(file_info['file_name'])
            if schema:
                for col in schema:
                    all_metadata.append({
                        'file_name': file_info['file_name'],
                        'column_name': col['column_name'],
                        'data_type': col['data_type']
                    })
        
        if not all_metadata:
            return []
        
        df = pd.DataFrame(all_metadata)
        
        # Group by column name and aggregate
        common_cols = df.groupby('column_name').agg({
            'file_name': lambda x: list(x),
            'data_type': lambda x: list(set(x))
        }).reset_index()
        
        # Filter by threshold and format
        common_cols['file_count'] = common_cols['file_name'].apply(len)
        common_cols = common_cols[common_cols['file_count'] >= threshold]
        
        result = []
        for _, row in common_cols.iterrows():
            result.append({
                'column_name': row['column_name'],
                'file_count': row['file_count'],
                'files': row['file_name'],
                'data_types': row['data_type']
            })
        
        return sorted(result, key=lambda x: x['file_count'], reverse=True)
    
    def _find_similar_schemas(self, threshold: int = 3) -> List[Dict[str, Any]]:
        """Find files with similar schema structures."""
        try:
            return self._find_similar_schemas_pandas(threshold)                
        except Exception as e:
            self.logger.error(f"Error finding similar schemas: {str(e)}")
            raise
    
    def _find_similar_schemas_pandas(self, threshold: int) -> List[Dict[str, Any]]:
        """Pandas implementation for finding similar schemas."""
        return self._find_similar_schemas_basic(threshold)
    
    def _find_similar_schemas_basic(self, threshold: int) -> List[Dict[str, Any]]:
        """Basic implementation for finding files with similar schema structures."""
        try:
            files = self.store.list_all_files()
            if len(files) < 2:
                return []

            # Get schemas for all files
            file_schemas = {}
            for file_info in files:
                schema = self.store.get_file_schema(file_info['file_name'])
                if schema:
                    file_schemas[file_info['file_name']] = set(col['column_name'] for col in schema)

            # Find files with similar schemas
            similar_groups = []
            processed_files = set()

            for file1, schema1 in file_schemas.items():
                if file1 in processed_files:
                    continue

                similar_files = [file1]

                for file2, schema2 in file_schemas.items():
                    if file2 == file1 or file2 in processed_files:
                        continue

                    # Calculate similarity (Jaccard similarity)
                    intersection = len(schema1 & schema2)
                    union = len(schema1 | schema2)

                    if union > 0:
                        similarity = intersection / union

                        # Use threshold as percentage (e.g., threshold=3 means 30% similarity)
                        similarity_threshold = threshold / 10.0 if threshold <= 10 else 0.3

                        if similarity >= similarity_threshold:
                            similar_files.append(file2)

                if len(similar_files) > 1:
                    # Calculate common columns
                    common_columns = file_schemas[similar_files[0]]
                    for similar_file in similar_files[1:]:
                        common_columns &= file_schemas[similar_file]

                    similar_groups.append({
                        'group_files': similar_files,
                        'common_columns': list(common_columns),
                        'common_column_count': len(common_columns),
                        'similarity_score': round(len(common_columns) / max(len(file_schemas[f]) for f in similar_files), 2)
                    })

                    # Mark files as processed
                    for file in similar_files:
                        processed_files.add(file)

            return similar_groups
        
        except Exception as e:
            self.logger.error(f"Error in _find_similar_schemas_basic: {str(e)}")
            return []
    
    def _find_schema_differences(self, **kwargs) -> List[Dict[str, Any]]:
        """Find differences between schemas (basic version without semantic analysis)."""
        try:
            files = self.store.list_all_files()
            if len(files) < 2:
                return []
            
            # Get schemas for all files
            file_schemas = {}
            for file_info in files:
                schema = self.store.get_file_schema(file_info['file_name'])
                if schema:
                    # Convert to dict with data types
                    schema_dict = {}
                    for col_info in schema:
                        schema_dict[col_info['column_name']] = col_info['data_type']
                    file_schemas[file_info['file_name']] = schema_dict
            
            # Compare all pairs of files
            differences = []
            file_names = list(file_schemas.keys())
            
            for i, file1 in enumerate(file_names):
                for file2 in file_names[i+1:]:
                    diff = self._basic_schema_diff(file1, file_schemas[file1], 
                                                 file2, file_schemas[file2])
                    if diff:
                        differences.append(diff)
            
            return differences
            
        except Exception as e:
            self.logger.error(f"Error finding schema differences: {str(e)}")
            return []
    
    def _basic_schema_diff(self, file1: str, schema1: dict, file2: str, schema2: dict) -> dict:
        """Basic schema difference analysis without semantic capabilities."""
        cols1_set = set(schema1.keys())
        cols2_set = set(schema2.keys())
        
        common_columns = cols1_set & cols2_set
        unique_to_file1 = {col: schema1[col] for col in cols1_set - cols2_set}
        unique_to_file2 = {col: schema2[col] for col in cols2_set - cols1_set}
        
        # Check for type mismatches in common columns
        type_mismatches = []
        for col in common_columns:
            if schema1[col] != schema2[col]:
                type_mismatches.append({
                    'column': col,
                    'type1': schema1[col],
                    'type2': schema2[col]
                })
        
        # Calculate basic similarity
        total_columns = len(cols1_set | cols2_set)
        matching_columns = len(common_columns) - len(type_mismatches)
        similarity = matching_columns / total_columns if total_columns > 0 else 0.0
        
        return {
            'file1': file1,
            'file2': file2,
            'similarity': similarity,
            'common_columns_count': len(common_columns),
            'unique_to_file1_count': len(unique_to_file1),
            'unique_to_file2_count': len(unique_to_file2),
            'type_mismatches_count': len(type_mismatches),
            'unique_to_file1': unique_to_file1,
            'unique_to_file2': unique_to_file2,
            'type_mismatches': type_mismatches
        }


class ConsistencyChecker(BaseAnalyzer):
    """Analyzer for detecting data consistency issues."""
    
    def analyze(self, analysis_type: str, **kwargs) -> List[Dict[str, Any]]:
        """Perform consistency analysis based on type."""
        if analysis_type == "data_types":
            return self._detect_type_mismatches(**kwargs)
        elif analysis_type == "naming_patterns":
            return self._detect_naming_inconsistencies(**kwargs)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    def _detect_type_mismatches(self) -> List[Dict[str, Any]]:
        """Detect columns with same name but different data types."""
        try:
            files = self.store.list_all_files()
            column_types = {}
            
            # Collect all columns and their types
            for file_info in files:
                schema = self.store.get_file_schema(file_info['file_name'])
                if schema:
                    for col in schema:
                        col_name = col['column_name']
                        if col_name not in column_types:
                            column_types[col_name] = {}
                        
                        data_type = col['data_type']
                        if data_type not in column_types[col_name]:
                            column_types[col_name][data_type] = []
                        column_types[col_name][data_type].append(file_info['file_name'])
            
            # Find mismatches
            mismatches = []
            for col_name, type_files in column_types.items():
                if len(type_files) > 1:  # Multiple data types for same column
                    mismatches.append({
                        'column_name': col_name,
                        'type_variations': {
                            data_type: files for data_type, files in type_files.items()
                        },
                        'total_files': sum(len(files) for files in type_files.values())
                    })
            
            return sorted(mismatches, key=lambda x: x['total_files'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error detecting type mismatches: {str(e)}")
            raise
    
    def _detect_naming_inconsistencies(self) -> List[Dict[str, Any]]:
        """Detect potential naming inconsistencies (similar column names)."""
        try:
            files = self.store.list_all_files()
            all_columns = set()
            
            # Collect all unique column names
            for file_info in files:
                schema = self.store.get_file_schema(file_info['file_name'])
                if schema:
                    for col in schema:
                        all_columns.add(col['column_name'])
            
            # Find potential naming inconsistencies
            # This is a basic implementation - could be enhanced with fuzzy matching
            inconsistencies = []
            column_list = sorted(all_columns)
            
            for i, col1 in enumerate(column_list):
                for col2 in column_list[i+1:]:
                    # Simple similarity check (could be enhanced)
                    if self._are_similar_names(col1, col2):
                        inconsistencies.append({
                            'column1': col1,
                            'column2': col2,
                            'similarity_reason': self._get_similarity_reason(col1, col2)
                        })
            
            return inconsistencies
            
        except Exception as e:
            self.logger.error(f"Error detecting naming inconsistencies: {str(e)}")
            raise
    
    def _are_similar_names(self, name1: str, name2: str) -> bool:
        """Check if two column names are similar enough to be potentially inconsistent."""
        # Basic similarity checks
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        # Check for similar prefixes/suffixes
        if (name1_lower.startswith(name2_lower[:4]) or 
            name2_lower.startswith(name1_lower[:4]) or
            name1_lower.endswith(name2_lower[-4:]) or 
            name2_lower.endswith(name1_lower[-4:])):
            return True
        
        # Check for underscore vs camelCase variations
        name1_normalized = name1_lower.replace('_', '')
        name2_normalized = name2_lower.replace('_', '')
        if name1_normalized == name2_normalized:
            return True
        
        return False
    
    def _get_similarity_reason(self, name1: str, name2: str) -> str:
        """Get reason why two names are considered similar."""
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        if name1_lower.replace('_', '') == name2_lower.replace('_', ''):
            return "underscore_variation"
        elif (name1_lower.startswith(name2_lower[:4]) or name2_lower.startswith(name1_lower[:4])):
            return "similar_prefix"
        elif (name1_lower.endswith(name2_lower[-4:]) or name2_lower.endswith(name1_lower[-4:])):
            return "similar_suffix"
        else:
            return "other_similarity"
