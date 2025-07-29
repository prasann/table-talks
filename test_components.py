#!/usr/bin/env python3
"""Quick test script for TableTalk functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from metadata.metadata_store import MetadataStore
from metadata.schema_extractor import SchemaExtractor
from tools.schema_tools import SchemaTools

def test_basic_functionality():
    """Test the core components work."""
    print("🧪 Testing TableTalk components...")
    
    # Test 1: Database
    print("1. Testing database...")
    store = MetadataStore('./database/test.duckdb')
    stats = store.get_database_stats()
    print(f"   ✅ Database initialized: {stats}")
    
    # Test 2: Schema extraction
    print("2. Testing schema extraction...")
    extractor = SchemaExtractor()
    try:
        schema = extractor.extract_from_file('data/sample/orders.csv')
        print(f"   ✅ Extracted schema: {len(schema)} columns")
        
        # Store in database
        store.store_schema_info(schema)
        print("   ✅ Stored in database")
    except Exception as e:
        print(f"   ❌ Schema extraction failed: {e}")
        return False
    
    # Test 3: Tools
    print("3. Testing schema tools...")
    tools = SchemaTools(store)
    try:
        result = tools.get_file_schema('orders.csv')
        print(f"   ✅ Tool response: {len(result)} characters")
        print(f"   Preview: {result[:100]}...")
    except Exception as e:
        print(f"   ❌ Tools failed: {e}")
        return False
    
    print("🎉 All tests passed!")
    return True

if __name__ == "__main__":
    test_basic_functionality()
