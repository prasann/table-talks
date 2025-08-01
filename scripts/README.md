# 📜 TableTalk Scripts

This directory contains setup scripts for TableTalk.

## 🚀 Setup Script

### `setup_phi4_function_calling.sh`
Essential setup script for Phi-4 models with function calling support.

**Usage:**
```bash
./scripts/setup_phi4_function_calling.sh
```

**What it does:**
- Downloads Phi-4-mini model (phi4-mini:3.8b-fp16)
- Configures function calling template for optimal performance
- Creates `phi4-mini-fc` model ready for TableTalk
- Validates the setup

**Required:** This script is necessary for TableTalk to work with function calling.

## 🔧 Usage

Run the script from the project root directory:

```bash
# From project root
./scripts/setup_phi4_function_calling.sh
```

## 📋 Prerequisites

- macOS or Linux with Ollama installed
- Internet connection for downloading models
- ~2GB free space for the Phi-4-mini model

## ⚙️ Configuration

After running the setup script, update your `config/config.yaml`:

```yaml
model: 'phi4-mini-fc'
base_url: 'http://localhost:11434'
```

## 🧪 Testing

To test the setup:

```bash
# Activate virtual environment
source venv/bin/activate

# Run TableTalk
python src/main.py

# Test with sample data
/scan data/sample
what files do we have?
```

---

**Need help?** Check the [troubleshooting guide](../docs/TROUBLESHOOTING.md) or main [README](../README.md).