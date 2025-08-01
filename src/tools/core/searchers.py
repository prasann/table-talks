"""Search strategy implementations for different metadata types."""

from typing import List, Dict, Any
from tools.core.base_components import BaseSearcher

class ColumnSearcher(BaseSearcher):
    """Search strategy for column metadata."""
    
    def search(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for columns containing the search term."""
        try:
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
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Error searching columns for {search_term}: {str(e)}")
            raise


class FileSearcher(BaseSearcher):
    """Search strategy for file metadata."""
    
    def search(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for files matching the search term."""
        try:
            files = self.store.list_all_files()
            matches = []
            search_lower = search_term.lower()
            
            for file_info in files:
                if search_lower in file_info['file_name'].lower():
                    # Get full file info including schema summary
                    schema = self.store.get_file_schema(file_info['file_name'])
                    file_info['column_count'] = len(schema) if schema else 0
                    file_info['columns'] = [col['column_name'] for col in schema] if schema else []
                    matches.append(file_info)
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Error searching files for {search_term}: {str(e)}")
            raise


class TypeSearcher(BaseSearcher):
    """Search strategy for data type metadata."""
    
    def search(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for columns with specific data types."""
        try:
            files = self.store.list_all_files()
            matches = []
            search_lower = search_term.lower()
            
            for file_info in files:
                schema = self.store.get_file_schema(file_info['file_name'])
                if schema:
                    for col in schema:
                        if search_lower in col['data_type'].lower():
                            matches.append({
                                'file_name': file_info['file_name'],
                                'column_name': col['column_name'],
                                'data_type': col['data_type'],
                                'null_count': col['null_count'],
                                'unique_count': col['unique_count']
                            })
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Error searching data types for {search_term}: {str(e)}")
            raise
