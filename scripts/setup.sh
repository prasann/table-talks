#!/bin/bash

# TableTalk Setup Script - Legacy Wrapper
# This script is now a simple wrapper around the Python-based setup.

echo "🗣️  TableTalk Setup"
echo "==================="
echo ""
echo "ℹ️  This setup has been migrated to Python for better cross-platform support."
echo ""
echo "� Running Python setup script..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found."
    echo "   Please install Python 3.11+ from: https://python.org"
    exit 1
fi

# Run the Python setup script
python3 "$(dirname "$0")/setup.py" "$@"

echo ""
echo "💡 For future setups, you can run directly:"
echo "   python3 scripts/setup.py"
