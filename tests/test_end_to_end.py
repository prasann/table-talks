#!/usr/bin/env python3
"""
End-to-End Tests for TableTalk

Simple, focused tests to ensure core functionality works.
Run with: python -m pytest tests/test_end_to_end.py -v
"""

import pytest
import sys
from pathlib import Path
from typing import List, Tuple

# Core test queries to validate functionality
TEST_QUERIES = [
    "what files do we have",
    "show me the customers schema", 
    "which files have customer_id",
    "find data quality issues"
]

# Expected response validation
EXPECTED_RESPONSES = {
    "what files do we have": {
        "should_contain": ["found", "files", ".csv"],
        "min_length": 50,
    },
    "show me the customers schema": {
        "should_contain": ["customers"],
        "min_length": 40,
    },
    "which files have customer_id": {
        "should_contain": ["customer_id"],
        "min_length": 50,
    },
    "find data quality issues": {
        "should_contain": ["data"],
        "min_length": 40,
    },
}


@pytest.fixture(scope="session")
def tabletalk_runner():
    """Set up TableTalk for testing."""
    import sys
    from pathlib import Path
    
    # Add src to path for test imports
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from src.main import run_tabletalk_commands
    
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
        assert len(query_response) > 30, f"Response too short for '{query}'"
        
        # Validate response content
        is_valid, validation_message = validate_response(query, query_response)
        assert is_valid, f"Response validation failed for '{query}': {validation_message}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
