# 📊 TableTalk

Chat with your CSV and Parquet files using natural language! TableTalk is a local-first data schema explorer powered by Phi-3 for intelligent query understanding.

## ✨ Features

- **🗣️ Natural Language**: Ask questions in plain English about your data
- **🤖 Smart Analysis**: AI-powered query understanding and tool selection
- **🔒 Privacy-First**: All processing happens locally on your machine
- **⚡ Fast & Simple**: Quick responses with intelligent fallback
- **📁 Multi-Format**: Supports CSV and Parquet files

## 🚀 Quick Start

```bash
# 1. Setup environment
python -m venv tabletalk-env
source tabletalk-env/bin/activate  # macOS/Linux
pip install -r requirements.txt

# 2. Install Ollama and pull model
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull phi3:mini

# 3. Start TableTalk
python src/main.py
```

## 💬 Example Usage

```bash
📊 TableTalk - Your Data Schema Explorer

> scan
🔍 Scanning data files... ✅ Found 4 files

> What files do we have?
📁 Available Files:
• customers.csv (6 columns, 1.2KB)
• orders.csv (5 columns, 2.1KB)

> Find any data quality issues
🔍 Data Quality Analysis:
• customer_id: int64 vs object type mismatch
• Column naming variations: customer_id vs cust_id

> Show me the customers schema
📋 customers.csv Schema:
• customer_id (int64) - 1000 unique values
• first_name (object) - 956 unique values
• email (object) - 1000 unique values
```

## 🎯 What You Can Ask

- **"What files do we have?"** - File discovery
- **"Show me the customer schema"** - Detailed column analysis
- **"Find data quality issues"** - Comprehensive analysis
- **"Are there type mismatches?"** - Specific validation
- **"Which files have customer_id?"** - Cross-file search

## 🛠️ Commands

- `scan` - Analyze all files in data/ folder
- `status` - Show system status
- `help` - Available commands
- `quit` - Exit application

## 🏗️ Architecture

**Pure LLM Design** - Clean 3-component architecture:
- **LLM Agent**: Query orchestration and response formatting
- **Context Manager**: Intelligent query parsing and tool selection
- **Schema Tools**: 8 specialized analysis functions

## 📋 Requirements

- Python 3.9+
- Ollama with phi3:mini model
- ~2GB RAM for model
- CSV/Parquet files in `data/` folder

## 🔧 Technical Details

- **Database**: DuckDB for fast metadata storage
- **LLM**: Phi-3 mini via Ollama for local inference
- **Files**: Supports CSV and Parquet up to 100MB
- **Response Time**: 1-3 seconds typical

---

**Ready to explore your data?** Put your files in the `data/` folder and start asking questions! 🚀
- Python 3.11+
- Ollama + Phi-3 (optional, falls back to basic mode)
- DuckDB (metadata storage)
- LangChain (LLM integration)
