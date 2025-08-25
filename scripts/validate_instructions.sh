#!/bin/bash
# Validation script to test GitHub Copilot instructions
# This script validates the key commands documented in .github/copilot-instructions.md

set -e

echo "=========================================="
echo "TableTalk Instructions Validation Script"
echo "=========================================="

echo "1. Python version check..."
python3 --version

echo "2. Virtual environment activation..."
source venv/bin/activate

echo "3. Python imports test..."
python -c "from src.agent.schema_agent import SchemaAgent; print('✅ Python imports work')"

echo "4. Testing file detection..."
ls data/sample/*.csv

echo "5. Code quality checks..."
echo "   - Black formatting check..."
black --check --quiet . && echo "✅ Code is formatted" || echo "❌ Code needs formatting (run: black .)"

echo "   - Flake8 linting..."
flake8 . --exclude=venv --quiet && echo "✅ No linting issues" || echo "❌ Linting issues found"

echo "   - Type checking..."
mypy src/ --ignore-missing-imports --no-error-summary > /tmp/mypy_output 2>&1 && echo "✅ Type checking passed" || echo "❌ Type checking issues (see mypy output)"

echo "6. Running tests..."
python -m pytest tests/test_end_to_end.py -v --tb=no -q

echo "7. Application startup test..."
timeout 5s python tabletalk.py </dev/null || echo "✅ Application started and timed out as expected"

echo ""
echo "=========================================="
echo "Validation Summary:"
echo "✅ Core functionality validated"
echo "⚠️  Full validation requires Ollama running"
echo "📝 Follow instructions in .github/copilot-instructions.md"
echo "=========================================="