# 📊 TableTalk

**TableTalk** is a local-first data schema explorer that lets you chat with your CSV and Parquet files using natural language.

## 🚀 Quick Start

### Automated Setup (Recommended)
```bash
# Cross-platform setup (Windows, macOS, Linux)
python3 scripts/setup.py

# Platform-specific wrappers also available:
# ./scripts/setup.sh       # Unix/macOS/Linux  
# scripts\setup.bat         # Windows
```

### Manual Setup
```bash
# 1. Install Ollama from https://ollama.ai
# 2. Setup Python environment
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows
pip install -r requirements.txt

# 3. Start Ollama and TableTalk
ollama serve
python tabletalk.py
```

## 📋 Requirements

- **Python 3.11+**: Core runtime
- **Ollama**: Local LLM inference ([install guide](https://ollama.ai))
- **Internet**: Required for initial model downloads (~80MB)

### Supported Platforms
- ✅ **Windows 10+** (Command Prompt, PowerShell, Windows Terminal)
- ✅ **macOS 12+** (Terminal, iTerm2)  
- ✅ **Linux** (Ubuntu 20.04+, other distributions)

## ✨ What You Can Do

- **Ask questions**: "What files do we have?", "Find data quality issues"  
- **Explore schemas**: "Show me the customers schema", "What columns are shared?"
- **Semantic search**: "Find user identifiers", "Show me timestamp columns"
- **Data quality**: "Check for type mismatches", "Find naming inconsistencies"

## 💬 Example Session

```bash
> scan
🔍 Scanning data files... ✅ Found 4 files

> What files do we have?
📁 customers.csv (6 columns), orders.csv (5 columns)

> Find any data quality issues  
⚠️ customer_id: int64 vs object type mismatch
⚠️ Column naming: customer_id vs cust_id variations

> Find user identifiers semantically
� customers.csv → customer_id (similarity: 0.89)
📍 reviews.csv → user_id (similarity: 0.68)
```

## � Documentation

- **[Usage Guide](docs/USAGE.md)** - Complete user guide with examples
- **[Architecture](docs/ARCHITECTURE.md)** - Technical overview  
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues

## 🏗️ Architecture

TableTalk uses a clean 4-layer architecture:
- **CLI Interface** - Natural language chat  
- **SchemaAgent** - AI query processing
- **ToolRegistry** - 8 unified analysis tools
- **MetadataStore** - DuckDB schema storage

Built with Python 3.11+, DuckDB, Ollama, and optional semantic search capabilities.