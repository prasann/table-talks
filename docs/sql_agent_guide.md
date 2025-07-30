# LangChain SQL Agent Integration Guide

## Overview

The SQL Agent Strategy provides natural language to SQL conversion for advanced data analysis in TableTalk. This strategy uses LangChain's SQL agent capabilities to convert complex natural language queries into SQL statements that execute against your metadata database.

## Features

### 🎯 **Natural Language to SQL**
- Convert complex questions into SQL queries automatically
- No need to know SQL syntax - just ask questions naturally
- Intelligent query planning and execution

### 🔍 **Advanced Analytics**
- Complex multi-table analysis
- Statistical queries and aggregations
- Pattern detection across multiple files
- Data quality analysis

### 🛡️ **Safety & Security**
- Read-only SQL operations (no data modification)
- Query validation and error handling
- Human-in-the-loop capability for sensitive operations

## Installation

1. **Install Dependencies**:
```bash
pip install langchain-community langgraph
```

2. **Verify Installation**:
```bash
python -c "from langchain_community.utilities import SQLDatabase; print('✅ LangChain SQL components available')"
```

## Usage

### **Activate SQL Agent Strategy**

1. **Via Configuration** (config/config.yaml):
```yaml
llm:
  model: "phi3"
  strategy_type: "sql_agent"
```

2. **Via CLI Commands**:
```bash
/strategy sql_agent
```

3. **Via Python API**:
```python
agent = LLMAgent(schema_tools, strategy_type="sql_agent")
```

### **Example Queries**

#### **Basic Schema Analysis**
```
"What files do we have and how many columns does each have?"
"Show me the schema of customers.csv"
"Which files have more than 10 columns?"
```

#### **Data Quality Analysis**
```
"Find columns with data type mismatches across files"
"Which files have the highest percentage of null values?"
"Show me columns that appear in multiple files with different types"
```

#### **Advanced Analytics**
```
"Which files have more than 5 columns and over 1000 rows?"
"Find files where more than 50% of values are null in any column"
"Show me the distribution of file sizes across all data"
```

#### **Relationship Analysis**
```
"What columns do customers.csv and orders.csv have in common?"
"Find all files that contain user identification columns"
"Which files might be related based on common column names?"
```

## Strategy Comparison

| Feature | SQL Agent | Function Calling | Structured Output |
|---------|-----------|------------------|-------------------|
| **Query Complexity** | ✅ Very High | ✅ High | ⚠️ Medium |
| **Natural Language** | ✅ Excellent | ✅ Good | ⚠️ Basic |
| **Performance** | ✅ Excellent | ✅ Very Good | ✅ Good |
| **Flexibility** | ✅ Maximum | ⚠️ Tool-Limited | ⚠️ Pattern-Limited |
| **Setup Complexity** | ⚠️ Medium | ✅ Simple | ✅ Simple |
| **Dependencies** | ⚠️ LangGraph | ✅ Minimal | ✅ LangChain |

## Architecture

### **Components**

1. **SQLAgentStrategy**: Main strategy implementation
2. **LangChain SQL Agent**: Converts NL to SQL
3. **DuckDB Integration**: Executes queries against metadata
4. **Fallback System**: Uses schema_tools when agent unavailable

### **Data Flow**

```
User Query → SQL Agent → SQL Generation → DuckDB Execution → Response Synthesis
     ↓              ↓            ↓              ↓              ↓
"Show files    Agent analyzes   SELECT        DuckDB         Formatted
 with >10      query context    file_name,    executes       natural
 columns"      and generates    COUNT(*)      query          language
               appropriate      FROM...                      response
               SQL
```

### **Safety Features**

- **Read-Only Operations**: Only SELECT queries allowed
- **Query Validation**: SQL syntax and safety checks
- **Error Handling**: Graceful fallback to schema_tools
- **Logging**: All queries logged for audit

## Advanced Configuration

### **Custom System Prompts**

You can customize the SQL agent's behavior by modifying the system prompt in `sql_agent_strategy.py`:

```python
system_message = """Your custom instructions here..."""
```

### **Adding Custom Tools**

Extend the SQL toolkit with custom tools:

```python
from langchain_community.agent_toolkits import SQLDatabaseToolkit

toolkit = SQLDatabaseToolkit(db=self._sql_db, llm=self.llm.llm)
custom_tools = [your_custom_tool]
tools = toolkit.get_tools() + custom_tools
```

### **Performance Tuning**

1. **Database Optimization**:
   - Ensure proper indexes on metadata table
   - Regular VACUUM operations for DuckDB
   
2. **LLM Optimization**:
   - Use faster models for simple queries
   - Adjust temperature for consistency

## Troubleshooting

### **Common Issues**

1. **"Import langgraph could not be resolved"**
   ```bash
   pip install langgraph
   ```

2. **SQL Agent not initializing**
   - Check LLM availability
   - Verify DuckDB connection
   - Check logs for detailed errors

3. **Queries timing out**
   - Use simpler questions
   - Check database performance
   - Verify model response time

### **Fallback Behavior**

When SQL Agent fails, the system automatically falls back to:
1. Traditional schema_tools operations
2. Pattern-based query matching
3. Basic file listing

### **Debug Mode**

Enable detailed logging:
```python
import logging
logging.getLogger("tabletalk.sql_agent").setLevel(logging.DEBUG)
```

## Best Practices

### **Query Formulation**
- Be specific about what you want to analyze
- Use domain terms (files, columns, data types)
- Ask one question at a time for clarity

### **Performance Optimization**
- Start with simple queries to warm up the agent
- Use SQL Agent for complex analysis, other strategies for simple lookups
- Monitor query execution times

### **Error Handling**
- Check logs if queries fail
- Try rephrasing complex questions
- Use fallback commands if needed

## Migration from Other Strategies

### **From Function Calling**
```bash
# Check current strategy
/status

# Switch to SQL Agent
/strategy sql_agent

# Verify switch
/status
```

### **From Structured Output**
The SQL Agent provides much more sophisticated query understanding and can handle questions that would require multiple tool calls in other strategies.

## Future Enhancements

- **Human-in-the-loop**: Review queries before execution
- **Query Caching**: Store frequent query results
- **Custom Functions**: Domain-specific SQL functions
- **Visual Query Builder**: GUI for complex queries
