#!/bin/bash

# Test logging configuration for TableTalk

echo "🧪 Testing TableTalk logging configuration..."

# Clean up any existing logs
rm -rf logs/

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Start TableTalk briefly to generate logs
echo "🚀 Starting TableTalk (will exit quickly)..."
echo "/exit" | timeout 10s python src/main.py 2>/dev/null || true

# Check if logs were created
if [ -d "logs" ]; then
    echo "✅ Logs directory created successfully"
    if [ -f logs/tabletalk_debug_*.log ]; then
        echo "✅ Debug log file created"
        echo "📄 Log contents preview:"
        echo "----------------------------------------"
        head -10 logs/tabletalk_debug_*.log
        echo "----------------------------------------"
        echo "📊 Total log entries: $(wc -l logs/tabletalk_debug_*.log | cut -d' ' -f1)"
    else
        echo "❌ Debug log file not found"
    fi
else
    echo "❌ Logs directory not created"
fi

echo "🏁 Logging test complete!"
