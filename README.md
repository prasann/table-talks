# 🗣️ TableTalk

A conversational EDA assistant that enables natural language exploration of data schemas using a local Small Language Model.

## 🎯 What is TableTalk?

TableTalk helps you understand your datasets through natural conversation. Instead of manually inspecting CSV and Parquet files, just ask questions like:
- "Show me the schema of orders.csv"
- "Which files have a user_id column?"
- "Find data type inconsistencies across files"

## ✨ Features

- **Schema Extraction**: Automatically scan CSV and Parquet files
- **Natural Language Queries**: Ask questions about your data in plain English
- **Type Mismatch Detection**: Find inconsistencies across files
- **Local Processing**: Everything runs locally with Ollama + Phi-3
- **Fast Metadata Storage**: Powered by DuckDB

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Clone and setup (if from repository)
git clone <repo-url>
cd table-talk
./setup.sh

# Start TableTalk
source venv/bin/activate
python src/main.py
```

### Option 2: Manual Setup
```bash
# Prerequisites check
python3 --version  # Should be 3.11+
ollama --version    # Install from https://ollama.ai if needed

# Setup environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start Ollama and pull model
ollama serve &
ollama pull phi3:mini

# Start TableTalk
python src/main.py
```

### First Steps
1. **Activate environment**: `source venv/bin/activate` (important!)
2. **Test with sample data**: `/scan data/sample`
3. **Ask a question**: "What files do we have?"
4. **Explore schemas**: "Show me the schema of orders.csv"
5. **Find patterns**: "Which files have customer_id?"

## 📋 Available Commands

### CLI Commands
- `/scan <directory>` - Scan files in directory for schema information
- `/help` - Show available commands and example queries
- `/status` - Display system status and database statistics
- `/clear` - Clear conversation memory
- `/exit` or `/quit` - Exit TableTalk

### Natural Language Queries
**File Information:**
- "What files do we have?"
- "List all scanned files"
- "Show me a summary of the database"

**Schema Exploration:**
- "Show me the schema of orders.csv"
- "Describe the structure of customers.csv"
- "What columns are in reviews.csv?"

**Cross-File Analysis:**
- "Which files have a user_id column?"
- "Find columns that appear in multiple files"
- "What columns are common across all files?"

**Data Quality:**
- "Find data type inconsistencies"
- "Detect type mismatches across files"
- "Are there any schema conflicts?"

### Example Workflow
```bash
TableTalk> /scan data/sample                    # Scan sample data
TableTalk> What files do we have?               # See available files
TableTalk> Show me the schema of orders.csv     # Explore specific file
TableTalk> Find common columns across files     # Cross-file analysis
TableTalk> Detect type mismatches              # Quality check
TableTalk> /status                             # System overview
TableTalk> /exit                               # Done
```

## 📊 Current Status

✅ **Completed (MVP Core)**
- ✅ Project structure and configuration
- ✅ DuckDB metadata storage
- ✅ CSV/Parquet schema extraction
- ✅ LangChain tool integration
- ✅ Ollama + Phi-3 agent setup
- ✅ Interactive CLI interface
- ✅ Sample data files
- ✅ Basic test framework
- ✅ Setup automation

� **Ready for Testing**
The MVP is complete and ready for testing! You can:
1. Scan directories for CSV/Parquet files
2. Ask natural language questions about schemas
3. Find type mismatches and common columns
4. Get file summaries and database statistics

## �📁 Project Structure

```
table-talk/
├── src/
│   ├── metadata/       # Schema extraction and DuckDB storage
│   ├── tools/          # LangChain tool functions
│   ├── agent/          # LLM agent and context management
│   ├── cli/            # Command-line interface
│   └── main.py         # Entry point
├── tests/              # Unit tests
├── data/sample/        # Sample CSV files for testing
├── config/             # Configuration files
├── setup.sh           # Automated setup script
└── requirements.txt    # Python dependencies
```

## 🧪 Testing with Sample Data

TableTalk comes with sample CSV files to test all features immediately:

### Quick Test (2 minutes)
```bash
# 1. Start TableTalk
python src/main.py

# 2. Scan the sample data
TableTalk> /scan data/sample

# Expected output:
# 🔍 Scanning directory: data/sample
# ✓ customers.csv: 6 columns
# ✓ orders.csv: 6 columns  
# ✓ reviews.csv: 6 columns
# ✅ Scan complete: 3 files, 18 columns processed

# 3. Test natural language queries
TableTalk> What files do we have?
TableTalk> Show me the schema of orders.csv
TableTalk> Which files have customer_id?
TableTalk> Find common columns across files
TableTalk> Detect type mismatches

# 4. Exit
TableTalk> /exit
```

### Sample Data Overview
The `data/sample/` directory contains:
- **orders.csv**: E-commerce orders (10 rows, 6 columns)
  - `order_id`, `customer_id`, `product_name`, `quantity`, `price`, `order_date`
- **customers.csv**: Customer information (6 rows, 6 columns)
  - `customer_id`, `first_name`, `last_name`, `email`, `signup_date`, `is_active`
- **reviews.csv**: Product reviews (6 rows, 6 columns)
  - `review_id`, `user_id`, `product_name`, `rating`, `review_text`, `created_date`

### Expected Test Results
1. **Common columns**: `customer_id` (orders.csv + customers.csv), `product_name` (orders.csv + reviews.csv)
2. **Type consistency**: All data types should be consistent across files
3. **Schema details**: Each file's column types, null counts, and unique values

### Testing Your Own Data
```bash
# Scan your own CSV/Parquet files
TableTalk> /scan /path/to/your/data/directory

# Ask questions about your data
TableTalk> Show me the schema of your_file.csv
TableTalk> Find type mismatches
TableTalk> What columns appear in multiple files?
```

## 🔧 Troubleshooting

### Common Issues & Solutions

**1. "Cannot connect to Ollama" Error**
```bash
# Start Ollama service
ollama serve

# In another terminal, test connection
curl http://localhost:11434/api/tags

# Pull the model if needed
ollama pull phi3:mini
```

**2. "Import Error" or Module Not Found**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**3. "No files found" when scanning**
```bash
# Check file formats (only CSV and Parquet supported)
ls -la your/data/directory/

# Use absolute path
TableTalk> /scan /absolute/path/to/data
```

**4. Database Errors**
```bash
# Delete and recreate database
rm -rf database/
mkdir -p database

# Make sure virtual environment is activated
source venv/bin/activate  # Critical step!

# Run TableTalk (will recreate clean database)
python src/main.py
```

**5. LLM Agent Not Available**
- Ensure Ollama is running: `ollama serve`
- Check model is installed: `ollama list`
- You can still use `/scan` commands without the LLM

**6. "Module not found" errors**
```bash
# Always activate virtual environment first
source venv/bin/activate

# Verify activation (should show (venv) in prompt)
which python

# Then run TableTalk
python src/main.py
```

### Getting Help
- Use `/help` in TableTalk for available commands
- Check logs in `logs/tabletalk.log` for detailed error information
- Use `/status` to check system status

## 🔧 Next Steps

**Phase 2 Enhancements:**
- [ ] Docker containerization
- [ ] Enhanced data profiling
- [ ] Data quality scoring
- [ ] Cross-file relationship detection
- [ ] Web interface (Streamlit)

## 🛠️ Development

See `TableTalk_MVP_Plan.md` for detailed implementation plan and development guidelines.

## 📄 License

MIT License - see LICENSE file for details.
