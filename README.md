# � TableTalk

**TableTalk** is a local-first data schema explorer that lets you chat with your CSV and Parquet files using natural language, powered by Phi-3 for intelligent query understanding.

## 🚀 Quick Start

```bash
# 1. Setup environment
python -m venv tabletalk-env
source tabletalk-env/bin/activate  # macOS/Linux
pip install -r requirements.txt

# 2. Install Ollama and setup function calling
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# For basic functionality (any model works)
ollama pull phi3:mini

# For advanced function calling (recommended)
./scripts/setup_phi4_function_calling.sh

# 3. Start TableTalk
python src/main.py
```

## ✨ Features

- **🗣️ Natural Language**: Ask questions in plain English about your data
- **🤖 Smart Analysis**: AI-powered query understanding and tool selection
- **🔒 Privacy-First**: All processing happens locally on your machine
- **⚡ Fast & Simple**: Quick responses with intelligent fallback
- **📁 Multi-Format**: Supports CSV and Parquet files

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

## 📖 User Documentation

- **[Usage Guide](docs/USAGE.md)** - Detailed usage instructions and examples
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🏗️ Technical Documentation

- **[Architecture Overview](docs/vibe-collab/ARCHITECTURE.md)** - Comprehensive technical architecture documentation
- **[Development Guide](docs/DEVELOPMENT.md)** - Setup and development guidelines
- **[Development Plan](docs/vibe-collab/concept_and_plan.md)** - Project concept, vision, and implementation roadmap
- **[Technical Documentation Guide](docs/vibe-collab/README.md)** - Overview of technical docs structure

## 📝 Development Notes

- **[Migration History](docs/vibe-collab/migration_plan.md)** - Historical architecture migration details
- **[Todo List](docs/todo.txt)** - Development tasks and ideas

## 🗂️ Project Structure

```
table-talk/
├── README.md                    # This file - main project documentation
├── src/                         # Source code
├── docs/                        # Documentation
│   ├── USAGE.md                 # User guide and examples
│   ├── DEVELOPMENT.md           # Development setup and guidelines
│   ├── TROUBLESHOOTING.md       # Common issues and solutions
│   ├── todo.txt                 # Development notes
│   └── vibe-collab/             # Technical architecture docs (for GitHub Copilot)
│       ├── README.md            # Technical docs overview
│       ├── ARCHITECTURE.md      # Comprehensive technical architecture
│       ├── concept_and_plan.md  # Project concept and roadmap
│       └── migration_plan.md    # Historical migration documentation
├── scripts/                     # Setup and utility scripts
├── tests/                       # Test files
├── data/                        # Data files directory
└── config/                      # Configuration files
├── scripts/                     # Setup and utility scripts
├── tests/                       # Test files
├── data/                        # Data files directory
└── config/                      # Configuration files
```

## 🔗 Quick Links

- **Getting Started**: Quick start instructions below
- **Scripts**: Setup and utility scripts in [scripts/](scripts/)
- **Tests**: Test files in [tests/](tests/)
- **Source Code**: Implementation in [src/](src/)

---