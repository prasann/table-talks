# TableTalk Development Instructions

**ALWAYS follow these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Project Overview

TableTalk is a local-first data schema explorer that lets you chat with CSV and Parquet files using natural language. It uses Python 3.11+, DuckDB for metadata storage, Ollama for local LLM inference with phi4-mini-fc model, and optional semantic search capabilities.

## Working Effectively

### Initial Setup & Dependencies (REQUIRED)
Always run these steps in order for a fresh environment:

1. **Verify Python version**: 
   ```bash
   python3 --version  # Must be 3.11+
   ```

2. **Automated setup (RECOMMENDED)**:
   ```bash
   python3 scripts/setup.py
   ```
   - NEVER CANCEL: Setup takes 5-10 minutes including model downloads. Set timeout to 15+ minutes.
   - Creates virtual environment (~3 seconds)
   - Installs dependencies (~2-3 minutes)
   - Sets up Ollama models (~3-5 minutes for phi4-mini-fc download)
   - Warms up semantic model (~1-2 minutes, ~80MB download)

3. **Manual setup (if automated fails)**:
   ```bash
   # Install Ollama first from https://ollama.ai
   python3 -m venv venv
   source venv/bin/activate      # macOS/Linux
   # venv\Scripts\activate       # Windows
   pip install --upgrade pip
   pip install -r requirements.txt  # NEVER CANCEL: Takes 2-3 minutes
   pip install --upgrade sentence-transformers scikit-learn  # Optional semantic search
   mkdir -p database logs data
   ```

4. **Start Ollama service**:
   ```bash
   ollama serve  # Must run in separate terminal
   ollama pull phi4-mini-fc  # NEVER CANCEL: Takes 3-5 minutes (~80MB download)
   ```

### Running the Application

1. **Start TableTalk**:
   ```bash
   source venv/bin/activate  # Always activate first
   python tabletalk.py
   ```
   - Application starts in ~1-2 seconds
   - Shows system status with component health check
   - Requires Ollama running for natural language queries

2. **Basic CLI commands**:
   - `/scan` - Scan current directory for CSV/Parquet files
   - `/scan <path>` - Scan specific directory
   - `/help` - Show available commands
   - `/status` - Show system status
   - `/exit` - Exit application

### Development & Testing

1. **Run tests**:
   ```bash
   source venv/bin/activate
   python -m pytest tests/test_end_to_end.py -v  # Takes ~1-2 seconds
   ```
   - Basic tests work without Ollama (file scanning, schema extraction)
   - Natural language query tests require Ollama running

2. **Code quality checks** (ALWAYS run before committing):
   ```bash
   source venv/bin/activate
   black .                    # Format code (~1-2 seconds)
   flake8 . --exclude=venv   # Lint code (~1 second)
   mypy src/ --ignore-missing-imports  # Type check (~1 second)
   ```

3. **Manual validation scenarios** (CRITICAL - test these after changes):
   ```bash
   # Start application - should show system status and Ollama warning if not running
   python tabletalk.py
   # Expected: System status table showing 8 tools available, Ollama connection warning
   
   # Test file scanning (works without Ollama)
   > scan data/sample
   # Expected: Should show "Found 2 files" or similar with CSV detection
   
   # Test schema queries (requires Ollama running)
   > What files do we have?
   > Show me the customers schema  
   > Find data quality issues
   > Find user identifiers semantically
   # Expected with Ollama: Detailed responses with schema information
   # Expected without Ollama: "function calling failed" error message
   ```

## Validation Requirements

### Essential Test Data
The repository includes rich multi-tenant retail dataset in `data/multi-tenant/` with 15 CSV files:
- 3 regions: US (snake_case), EU (camelCase), Asia (abbreviated)
- Tables: customers, orders, payments, products, reviews
- Perfect for testing schema differences and semantic matching

### Manual Testing Scenarios (ALWAYS execute these)
1. **File Discovery**: Verify `scan data/sample` command finds CSV files correctly
2. **Schema Extraction**: Check DuckDB metadata storage works (database/ directory created)
3. **Application Startup**: Verify system status shows 8 tools, appropriate Ollama warnings
4. **Natural Language Queries**: Test with Ollama running
   - "What files do we have?"
   - "Find schema differences with semantic analysis"
   - "Check for type mismatches across files"
5. **Semantic Search**: Test semantic model functionality
   - "Find user identifiers semantically"
   - First query takes ~5 seconds (model loading), subsequent queries are fast

### Critical Timing Warnings
- **NEVER CANCEL builds or installs** - Dependencies take 2-3 minutes
- **NEVER CANCEL model downloads** - phi4-mini-fc takes 3-5 minutes (~80MB)
- **NEVER CANCEL semantic model** - First load takes 1-2 minutes (~80MB)
- Set timeouts of 15+ minutes for setup commands
- Set timeouts of 5+ minutes for model operations

## Application Architecture

### Key Components
- **CLI Interface** (`src/cli/`) - Rich terminal interface with natural language chat
- **SchemaAgent** (`src/agent/`) - AI query processing with function calling
- **ToolRegistry** (`src/tools/`) - 8 analysis tools for schema operations
- **MetadataStore** (`src/metadata/`) - DuckDB-based schema storage
- **Semantic Search** (`src/tools/core/semantic_search.py`) - Optional sentence-transformers integration

### Database & Storage
- **DuckDB**: `database/metadata.duckdb` (auto-created)
- **Logs**: `logs/tabletalk.log` (detailed application logs)
- **Exports**: `exports/` (query result exports)

## Common Issues & Solutions

### "Ollama not found" or connection refused
- Install Ollama from https://ollama.ai
- Start service: `ollama serve`
- Verify: `curl http://localhost:11434/api/version`

### Python import errors
- Activate virtual environment: `source venv/bin/activate`
- Reinstall requirements: `pip install -r requirements.txt`
- Test imports: `python -c "from src.agent.schema_agent import SchemaAgent; print('✅ OK')"`

### Semantic search fails
- Non-critical - TableTalk works without semantic features
- Install: `pip install sentence-transformers scikit-learn`
- First semantic query takes ~5 seconds for model loading

### Code formatting issues
- Auto-fix: `black .`
- Check lint: `flake8 . --exclude=venv`
- The codebase has many formatting issues - always run `black` before committing

## Repository Navigation

### Frequently Used Files
- `tabletalk.py` - Main entry point
- `src/main.py` - Application initialization and LLM connection
- `src/cli/chat_interface.py` - Interactive chat interface
- `src/agent/schema_agent.py` - Core AI agent with function calling
- `src/tools/tool_registry.py` - Tool management and function calling schemas
- `config/config.yaml` - Application configuration
- `tests/test_end_to_end.py` - Integration tests

### Important Directories
```
├── src/                     # Main application code
├── config/                  # Configuration files  
├── data/multi-tenant/       # Rich sample dataset (15 CSV files)
├── scripts/                 # Setup and utility scripts
├── tests/                   # Test suite
├── docs/                    # Documentation (USAGE.md, ARCHITECTURE.md)
├── database/               # Generated DuckDB files
└── logs/                   # Application logs
```

## Build & CI Information
- **No CI/CD pipeline currently** - validate locally before commits
- **Tests pass with Ollama running** - some tests skip without it
- **Expected test time**: ~1-2 seconds for basic tests
- **Expected build time**: Setup takes 5-10 minutes total

## Key Success Metrics
After making changes, verify:
1. ✅ Application starts without errors (~1-2 seconds startup time)
2. ✅ System status shows 8 tools available and component health
3. ✅ File scanning discovers CSV/Parquet files (scan data/sample finds 2 files)
4. ✅ Schema extraction creates DuckDB metadata (database/metadata.duckdb file)
5. ✅ With Ollama: Natural language queries work
6. ✅ Without Ollama: Appropriate warnings shown, basic functionality works
7. ✅ Code passes black formatting and flake8 linting
8. ✅ Tests run successfully: `pytest tests/test_end_to_end.py -v`

**Always test the complete user workflow from fresh environment setup through data exploration.**