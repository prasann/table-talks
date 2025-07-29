# TableTalk

Chat with your CSV/Parquet files using natural language. Built with local Phi-3 model via Ollama.

## Quick Start

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Start Ollama (separate terminal)
ollama serve
ollama pull phi3:mini

# Run TableTalk
python src/main.py
```

## Usage

```bash
TableTalk> /scan data/sample          # Scan files
TableTalk> What files do we have?     # List files
TableTalk> Show schema of orders.csv  # File details
TableTalk> Find common columns        # Cross-file analysis
```

## Commands
- `/scan <dir>` - Scan directory for files
- `/help` - Show commands
- `/exit` - Quit

Ask questions in plain English about your data schemas.

## Dependencies
- Python 3.11+
- Ollama + Phi-3
- DuckDB (metadata storage)
- LangChain (LLM integration)
