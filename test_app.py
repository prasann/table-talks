#!/usr/bin/env python3
"""Test script for TableTalk functionality."""

import sys
sys.path.append('.')

from src.main import run_tabletalk_commands

def test_tabletalk():
    """Test TableTalk commands."""
    print("Testing TableTalk functionality...")
    
    # Test commands
    commands = [
        "/status",
        "/help", 
        "which tables have customer_id columns",
        "show me all tables",
        "/exit"
    ]
    
    results = run_tabletalk_commands(commands)
    
    for command, response, success in results:
        print(f"\n{'='*50}")
        print(f"Command: {command}")
        print(f"Success: {success}")
        print(f"Response:")
        print(response)

if __name__ == "__main__":
    test_tabletalk()
