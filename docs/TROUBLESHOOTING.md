# 🛠️ Troubleshooting

## Quick Fixes

### Ollama Issues
```bash
# Start Ollama service
ollama serve

# Install required model
./scripts/setup_phi4_function_calling.sh

# Verify model is available
ollama list | grep phi4-mini-fc
```

### Import/Environment Errors
```bash
# Activate virtual environment
source tabletalk-env/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Test basic imports
python -c "from src.tools.tool_registry import ToolRegistry; print('✅ OK')"
```

### No Data Files Found
```bash
# Put CSV/Parquet files in data/ folder
ls data/

# Run scan command
python tabletalk.py
> scan
```

### Semantic Search Not Working
```bash
# Install optional dependencies
pip install sentence-transformers scikit-learn

# First semantic query takes ~5 seconds (model loading)
# Subsequent queries are fast
```

### Performance Issues
- **First run**: Model downloads may take time
- **Large files**: Files >100MB are automatically sampled
- **Memory**: Close other applications if running low on RAM
- **Restart**: `python tabletalk.py` to reload fresh

### Still Having Issues?
- Check `logs/tabletalk.log` for detailed error messages
- Ensure Python 3.11+ is installed
- Verify Ollama is running: `curl http://localhost:11434/api/version`
