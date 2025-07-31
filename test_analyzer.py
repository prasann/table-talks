#!/usr/bin/env python3
"""Direct test of schema analyzer functionality."""

import sys
sys.path.append('.')

from src.analysis.schema_analyzer import create_schema_analyzer

def test_schema_analyzer():
    """Test the schema analyzer directly."""
    print("Testing schema analyzer...")
    
    try:
        analyzer = create_schema_analyzer('./database/metadata.duckdb')
        if analyzer:
            print("✓ Schema analyzer created successfully")
            
            # Test search columns
            result = analyzer.search_columns('customer_id')
            print(f"✓ Search columns result: {result[:200]}...")
            
            # Test list files
            result = analyzer.list_files()
            print(f"✓ List files result: {result[:200]}...")
            
        else:
            print("✗ Failed to create schema analyzer")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_schema_analyzer()
