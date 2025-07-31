#!/usr/bin/env python3
"""
End-to-End Tests for TableTalk

Simple, focused tests to ensure core functionality works.
Run with: python scripts/run_tests.py
"""

import pytest
import sys
from pathlib import Path
from typing import List, Tuple

# Test queries to validate LLM functionality
TEST_QUERIES = [
    "what files do we have",
    "show me the customers schema", 
    "describe the orders file",
    "find data quality issues",
    "detect type mismatches",
    "which files have customer_id",
    "compare schemas across files",
    "what data types are in customers file"
]

# Expected response validation rules
EXPECTED_RESPONSES = {
    "what files do we have": {
        "should_contain": ["scanned files", "customers.csv", "orders.csv", "reviews.csv", "legacy_users.csv"],
        "should_not_contain": ["error", "failed"],
        "min_length": 100,
    },
    "show me the customers schema": {
        "should_contain": ["customers.csv", "customer_id", "email", "first_name", "last_name", "is_active"],
        "should_not_contain": ["error", "not found"],
        "min_length": 150,
    },
    "describe the orders file": {
        "should_contain": ["orders.csv", "customer_id", "order_id", "price", "product_name"],
        "should_not_contain": ["error", "not found"],
        "min_length": 150,
    },
    "find data quality issues": {
        "should_contain": ["type mismatches", "legacy_users.csv", "is_active", "price"],
        "should_not_contain": ["no issues found"],
        "min_length": 200,
    },
    "detect type mismatches": {
        "should_contain": ["type mismatches found", "is_active", "price"],
        "should_not_contain": ["no mismatches"],
        "min_length": 150,
    },
    "which files have customer_id": {
        "should_contain": ["customer_id", "customers.csv", "legacy_users.csv", "orders.csv"],
        "should_not_contain": ["not found", "no files"],
        "min_length": 100,
    },
    "compare schemas across files": {
        "should_contain": ["common columns", "customer_id", "type mismatch"],
        "should_not_contain": ["no common columns"],
        "min_length": 300,
    },
    "what data types are in customers file": {
        "should_contain": ["customers.csv", "customer_id", "email", "(integer)", "(string)"],
        "should_not_contain": ["error", "not found"],
        "min_length": 150,
    },
}


@pytest.fixture(scope="session")
def tabletalk_runner():
    """Set up TableTalk for testing."""
    from main import run_tabletalk_commands
    
    def _run_commands(commands: List[str]) -> List[Tuple[str, str, bool]]:
        try:
            return run_tabletalk_commands(commands)
        except Exception as e:
            return [("error", str(e), False)]
    
    return _run_commands


@pytest.fixture(scope="session")
def sample_data_dir():
    """Sample data directory fixture."""
    data_dir = Path(__file__).parent.parent / "data" / "sample"
    if not data_dir.exists():
        pytest.skip(f"Sample data directory not found: {data_dir}")
    return str(data_dir)


def validate_response(query: str, response: str) -> Tuple[bool, str]:
    """Validate response against expected patterns."""
    if query not in EXPECTED_RESPONSES:
        return True, "No validation rules"
    
    expected = EXPECTED_RESPONSES[query]
    
    # Check minimum length
    if len(response) < expected["min_length"]:
        return False, f"Response too short: {len(response)} < {expected['min_length']}"
    
    # Check required content
    response_lower = response.lower()
    for required in expected["should_contain"]:
        if required.lower() not in response_lower:
            return False, f"Missing: '{required}'"
    
    # Check forbidden content
    for forbidden in expected["should_not_contain"]:
        if forbidden.lower() in response_lower:
            return False, f"Contains forbidden: '{forbidden}'"
    
    return True, "Valid"


class TestTableTalkBasics:
    """Test basic TableTalk functionality."""
    
    def test_application_startup(self, tabletalk_runner):
        """Test application startup."""
        results = tabletalk_runner(["/help"])
        assert len(results) > 0, "No results returned"
        
        command, response, success = results[0]
        assert success, f"Help command failed: {response}"
        assert "TableTalk" in response or "help" in response.lower()
    
    def test_file_scanning(self, tabletalk_runner, sample_data_dir):
        """Test file scanning."""
        commands = [f"/scan {sample_data_dir}", "/status"]
        results = tabletalk_runner(commands)
        
        assert len(results) >= 2, "Expected scan + status results"
        
        # Check scan
        scan_command, scan_response, scan_success = results[0]
        assert scan_success, f"Scan failed: {scan_response}"
        
        # Check status
        status_command, status_response, status_success = results[1]
        assert status_success, f"Status failed: {status_response}"
        assert "files" in status_response.lower()


class TestTableTalkQueries:
    """Test natural language queries."""
    
    @pytest.mark.parametrize("query", TEST_QUERIES)
    def test_query(self, tabletalk_runner, sample_data_dir, query):
        """Test individual queries."""
        commands = [f"/scan {sample_data_dir}", query]
        results = tabletalk_runner(commands)
        
        assert len(results) >= 2, f"Expected scan + query results for: {query}"
        
        # Check scan worked
        scan_command, scan_response, scan_success = results[0]
        assert scan_success, f"Scan failed for '{query}': {scan_response}"
        
        # Check query worked
        query_command, query_response, query_success = results[1]
        assert query_success, f"Query '{query}' failed: {query_response}"
        assert len(query_response) > 50, f"Response too short for '{query}'"
        
        # Validate response content
        is_valid, validation_message = validate_response(query, query_response)
        assert is_valid, f"Response validation failed for '{query}': {validation_message}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
