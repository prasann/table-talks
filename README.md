# 📊 TableTalk

**TableTalk** is a local-first data schema explorer that lets you chat with your CSV and Parquet files using natural language.

## 🚀 Quick Start

```bash
# 1. Setup environment
python -m venv tabletalk-env
source tabletalk-env/bin/activate  # macOS/Linux
pip install -r requirements.txt

# 2. Install Ollama and setup models
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
./scripts/setup_phi4_function_calling.sh

# 3. Start TableTalk
python tabletalk.py
```

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