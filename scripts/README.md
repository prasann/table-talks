# 📜 TableTalk Scripts

This directory contains setup and utility scripts for TableTalk.

## 🚀 Setup Scripts

### `setup.sh`
Basic environment setup script for TableTalk.

**Usage:**
```bash
./scripts/setup.sh
```

**What it does:**
- Sets up Python virtual environment
- Installs required dependencies
- Basic Ollama setup instructions

### `setup_phi4_function_calling.sh`
Advanced setup script for optimal function calling performance with Phi-4 models.

**Usage:**
```bash
./scripts/setup_phi4_function_calling.sh
```

**What it does:**
- Downloads and configures Phi-4 models optimized for function calling
- Sets up model-specific configurations
- Enables advanced TableTalk features

**Recommended:** Use this script for the best TableTalk experience.

## 🧪 Testing Scripts

### `run_tests.py`
Simple test runner for end-to-end functionality tests.

**Usage:**
```bash
python scripts/run_tests.py
```

**What it does:**
- Runs all TableTalk end-to-end tests
- Validates core functionality works
- Tests natural language queries with real LLM

## 🔧 Usage

All scripts should be run from the project root directory:

```bash
# From project root
./scripts/setup.sh
./scripts/setup_phi4_function_calling.sh
python scripts/run_tests.py
```

## 📋 Prerequisites

- macOS or Linux
- Python 3.9+
- Internet connection for downloading models
- ~2GB free space for models

---

**Need help?** Check the [troubleshooting guide](../docs/TROUBLESHOOTING.md) or main [README](../README.md).