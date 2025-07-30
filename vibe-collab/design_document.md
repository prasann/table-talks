# 🏗️ TableTalk Design Document

## 📋 Overview

TableTalk is a conversational EDA assistant for exploring data schemas using local Small Language Models. This document outlines the current technical architecture and implementation details.

## 🎯 Design Philosophy

### Core Principles
1. **Simplicity First**: Clean, maintainable code over complex abstractions
2. **Local-First**: All processing happens locally for privacy and cost control
3. **Pure LLM**: Single processing path using natural language understanding
4. **Developer-Friendly**: Clear components with single responsibilities

### Technology Stack
- **Python 3.11+**: Primary language with type hints
- **DuckDB**: Embedded analytics database for metadata storage
- **LangChain + Ollama**: Local LLM integration
- **Phi-3**: Microsoft's efficient reasoning model
- **Pandas**: Data processing and CSV/Parquet parsing

---

## 🏛️ Architecture Overview

TableTalk has a clean 4-layer architecture with strategy pattern for query processing:

```
┌─────────────────────────────────────────────────┐
│                CLI Interface                   │
│         • Command handling                     │
│         • Natural language routing             │
│         • User interaction                     │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│                LLM Agent                       │
│         • Strategy factory                     │
│         • Query orchestration                  │
│         • Response formatting                  │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│           Query Strategy Layer                 │
│    ┌─────────────────┐  ┌─────────────────┐     │
│    │ Function Calling│  │ Structured      │     │
│    │ Strategy        │  │ Output Strategy │     │
│    │ (phi4-mini-fc)  │  │ (phi3)          │     │
│    └─────────────────┘  └─────────────────┘     │
│    ┌─────────────────┐                          │
│    │ SQL Agent       │  📊 NEW STRATEGY         │
│    │ Strategy        │  Natural Language → SQL  │
│    │ (LangChain)     │  Advanced Analytics      │
│    └─────────────────┘                          │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│             Schema Tools                       │
│    • 8 analysis functions                     │
│    • DuckDB metadata queries                  │
│    • Formatted responses                      │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              Data Layer                        │
│    • Schema Extraction (CSV/Parquet)          │
│    • DuckDB Storage                            │
│    • File System Access                       │
└─────────────────────────────────────────────────┘
```

---

## 🧩 Core Components

### 1. Query Strategy Pattern - Intelligent Processing

Clean separation of query processing approaches:

```python
class QueryProcessingStrategy(ABC):
    @abstractmethod
    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse user query and determine tool to use"""
    
    @abstractmethod  
    def execute_plan(self, plan: Dict, schema_tools) -> Dict[str, Any]:
        """Execute plan using schema tools"""
        
    @abstractmethod
    def synthesize_response(self, query: str, plan: Dict, results: str) -> Dict[str, Any]:
        """Synthesize final response"""
```

#### Function Calling Strategy (phi4-mini-fc)
- **Native Ollama function calling**: Direct API calls with tool definitions
- **200 lines vs 400+**: Dramatically simplified from old context manager
- **Auto-tool selection**: Model chooses appropriate schema tool
- **Robust validation**: Parameter checking and fallback logic

#### Structured Output Strategy (phi3)  
- **LangChain integration**: Structured prompting with JSON parsing
- **Fallback support**: Multiple parsing methods for reliability
- **Pattern extraction**: Regex fallbacks when structured parsing fails

#### SQL Agent Strategy (LangChain) 📊 NEW
- **Natural Language to SQL**: Advanced query conversion using LangChain SQL agents
- **Complex Analytics**: Multi-table analysis, statistical queries, pattern detection
- **Safety First**: Read-only operations with query validation
- **Intelligent Planning**: Automatic query breakdown and execution
- **Fallback Support**: Uses schema_tools when SQL agent unavailable

### 2. Strategy Factory - Auto-Detection

```python
class QueryStrategyFactory:
    def create_strategy(self, model_name: str, strategy_type: str = None, ...) -> QueryProcessingStrategy:
        """Auto-detect model capabilities and create appropriate strategy"""
        if strategy_type == "sql_agent":
            return SQLAgentStrategy(...)
        elif strategy_type == "function_calling":
            return FunctionCallingStrategy(...)
        elif strategy_type == "structured_output":
            return StructuredOutputStrategy(...)
        elif self._supports_function_calling(model_name):
            return FunctionCallingStrategy(...)
        else:
            return StructuredOutputStrategy(...)
```

**Features:**
- Model capability detection (phi4-mini-fc → function calling, phi3 → structured)
- Explicit strategy selection via strategy_type parameter
- Automatic strategy selection when strategy_type is None
- Clean factory pattern with SQL Agent support

### 3. LLM Agent - Strategy Orchestrator

```python
class LLMAgent:
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process query using appropriate strategy"""
        parsing_result = self.query_strategy.parse_query(query)
        execution_result = self.query_strategy.execute_plan(parsing_result["parsed_query"], self.schema_tools)
        synthesis_result = self.query_strategy.synthesize_response(query, parsing_result["parsed_query"], execution_result["result"])
        return synthesis_result
```

**Responsibilities:**
- Strategy initialization via factory
- Query processing orchestration  
- Error handling and response formatting

### 4. ChatInterface - CLI

```python
class ChatInterface:
    def start(self):
        """Main interaction loop with commands and natural language"""
```

**Features:**
- Commands: `/scan`, `/help`, `/status`, `/strategy`, `/exit`
- Natural language query processing
- Strategy switching capability (`/strategy sql_agent`)
- Strategy status indicators (🚀 SQL Agent, 🔧 Function Calling, 📝 Structured Output)

---

## 🔧 Design Decisions

### Strategy Pattern Architecture
- **Clean separation**: Function calling vs structured output approaches
- **Model-specific optimization**: Phi4-mini-fc native function calling, Phi3 structured prompting
- **Simplified codebase**: 200 lines vs 400+ line monolithic context manager
- **Future-proof**: Easy to add new strategies for different model types

### Auto-Detection Strategy Selection
- **Zero configuration**: Automatically chooses best approach per model
- **Consistent interface**: All strategies implement same interface
- **Graceful fallback**: Pattern-based fallback when LLM unavailable

### Function Calling First
- **Native tool calling**: Direct Ollama API integration for supported models
- **Intelligent selection**: Model chooses appropriate tool based on query
- **Parameter validation**: Robust checking of tool parameters
- **Enhanced logging**: Detailed debugging for function calls

### Local-First Processing
- **Privacy**: All data stays local
- **Cost control**: No API calls to external services
- **Fast inference**: Local Phi-3 model
- **Always available**: No internet dependency

### Tool-Based Design
- **8 schema analysis tools**: Each with specific purpose
- **Strategy-based selection**: Function calling or structured output tool selection
- **Extensible**: Easy to add new analysis functions

---

## 📊 Data Flow

### Query Processing with Strategy Pattern
```
Natural Language Query
    ↓
Strategy Factory → Auto-detect Model Capabilities  
    ↓
```
Function Calling Strategy          Structured Output Strategy          SQL Agent Strategy
(phi4-mini-fc)                    (phi3)                               (LangChain)
    ↓                                 ↓                                     ↓
Native Ollama Function Calls      LangChain + JSON Parsing           NL → SQL Conversion
    ↓                                 ↓                                     ↓
Tool Selection & Validation       Pattern Extraction Fallback        Query Planning & Execution
    ↓                                 ↓                                     ↓
    └─────────────┬─────────────────┬─────────────────────────────────────┘
                  ↓                 ↓                                     ↓
Execute Schema Tool           Execute Schema Tool                  Execute SQL Query
    ↓                            ↓                                     ↓
Format Response             Format Response                    Format Response
```

### Strategy Selection Examples
```
Model: "phi4-mini-fc" → Function Calling Strategy
Model: "phi3"         → Structured Output Strategy  
Model: "custom"       → Structured Output Strategy (default)
Strategy: "sql_agent" → SQL Agent Strategy (explicit)
```

### Query Processing Examples

#### Function Calling
```
"compare schemas across files" → detect_type_mismatches()
"Which files have user_id?"    → find_columns(column_name="user_id")
"Give me a database summary"   → database_summary()
```

#### SQL Agent 📊 NEW
```
"Which files have more than 10 columns?" 
    → SELECT file_name, COUNT(*) as cols FROM schema_info GROUP BY file_name HAVING COUNT(*) > 10

"Find columns with type mismatches"
    → SELECT column_name, data_type, string_agg(file_name) FROM schema_info 
      GROUP BY column_name, data_type HAVING column_name IN (...)

"Show files with highest null percentages"
    → SELECT file_name, AVG(null_count::float/total_rows) as null_pct 
      FROM schema_info GROUP BY file_name ORDER BY null_pct DESC
```
```

### Strategy Selection Examples
```
Model: "phi4-mini-fc" → Function Calling Strategy
Model: "phi3"         → Structured Output Strategy  
Model: "custom"       → Structured Output Strategy (default)
```

### Function Calling Examples
```
"compare schemas across files" → detect_type_mismatches()
"Which files have user_id?"    → find_columns(column_name="user_id")
"Give me a database summary"   → database_summary()
"Find data quality issues"     → database_summary()
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE schema_info (
    id INTEGER PRIMARY KEY,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL, 
    column_name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    null_count INTEGER,
    unique_count INTEGER,
    total_rows INTEGER,
    file_size_mb REAL,
    last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX idx_file_name ON schema_info(file_name);
CREATE INDEX idx_column_name ON schema_info(column_name);
```

**Design:**
- One row per column for normalized storage
- Rich metadata for analysis
- Indexes for fast queries

---

## 🛠️ Schema Tools

8 analysis functions available to the LLM:

| Tool | Purpose | Example Query |
|------|---------|---------------|
| `list_files()` | Show all scanned files | "What files do we have?" |
| `get_file_schema(file)` | Detailed schema for a file | "Schema of customers.csv" |
| `find_columns(name)` | Find columns by name | "Which files have user_id?" |
| `detect_type_mismatches()` | Find type inconsistencies | "Any type mismatches?" |
| `find_common_columns()` | Columns in multiple files | "What columns are shared?" |
| `database_summary()` | Overall statistics | "Database overview" |
| `detect_semantic_type_issues()` | Type vs naming problems | "Data quality issues?" |
| `detect_column_name_variations()` | Naming inconsistencies | "Similar column names?" |

**Pattern:**
```python
def tool_function(parameter: str) -> str:
    # 1. Query DuckDB metadata
    # 2. Format for user display
    # 3. Handle errors gracefully
```

---

##  Performance

- **Query Response**: 1-3 seconds typical
- **File Scanning**: ~1 second per MB  
- **Memory Usage**: ~100MB base + file data
- **Database**: Sub-second metadata queries with DuckDB indexes

##  Current Status

### ✅ Implemented  
- **Strategy pattern architecture** with clean separation of concerns
- **Function calling strategy** for phi4-mini-fc with native Ollama integration
- **Structured output strategy** for phi3 with LangChain + fallback parsing
- **Auto-detection factory** for model capability-based strategy selection
- **8 schema analysis tools** with intelligent strategy-based selection
- **Enhanced error handling** with proper dictionary return formats
- **Robust parameter validation** and graceful fallback logic
- **Local Phi-3/Phi-4 integration** via Ollama with dual model support
- **Clean CLI** with commands and natural language
- **DuckDB metadata storage** with CSV/Parquet support

### 🎯 Benefits
- **Maintainability**: Clean strategy pattern, 200 lines vs 400+ monolithic code
- **Flexibility**: Different processing approaches for different model capabilities  
- **Consistency**: All strategies implement uniform interface
- **Performance**: Native function calling dramatically faster for supported models
- **Privacy**: Complete local processing with multiple model options
- **User Experience**: Natural language with intelligent tool selection
- **Future-proof**: Easy to add new strategies for emerging model types

### 🚀 Recent Improvements
- **Eliminated complex context manager** in favor of strategy pattern
- **Fixed function calling integration** with proper Ollama API usage
- **Added parameter validation** to prevent invalid tool calls
- **Enhanced logging** for debugging function calls and strategy selection
- **Improved tool descriptions** for better model understanding

---

*This document reflects the current simplified architecture of TableTalk focused on core design decisions and implementation details.*
