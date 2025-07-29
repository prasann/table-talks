"""Tests for MetadataStore."""

import pytest
import tempfile
import os
from pathlib import Path

from src.metadata.metadata_store import MetadataStore


class TestMetadataStore:
    """Test cases for MetadataStore class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.duckdb")
        self.store = MetadataStore(self.db_path)
        
        # Sample test data
        self.sample_schema = [
            {
                'file_name': 'test.csv',
                'file_path': '/tmp/test.csv',
                'column_name': 'id',
                'data_type': 'integer',
                'null_count': 0,
                'unique_count': 100,
                'total_rows': 100,
                'file_size_mb': 0.1
            },
            {
                'file_name': 'test.csv',
                'file_path': '/tmp/test.csv',
                'column_name': 'name',
                'data_type': 'string',
                'null_count': 5,
                'unique_count': 95,
                'total_rows': 100,
                'file_size_mb': 0.1
            }
        ]
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove temporary database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_store_and_retrieve_schema(self):
        """Test storing and retrieving schema information."""
        # Store schema
        self.store.store_schema_info(self.sample_schema)
        
        # Retrieve schema
        result = self.store.get_file_schema('test.csv')
        
        assert len(result) == 2
        assert result[0]['column_name'] == 'id'
        assert result[1]['column_name'] == 'name'
    
    def test_list_files(self):
        """Test listing all files."""
        # Store schema
        self.store.store_schema_info(self.sample_schema)
        
        # List files
        files = self.store.list_all_files()
        
        assert len(files) == 1
        assert files[0]['file_name'] == 'test.csv'
        assert files[0]['column_count'] == 2
    
    def test_find_columns_by_name(self):
        """Test finding columns by name."""
        # Store schema
        self.store.store_schema_info(self.sample_schema)
        
        # Find columns
        results = self.store.find_columns_by_name('id')
        
        assert len(results) == 1
        assert results[0]['column_name'] == 'id'
        assert results[0]['file_name'] == 'test.csv'
    
    def test_database_stats(self):
        """Test database statistics."""
        # Store schema
        self.store.store_schema_info(self.sample_schema)
        
        # Get stats
        stats = self.store.get_database_stats()
        
        assert stats['total_files'] == 1
        assert stats['total_columns'] == 2
        assert stats['unique_columns'] == 2
