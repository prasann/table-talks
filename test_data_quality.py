#!/usr/bin/env python3
"""Test data quality analysis"""

import sys
sys.path.insert(0, '.')

from src.main import run_tabletalk_commands

# Test data quality analysis
test_commands = [
    'Analyze the data quality of the customers table'
]

print("Testing data quality analysis...")
run_tabletalk_commands(test_commands)
