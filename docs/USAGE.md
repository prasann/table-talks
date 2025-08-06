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

**Schema Differences:**
- "Find schema differences between all files"
- "Analyze differences between schemas with semantic analysis"
- "Show me schema differences" (finds unique columns, type mismatches, semantic equivalents)

## 🧪 Testing Prompts

Here are specific prompts you can use to test different functionality:

### Basic Schema Operations
```bash
"List all files"
"Show me the schema for customers"
"Get file statistics"
"What columns are in orders.csv?"
```

### Schema Relationships & Differences
```bash
# Traditional relationships
"Find common columns across files"
"What columns appear in 2 or more files?"

# Schema differences (our new feature!)
"Find schema differences between all files"
"Analyze differences between schemas with semantic analysis"
"find relationships with analysis type schema_differences"

# Semantic relationships
"Find similar schemas semantically"
"Group columns by semantic concepts"
"Find semantic groups with threshold 0.7"
```

### Data Quality Testing
```bash
"Detect data type inconsistencies"
"Find naming pattern issues"
"Check for semantic naming problems"
"Find abbreviation inconsistencies"
```

### Semantic Search Testing
```bash
"Find user identifiers semantically"
"Show me timestamp columns"
"Find customer related fields semantically"
"Search for price related columns"
"Find ID fields across all files"
```

### Advanced Analysis
```bash
"Run concept evolution analysis"
"Check concept consistency across files"
"Find potential missing columns"
"Analyze schema similarity with threshold 0.8"
```

## 🧠 Semantic Search

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

> find schema differences with semantic analysis
[DIFF] **Schema Difference Analysis**

**customers.csv** vs **orders.csv**
  Overall similarity: 0.091

  Columns only in customers.csv (5):
    • last_name (string)
    • email (string)
    • first_name (string)
    • signup_date (string)
    • is_active (boolean)

  Columns only in orders.csv (5):
    • quantity (integer)
    • price (float)
    • product_name (string)
    • order_date (string)
    • order_id (integer)

  Type mismatches (1):
    • customer_id: integer vs string

  Semantic equivalents (1):
    • customer_id ↔ user_id (similarity: 0.85)

---

**legacy_users.csv** vs **orders.csv**
  Overall similarity: 0.333

  Type mismatches (1):
    • price: string vs float

  Potentially missing columns:
    • orders.csv might need: signup_date (similar to none found)
    • legacy_users.csv might need: order_date (similar to none found)
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

### 🔄 Schema Differences Analysis
- **Comprehensive comparison**: Compare schemas across all file pairs
- **Unique columns**: Identify columns that exist only in specific files
- **Type mismatches**: Find common columns with different data types
- **Semantic equivalents**: Detect columns with different names but similar meanings
- **Missing column analysis**: Suggest potentially missing columns based on semantic similarity

**Example Schema Difference Analysis:**
```
> find schema differences with semantic analysis

customers.csv vs orders.csv (similarity: 0.091)
  Columns only in customers.csv (5):
    • last_name (string)
    • email (string)
    • first_name (string)
    • signup_date (string)
    • is_active (boolean)

  Columns only in orders.csv (5):
    • quantity (integer)
    • price (float)
    • product_name (string)
    • order_date (string)
    • order_id (integer)

  Semantic equivalents (1):
    • customer_id ↔ user_id (similarity: 0.85)

  Type mismatches (1):
    • customer_id: integer vs string
```

## � Testing Tips & Best Practices

### For Schema Differences Analysis
- **Use semantic analysis** for better results: Add "semantic" or "semantically" to your query
- **Adjust thresholds**: Try different values like `"threshold 0.7"` for more/fewer matches
- **Test with diverse data**: Schema differences work best with files that have some overlap
- **Check type mismatches**: Look for columns with same names but different data types

### Effective Query Patterns
**✅ Good queries:**
- `"find schema differences with semantic analysis"`
- `"analyze differences between schemas semantically"`
- `"find relationships with analysis type schema_differences"`

**❌ Avoid:**
- Overly complex queries with multiple requirements
- Queries without semantic keywords when you want semantic analysis
- Very low thresholds (< 0.5) which may produce too many false positives

### Performance Tips
- **First semantic query** takes longer (~5 seconds) as AI models load
- **Subsequent queries** are much faster (< 1 second)
- **Large datasets**: Consider testing with smaller sample files first
- **Threshold tuning**: Start with 0.7, adjust based on results

### Expected Results
When testing schema differences, expect to see:
- **Similarity scores** between 0.0 and 1.0
- **Unique columns** listed per file with data types
- **Type mismatches** for columns with same names but different types
- **Semantic equivalents** when semantic analysis is enabled
- **Missing column suggestions** based on semantic similarity

## �🚨 Troubleshooting

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

## 🚀 Quick Reference

### Essential Commands
| Category | Command | Example |
|----------|---------|---------|
| **Files** | List files | `"What files do we have?"` |
| **Schemas** | Show schema | `"Show me the customers schema"` |
| **Differences** | Schema diff | `"find schema differences with semantic analysis"` |
| **Quality** | Type issues | `"Check for type mismatches"` |
| **Semantic** | Find concepts | `"Find user identifiers semantically"` |
| **Analysis** | Relationships | `"What columns are shared between files?"` |

### Tool Parameters (Advanced)
- **analysis_type**: `"common_columns"`, `"similar_schemas"`, `"semantic_groups"`, `"concept_evolution"`, `"schema_differences"`
- **semantic**: Add `"semantic"` or `"semantically"` to enable
- **threshold**: Specify like `"threshold 0.7"` (0.5-0.9 range)

### Sample Data for Testing
If you don't have data files, create sample CSV files with:
```bash
# customers.csv
customer_id,first_name,last_name,email,signup_date,is_active
1,John,Doe,john@email.com,2023-01-01,true

# orders.csv  
order_id,customer_id,product_name,price,quantity,order_date
1,1,Widget,29.99,2,2023-01-15
```

This gives you overlapping schemas to test schema differences!
