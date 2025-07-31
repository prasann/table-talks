# TableTalk Tests

Simple end-to-end tests to ensure TableTalk functionality works correctly.

## Quick Start

```bash
# Run all tests
python scripts/run_tests.py

# Or run tests directly with pytest
PYTHONPATH=src pytest tests/test_end_to_end.py -v
```

## What Gets Tested

### Basic Functionality
- ✅ Application startup (`/help` command)
- ✅ File scanning (`/scan` and `/status` commands)

### Natural Language Queries
- ✅ File listing: "what files do we have"
- ✅ Schema inspection: "show me the customers schema"
- ✅ File description: "describe the orders file"
- ✅ Data quality analysis: "find data quality issues"
- ✅ Type checking: "detect type mismatches"
- ✅ Column search: "which files have customer_id"
- ✅ Schema comparison: "compare schemas across files"
- ✅ Data type inspection: "what data types are in customers file"

## Response Validation

Each query response is validated for:
- **Content**: Must contain expected keywords/phrases
- **Length**: Minimum response length requirements
- **Quality**: Should not contain error messages

## Test Structure

```
tests/
├── test_end_to_end.py    # Main test file
├── conftest.py          # pytest configuration  
└── README.md           # This file
```

## Requirements

- **Sample Data**: Tests use `data/sample/` directory
- **Ollama**: Must be running for LLM queries
- **Dependencies**: Install with `pip install -r requirements.txt`

## Troubleshooting

### Import Errors
```bash
# Ensure PYTHONPATH includes src
export PYTHONPATH=src
pytest tests/test_end_to_end.py -v
```

### Sample Data Missing
```bash
# Check data directory exists
ls data/sample/
# Should show: customers.csv, orders.csv, reviews.csv, legacy_users.csv
```

### Ollama Not Running
```bash
# Start Ollama
ollama serve

# Check if model is available
ollama list
```

## Understanding Test Output

### ✅ Success
```
test_query[what files do we have] PASSED
```

### ❌ Failure
```
FAILED tests/test_end_to_end.py::TestTableTalkQueries::test_query[find data quality issues] 
AssertionError: Response validation failed for 'find data quality issues': Missing: 'type mismatches'
```

## Modifying Tests

To update validation rules, edit `EXPECTED_RESPONSES` in `test_end_to_end.py`:

```python
EXPECTED_RESPONSES = {
    "your query": {
        "should_contain": ["required", "keywords"],
        "should_not_contain": ["error", "failed"], 
        "min_length": 100,
    }
}
```
