#!/bin/bash

# TableTalk Setup Script
echo "🗣️  Setting up TableTalk..."

# Check if Python 3.11+ is available
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+' | head -1)
if [ -z "$python_version" ]; then
    echo "❌ Python 3.11+ is required"
    exit 1
fi

echo "✅ Found Python $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p database
mkdir -p logs

# Check if Ollama is installed
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is installed"
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is running"
        
        # Check if phi3:mini model is available
        if ollama list | grep -q "phi3:mini"; then
            echo "✅ phi3:mini model is available"
        else
            echo "📥 Downloading phi3:mini model..."
            ollama pull phi3:mini
        fi
    else
        echo "⚠️  Ollama is not running. Start it with: ollama serve"
    fi
else
    echo "⚠️  Ollama not found. Install it from: https://ollama.ai"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start TableTalk:"
echo "  1. Make sure Ollama is running: ollama serve"
echo "  2. Activate the virtual environment: source venv/bin/activate"
echo "  3. Run TableTalk: python src/main.py"
echo ""
echo "For help: python src/main.py and type /help"
