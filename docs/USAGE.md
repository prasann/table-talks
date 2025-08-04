# 📚 TableTalk Usage Guide

TableTalk is a natural language interface for exploring data schemas. Chat with your CSV and Parquet files using plain English!

## 🚀 Quick Start

### 1. Setup & Start
```bash
# Install dependencies
pip install -r requirements.txt

# Install Ollama and models
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
./scripts/setup_phi4_function_calling.sh

# Start TableTalk
python tabletalk.py
```

### 2. Basic Commands
- `scan` - Analyze data files
- `status` - Show system status
- `help` - List commands  
- `quit` - Exit

## 💬 How to Use

### Natural Language Queries
Just type what you want to know!

**File Information:**
- "What files do we have?"
- "Show me the customers schema"
- "List columns in orders.csv"

**Data Quality:**
- "Find data quality issues"
- "Check for type mismatches"
- "Find naming inconsistencies"

**Semantic Search:**
- "Find user identifiers" (finds user_id, customer_id)
- "Show me timestamp columns" (finds date fields)
- "Customer related fields semantically"

**Schema Analysis:**
- "What columns are shared between files?"
- "Compare schemas between orders and customers"

## � Semantic Search

TableTalk includes AI-powered semantic search that understands the **meaning** behind your queries.

### Automatic Activation
Use phrases like "semantically", "semantic search", "find similar", "related columns" to enable semantic search automatically.

### Examples
```bash
# Traditional: exact matches only
search customer → finds only "customer_id"

# Semantic: concept understanding  
find user identifiers semantically → finds "user_id", "customer_id", "review_id"
show me timestamp columns → finds "created_date", "order_date", "signup_date"
```

### Installation
For semantic search capabilities:
```bash
pip install sentence-transformers scikit-learn
```

## �📊 Example Session

```
📊 TableTalk - Your Data Schema Explorer

> scan
🔍 Scanning data files...
✅ Found 4 files: customers.csv, orders.csv, reviews.csv, products.csv

> What files do we have?
📁 **Available Files:**
• customers.csv - 6 columns, 1.2KB
• orders.csv - 5 columns, 2.1KB
• reviews.csv - 4 columns, 0.8KB

> Find data quality issues
🔍 **Data Quality Analysis:**
⚠️ customer_id: int64 in customers.csv vs object in orders.csv
⚠️ Column naming: customer_id vs cust_id variations

> Find user identifiers semantically
📍 reviews.csv → user_id (similarity: 0.679)
📍 customers.csv → customer_id (similarity: 0.593)
```

## 🎯 What TableTalk Can Do

### 📁 File Operations
- **Scan files**: Discover CSV/Parquet files automatically
- **Show schemas**: Column names, types, and statistics
- **File comparison**: Find similarities and differences

### 🔍 Data Quality
- **Type checking**: Find inconsistent data types across files
- **Column analysis**: Detect naming variations and patterns
- **Schema validation**: Identify potential data issues

### 🧠 Semantic Intelligence
- **Concept search**: Find "user identifiers" across all files
- **Pattern detection**: Group similar columns semantically
- **Smart suggestions**: AI-powered analysis recommendations

## 🚨 Troubleshooting

### Common Issues
**"No LLM available":**
```bash
ollama serve
./scripts/setup_phi4_function_calling.sh
```

**"No data files found":**
- Put CSV/Parquet files in the `data/` folder
- Run `scan` command

**Slow responses:**
- First semantic query loads AI models (~5 seconds)
- Subsequent queries are fast (<1 second)

### Getting Help
- Type `help` for commands
- Type `status` to check system
- Check `logs/tabletalk.log` for errors
