# 📖 TableTalk Usage Guidelines

## Commands Reference

### CLI Commands
- `/scan <directory>` - Scan files for schema information
- `/help` - Show available commands  
- `/status` - Display system status
- `/clear` - Clear conversation memory
- `/exit` or `/quit` - Exit TableTalk

### Natural Language Query Examples

#### File Information
```
What files do we have?
List all scanned files
Show me a summary of the database
How many files are scanned?
```

#### Schema Exploration
```
Show me the schema of orders.csv
Describe the structure of customers.csv
What columns are in reviews.csv?
Tell me about the data types in users.parquet
```

**Example Output:**
```
📁 **customers.csv**
📊 Rows: 6 | Columns: 6

| Column | Type | Unique | Nulls |
|--------|------|--------|-------|
| customer_id | integer | 6 | 0 |
| email | string | 6 | 0 |
| first_name | string | 6 | 0 |
| is_active | boolean | 2 | 0 |
| last_name | string | 6 | 0 |
| signup_date | string | 6 | 0 |
```

#### Cross-File Analysis
```
Which files have a user_id column?
Find columns that appear in multiple files
What columns are common across all files?
Show me shared columns between orders and customers
```

**Example Output:**
```
🔗 Common Columns (3 found)

customer_id ✅
  📂 Files: 2 | Types: integer
  📁 In: orders.csv, customers.csv

email ⚠️  
  📂 Files: 2 | Types: string, varchar
  📁 In: customers.csv, reviews.csv

⚠️ = Type inconsistency detected
```

#### Data Quality Checks
```
Find data type inconsistencies
Detect type mismatches across files
Are there any schema conflicts?
Which columns have different types in different files?
```

## Usage Tips

### Getting Started Workflow
1. **Scan your data**: `/scan /path/to/your/data`
2. **Overview**: "What files do we have?"
3. **Explore**: "Show me the schema of filename.csv"
4. **Analyze**: "Find common columns across files"
5. **Quality check**: "Detect type mismatches"

### Best Practices

#### File Organization
- Keep CSV/Parquet files in organized directories
- Use consistent naming conventions
- Ensure files are under 100MB (default limit)

#### Query Strategies
- Start with general questions, then get specific
- Use exact file names in schema queries
- Ask one question at a time for best results

#### Performance Tips
- Scan smaller directories first to test
- Use `/status` to monitor database size
- Clear memory with `/clear` for long sessions

### Sample Data Testing
Use the provided sample data to test features:

```bash
TableTalk> /scan data/sample
TableTalk> What files do we have?
TableTalk> Show me the schema of orders.csv
TableTalk> Find common columns across files
TableTalk> Which files have customer_id?
```

### Working with Your Own Data

#### Supported Formats
- **CSV files**: `.csv` (various encodings and separators)
- **Parquet files**: `.parquet` (optimized columnar format)

#### File Requirements
- Files should be under 100MB (configurable)
- Valid CSV structure with headers
- Readable file permissions

#### Directory Scanning
```bash
# Scan current directory
TableTalk> /scan .

# Scan specific directory
TableTalk> /scan /path/to/data

# Scan with subdirectories (automatic)
TableTalk> /scan /path/to/nested/data
```

## Advanced Usage

### Configuration Customization
Edit `config/config.yaml` to modify:
- File size limits
- Sample sizes for large files
- LLM model settings
- Database location

### Query Refinement
If queries don't work as expected:
1. Check exact file names with "What files do we have?"
2. Use simpler, more direct questions
3. Try alternative phrasings
4. Use `/help` for command reference

### Session Management
- Use `/clear` to reset conversation context
- Use `/status` to check system health
- Restart TableTalk for complete reset
