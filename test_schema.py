#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, 'src')

from metadata.schema_extractor import SchemaExtractor

# Test the schema extractor
extractor = SchemaExtractor()

try:
    result = extractor.extract_from_file('data/sample/customers.csv')
    print(f"Schema extraction successful!")
    print(f"Type: {type(result)}")
    print(f"Length: {len(result)}")
    print(f"First item: {result[0] if result else 'Empty'}")
except Exception as e:
    print(f"Error: {e}")
