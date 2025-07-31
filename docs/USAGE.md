# 📚 TableTalk Usage Guide

TableTalk is a natural language interface for exploring data schemas. Chat with your CSV and Parquet files using plain English!

## 🚀 Quick Start

### 1. Set Up Environment
```bash
# Install Python 3.9+
python -m venv tabletalk-env
source tabletalk-env/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Install and start Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull phi3:mini
```

### 2. Start TableTalk
```bash
cd table-talk

# Option 1: Run as module (recommended)
python -m src.main

# Option 2: If using virtual environment
./venv/bin/python -m src.main
```

## 💬 How to Use

### Basic Commands
- `scan` - Analyze all data files in the data/ folder
- `status` - Show system status and scanned files
- `help` - List available commands
- `quit` - Exit the application

### Natural Language Queries
Just type what you want to know! TableTalk understands:

**File Information:**
- "What files do we have?"
- "Show me the customers file schema"
- "List all columns in orders.csv"

**Data Quality:**
- "Find any data quality issues"
- "Are there type mismatches?"
- "Check for column naming problems"

**Schema Analysis:**
- "What data types are in the sales file?"
- "Find files with similar schemas"
- "Show me patterns across all files"

## 📊 Example Session

```
📊 TableTalk - Your Data Schema Explorer
Type 'help' for commands or just ask questions in natural language!

> scan
🔍 Scanning data files...
✅ Found and analyzed 4 files:
- customers.csv (6 columns)
- orders.csv (5 columns) 
- reviews.csv (4 columns)
- products.csv (3 columns)

> What files do we have?
📁 **Available Files:**
• customers.csv - 6 columns, 1.2KB
• orders.csv - 5 columns, 2.1KB
• reviews.csv - 4 columns, 0.8KB
• products.csv - 3 columns, 0.5KB

> Show me the customers schema
📋 **customers.csv Schema:**
• customer_id (int64) - 1000 unique values
• first_name (object) - 956 unique values
• last_name (object) - 874 unique values
• email (object) - 1000 unique values
• signup_date (object) - 365 unique values
• total_spent (float64) - 892 unique values

> Find any data quality issues
🔍 **Data Quality Analysis:**

**Type Mismatches Found:**
• customer_id: int64 in customers.csv vs object in orders.csv
• signup_date: object format varies between files

**Column Name Variations:**
• customer_id vs cust_id vs CustomerID
• total_spent vs total_amount

**Recommendations:**
• Standardize customer_id as consistent integer type
• Establish naming convention for customer identifiers
• Consider date format standardization
```

## 🎯 What TableTalk Can Do

### 📁 File Operations
- **Scan files**: Automatically discover CSV/Parquet files
- **Show schemas**: Column names, types, and statistics
- **File comparison**: Find similarities and differences

### 🔍 Data Quality
- **Type checking**: Find inconsistent data types
- **Column analysis**: Detect naming variations and patterns
- **Schema validation**: Identify potential data issues

### 📊 Schema Analysis
- **Pattern detection**: Find common structures across files
- **Relationship hints**: Suggest potential foreign keys
- **Data profiling**: Basic statistics and uniqueness info

## 🛠️ Available Tools

TableTalk has 8 built-in analysis tools that it intelligently selects based on your questions:

| Tool | Purpose | Example Query |
|------|---------|---------------|
| `list_files` | Show available data files | "What files do we have?" |
| `get_file_schema` | Show column details for a file | "Show me customers schema" |
| `get_all_schemas` | Show all file schemas | "Show me all schemas" |
| `detect_type_mismatches` | Find inconsistent data types | "Any type problems?" |
| `detect_semantic_type_issues` | Find column naming issues | "Check column names" |
| `find_files_with_column` | Find files containing a column | "Which files have customer_id?" |
| `get_column_patterns` | Show column name patterns | "What naming patterns exist?" |
| `detect_column_name_variations` | Find naming variations | "Find similar column names" |

## 💡 Tips for Better Results

### 🎯 Effective Queries
- **Be specific**: "Show me customer file schema" vs "tell me about data"
- **Ask follow-ups**: "Find data quality issues" then "How to fix them?"
- **Use context**: TableTalk remembers recent conversation

### 🔍 Data Quality Focus
- Start with `scan` to analyze all files
- Ask "Find data quality issues" for comprehensive analysis
- Follow up with specific questions about problems found

### 📊 Schema Exploration
- Use "Show me all schemas" for overview
- Ask about specific files: "What's in the orders file?"
- Look for patterns: "Find similar column names"

## 🚨 Troubleshooting

### Common Issues

**"No LLM available" error:**
```bash
# Check if Ollama is running
ollama serve

# Verify phi3 model is installed
ollama list
ollama pull phi3:mini
```

**"No data files found":**
- Put CSV/Parquet files in the `data/` folder
- Run `scan` command to analyze files
- Check file permissions and formats

**Slow responses:**
- Phi3:mini model is optimized for speed
- Large files are automatically sampled
- Check available system memory

**Query not understood:**
- Try simpler, more direct questions
- Use specific file names when possible
- TableTalk falls back gracefully to basic file listing

### Getting Help
- Type `help` for available commands
- Type `status` to check system state
- Check `logs/tabletalk.log` for detailed error info

### Running TableTalk
- **Recommended**: `python -m src.main` (handles imports correctly)
- **Alternative**: `./venv/bin/python -m src.main` (with virtual environment)
- **Note**: Direct execution `python src/main.py` is not supported due to module structure

## 🎉 What Makes TableTalk Special

### 🤖 Smart & Simple
- **Natural language**: No special syntax required
- **Intelligent routing**: Automatically picks the right analysis tools
- **Graceful fallback**: Works even when LLM is unavailable

### 🔒 Privacy First
- **Local processing**: All analysis happens on your machine
- **No cloud APIs**: Complete data privacy
- **Offline capable**: Works without internet connection

### ⚡ Fast & Reliable
- **Quick responses**: 1-3 seconds typical
- **Smart sampling**: Handles large files efficiently
- **Robust parsing**: Works with various CSV formats

---

Ready to explore your data? Start with `scan` and then ask anything you want to know! 🚀
