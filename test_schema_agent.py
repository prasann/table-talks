#!/usr/bin/env python3
"""Test SchemaAgent consolidation"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from agent.schema_agent import SchemaAgent
    from metadata.metadata_store import MetadataStore
    from tools.schema_tools import SchemaTools
    
    print("✅ All imports successful!")
    
    # Quick functionality test
    store = MetadataStore("./database/test.duckdb")
    tools = SchemaTools(store)
    agent = SchemaAgent(tools, model_name="phi3")
    
    print(f"✅ SchemaAgent initialized: {agent.get_status()['mode']} mode")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
