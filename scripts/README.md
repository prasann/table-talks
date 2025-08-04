# TableTalk Setup Scripts

This folder contains setup scripts for TableTalk.

## Quick Setup

### Cross-Platform (Recommended)
```bash
python3 scripts/setup.py
```

### Platform-Specific Wrappers
```bash
# Unix/macOS/Linux
./scripts/setup.sh

# Windows
scripts\setup.bat
```

## What the setup does

1. ✅ **Python Environment**: Creates virtual environment and installs dependencies
2. ✅ **Ollama Models**: Sets up Phi4 with function calling support
3. ✅ **Semantic Search**: Downloads and warms up the semantic model
4. ✅ **Testing**: Verifies everything works correctly

## Requirements

- **Python 3.11+**: Required for TableTalk
- **Ollama**: Install from [ollama.ai](https://ollama.ai)
- **Internet**: Required for downloading models

## Platform Notes

### Windows
- Use Command Prompt or PowerShell
- Windows Terminal recommended for better colors

### macOS/Linux
- Bash or Zsh shell
- May require `curl` for model testing

## Troubleshooting

### "Ollama not found"
Install Ollama from [ollama.ai](https://ollama.ai)

### "Ollama not running"
Start Ollama with: `ollama serve`

### "Python imports failed"
Check virtual environment activation:
- Windows: `venv\Scripts\activate`
- Unix: `source venv/bin/activate`

### "Semantic model failed"
This is non-critical. TableTalk will work without semantic search features.
