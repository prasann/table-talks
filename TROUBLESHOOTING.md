# 🔧 TableTalk Troubleshooting Guide

## Common Issues & Solutions

### 1. "Cannot connect to Ollama" Error
```bash
# Start Ollama service
ollama serve

# In another terminal, test connection
curl http://localhost:11434/api/tags

# Pull the model if needed
ollama pull phi3:mini
```

### 2. "Import Error" or Module Not Found
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Verify activation (should show (venv) in prompt)
which python

# Reinstall dependencies if needed
pip install -r requirements.txt
```

### 3. "No files found" when scanning
```bash
# Check file formats (only CSV and Parquet supported)
ls -la your/data/directory/

# Use absolute path if relative path fails
TableTalk> /scan /absolute/path/to/data

# Check file permissions
ls -la your/data/directory/*.csv
```

### 4. Database Errors
```bash
# Delete and recreate database
rm -rf database/
mkdir -p database

# Make sure virtual environment is activated
source venv/bin/activate

# Run TableTalk (will recreate clean database)
python src/main.py
```

### 5. LLM Agent Not Available
- Ensure Ollama is running: `ollama serve`
- Check model is installed: `ollama list`
- Verify model name matches config: `phi3:mini`
- You can still use `/scan` commands without the LLM

### 6. Performance Issues
```bash
# Check file sizes (default limit: 100MB)
du -h your/data/directory/*.csv

# Reduce sample size in config.yaml if needed
scanner:
  sample_size: 500  # Reduce from 1000
```

### 7. Memory Issues
```bash
# Clear conversation memory
TableTalk> /clear

# Restart TableTalk for fresh session
TableTalk> /exit
python src/main.py
```

## Getting Help

- **Commands**: Use `/help` in TableTalk for available commands
- **Logs**: Check `logs/tabletalk.log` for detailed error information
- **Status**: Use `/status` to check system health
- **Configuration**: Modify `config/config.yaml` for custom settings

## Debug Mode

To enable verbose logging for debugging:

```bash
# Edit config/config.yaml
logging:
  level: "DEBUG"  # Change from "INFO"
  
# Restart TableTalk
python src/main.py

# Check logs
tail -f logs/tabletalk.log
```
