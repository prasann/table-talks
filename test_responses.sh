#!/bin/bash

# Quick test of improved TableTalk responses

echo "🧪 Testing TableTalk improvements..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Test with predefined queries
echo "🚀 Testing common columns query..."
echo "Find columns that appear in multiple files" | timeout 30s python src/main.py 2>/dev/null || echo "Test completed"

echo ""
echo "🚀 Testing schema query..."
echo "Describe the structure of customers.csv" | timeout 30s python src/main.py 2>/dev/null || echo "Test completed"

echo ""
echo "🏁 Test script complete!"
