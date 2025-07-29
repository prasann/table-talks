#!/usr/bin/env python3
"""Test script to check for datatype issues in test files."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.metadata.metadata_store import MetadataStore
from src.tools.schema_tools import SchemaTools
from src.metadata.schema_extractor import SchemaExtractor
from pathlib import Path

def main():
    print("🔍 Testing datatype detection...")
    
    # Initialize components
    metadata_store = MetadataStore()
    schema_extractor = SchemaExtractor()
    schema_tools = SchemaTools(metadata_store)
    
    # Scan test data files
    test_data_dir = Path("test_data")
    if not test_data_dir.exists():
        print("❌ test_data directory not found!")
        return
    
    print(f"\n📂 Scanning {test_data_dir.resolve()}...")
    
    file_count = 0
    for file_path in test_data_dir.rglob("*.csv"):
        try:
            schema_info = schema_extractor.extract_from_file(str(file_path))
            if schema_info:
                metadata_store.store_schema_info(schema_info)
                print(f"✅ {file_path.name}: {len(schema_info)} columns")
                file_count += 1
        except Exception as e:
            print(f"❌ {file_path.name}: {e}")
    
    print(f"\n📊 Scanned {file_count} files successfully!")
    
    if file_count == 0:
        print("No files were scanned. Exiting.")
        return
    
    # Test semantic type issues
    print("\n🔍 Checking for semantic datatype issues...")
    semantic_issues = schema_tools.detect_semantic_type_issues()
    print(semantic_issues)
    
    # Test column name variations
    print("\n🔍 Checking for column name variations...")
    name_variations = schema_tools.detect_column_name_variations()
    print(name_variations)
    
    # Test type mismatches
    print("\n🔍 Checking for type mismatches...")
    type_mismatches = schema_tools.detect_type_mismatches()
    print(type_mismatches)

if __name__ == "__main__":
    main()
