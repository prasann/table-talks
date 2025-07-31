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

## 🔧 Usage

All scripts should be run from the project root directory:

```bash
# From project root
./scripts/setup.sh
./scripts/setup_phi4_function_calling.sh
```

## 📋 Prerequisites

- macOS or Linux
- Python 3.9+
- Internet connection for downloading models
- ~2GB free space for models

---

**Need help?** Check the [troubleshooting guide](../docs/TROUBLESHOOTING.md) or main [README](../README.md).
