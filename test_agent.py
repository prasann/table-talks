#!/usr/bin/env python3
"""Simple test of the agent functionality."""

import sys
sys.path.append('.')

from src.agent.schema_agent import SchemaAgent

def test_agent():
    """Test the schema agent directly."""
    print("Testing schema agent...")
    
    try:
        # Create agent
        agent = SchemaAgent(
            database_path='./database/metadata.duckdb',
            model_name='phi4-mini-fc',
            base_url='http://localhost:11434'
        )
        print("✓ Agent created successfully")
        
        # Test query
        result = agent.query("which tables have customer_id columns")
        print(f"Query result: {result}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent()
