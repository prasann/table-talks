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

TableTalk has a clean 3-layer architecture with unified agent approach:

```
┌─────────────────────────────────────────────────┐
│                CLI Interface                   │
│         • Command handling                     │
│         • Natural language routing             │
│         • User interaction                     │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│               SchemaAgent                      │
│         • Auto-capability detection            │
│         • Unified query processing             │
│         • Fallback chain handling              │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│            Processing Modes                    │
│  ┌──────────────┐ ┌─────────────┐ ┌──────────┐  │
│  │Function      │ │Structured   │ │Pattern   │  │
│  │Calling       │ │Output       │ │Matching  │  │
│  │(phi4-mini-fc)│ │(phi3/phi4)  │ │(fallback)│  │
│  └──────────────┘ └─────────────┘ └──────────┘  │
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

### 1. SchemaAgent - Unified Query Processing

Single agent with auto-capability detection and fallback chain:

```python
class SchemaAgent:
    def __init__(self, schema_tools, model_name, base_url):
        """Initialize with auto-capability detection"""
        self.supports_function_calling = self._detect_function_calling()
        self.llm = self._init_llm() if not self.supports_function_calling else None
    
    def query(self, user_query: str) -> str:
        """Process query using best available method"""
        if self.supports_function_calling:
            return self._process_with_function_calling(user_query)
        elif self.llm:
            return self._process_with_structured_output(user_query)
        else:
            return self._process_with_patterns(user_query)
```

#### Function Calling Mode (phi4-mini-fc)
- **Native Ollama function calling**: Direct API calls with tool definitions
- **Auto-tool selection**: Model chooses appropriate schema tool
- **Robust validation**: Parameter checking and fallback logic
- **Optimal performance**: Direct model-to-tool communication

#### Structured Output Mode (phi3/phi4)  
- **LangChain integration**: Structured prompting with JSON parsing
- **Fallback support**: Multiple parsing methods for reliability
- **Pattern extraction**: Regex fallbacks when structured parsing fails

#### Pattern Matching Mode (fallback)
- **Simple pattern matching**: Basic keyword detection
- **No dependencies**: Works without LLM
- **Essential functionality**: Core commands still work

### 2. Auto-Capability Detection

```python
def _detect_function_calling(self) -> bool:
    """Auto-detect if model supports native function calling"""
    function_calling_indicators = ["phi4-mini-fc", "phi4-mini:fc", "phi4:fc"]
    
    if self.model_name in function_calling_indicators:
        return True
        
    if "phi4" in self.model_name.lower() and ("fc" in self.model_name.lower()):
        return True
        
    return False
```

**Benefits:**
- **No manual switching**: Auto-detects best approach at startup
- **Graceful degradation**: Falls back through capability chain
- **Simplified architecture**: Single agent handles all model types
- **Reduced complexity**: No factory pattern or strategy selection needed
- **Clean unified interface**: Same query() method regardless of model

### 3. SchemaAgent - Unified Implementation

```python
class SchemaAgent:
    def query(self, user_query: str) -> str:
        """Process query using best available method"""
        if self.supports_function_calling:
            return self._process_with_function_calling(user_query)
        elif self.llm:
            return self._process_with_structured_output(user_query)
        else:
            return self._process_with_patterns(user_query)
```

**Responsibilities:**
- Auto-capability detection at initialization
- Query processing with automatic fallbacks
- Error handling and response formatting  
- Direct integration with schema tools

### 4. ChatInterface - CLI

```python
class ChatInterface:
    def start(self):
        """Main interaction loop with commands and natural language"""
```

**Features:**
- Commands: `/scan`, `/help`, `/status`, `/exit`
- Natural language query processing
- Automatic mode detection (Function Calling/Structured Output/Pattern Matching)
- Status indicators show detected capability

---

## 🔧 Design Decisions

### Unified Agent Architecture
- **Simplified approach**: Single SchemaAgent replaces complex strategy pattern
- **Auto-capability detection**: Automatically determines best approach for each model
- **Graceful degradation**: Built-in fallback chain (function calling → structured output → pattern matching)
- **Reduced complexity**: ~300 lines total vs previous 1200+ line strategy system
- **Model-specific optimization**: Phi4-mini-fc native function calling, Phi3 structured prompting, pattern fallback

### Auto-Detection Implementation
- **Zero configuration**: Automatically chooses best approach per model
- **Unified interface**: Single query() method handles all model types
- **Graceful fallback**: Function calling → structured output → pattern matching

### Function Calling First
- **Native tool calling**: Direct Ollama API integration for supported models
- **Intelligent selection**: Model chooses appropriate tool based on query
- **Parameter validation**: Robust checking of tool parameters
- **Enhanced logging**: Detailed debugging for function calls

### Local-First Processing
- **Privacy**: All data stays local
- **Cost control**: No API calls to external services
- **Fast inference**: Local Phi-3/4 models
- **Always available**: No internet dependency

### Tool-Based Design
- **8 schema analysis tools**: Each with specific purpose
- **Auto-capability selection**: Function calling or structured output based on model
- **Extensible**: Easy to add new analysis functions

---

## 📊 Data Flow

### Query Processing with Unified Agent
```
Natural Language Query
    ↓
SchemaAgent → Auto-detect Model Capabilities at Initialization
    ↓
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    ▼                                     ▼                   ▼
Function Calling Mode             Structured Output Mode  Pattern Mode
(phi4-mini-fc)                    (phi3/phi4)            (fallback)
    ↓                                 ↓                       ↓
Native Ollama Function Calls      LangChain + JSON Parsing   Keyword Matching
    ↓                                 ↓                       ↓
Tool Selection & Validation       Pattern Extraction         Basic Commands
    ↓                                 ↓                       ↓
    └─────────────┬─────────────────────┘───────────────────────┘
                  ↓                                           
Execute Schema Tool & Format Response                                          
```
```
Natural Language Query
    ↓
Strategy Factory → Auto-detect Model Capabilities  
    ↓
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    ▼                                     ▼                   │
Function Calling Strategy          Structured Output Strategy │
(phi4-mini-fc)                    (phi3)                     │
    ↓                                 ↓                       │
Native Ollama Function Calls      LangChain + JSON Parsing   │
    ↓                                 ↓                       │
Tool Selection & Validation       Pattern Extraction Fallback│
    ↓                                 ↓                       │
    └─────────────┬─────────────────────┘                     │
                  ↓                                           │
Execute Schema Tool & Format Response                                          
```

### Auto-Detection Examples
```
Model: "phi4-mini-fc" → Function Calling Mode
Model: "phi3"         → Structured Output Mode  
Model: "any"          → Pattern Matching Mode (fallback)
```

### Query Processing Examples

#### Function Calling Mode
```
"compare schemas across files" → detect_type_mismatches()
"Which files have user_id?"    → find_columns(column_name="user_id")
"Give me a database summary"   → database_summary()
"Find data quality issues"     → detect_semantic_type_issues()
```

#### Structured Output Mode  
```
"What files do we have?"       → list_files()
"Schema of customers.csv"      → get_file_schema(file_name="customers.csv")
"Any type mismatches?"         → detect_type_mismatches()
```

#### Pattern Matching Mode
```
"help"                        → Show help message
"scan"                        → Trigger metadata scan
"status"                      → Show system status
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
- **Unified SchemaAgent architecture** with auto-capability detection
- **Function calling mode** for phi4-mini-fc with native Ollama integration
- **Structured output mode** for phi3/phi4 with LangChain + fallback parsing
- **Pattern matching fallback** for basic functionality without LLM
- **Auto-detection system** for model capability-based mode selection
- **8 schema analysis tools** with intelligent mode-based selection
- **Enhanced error handling** with proper dictionary return formats
- **Robust parameter validation** and graceful fallback logic
- **Local Phi-3/Phi-4 integration** via Ollama with dual model support
- **Clean CLI** with commands and natural language
- **DuckDB metadata storage** with CSV/Parquet support

### 🎯 Benefits
- **Simplicity**: Single SchemaAgent, ~300 lines vs 1200+ strategy system
- **Flexibility**: Three processing modes with automatic capability detection
- **Consistency**: Unified query() interface regardless of model type
- **Performance**: Native function calling dramatically faster for supported models
- **Privacy**: Complete local processing with multiple model options
- **User Experience**: Natural language with intelligent tool selection
- **Maintainability**: Consolidated codebase with clear architecture

### 🚀 Recent Improvements
- **Consolidated strategy pattern** into unified SchemaAgent approach
- **Eliminated complex factory system** in favor of direct auto-detection
- **Reduced codebase size** by ~75% while maintaining all functionality
- **Simplified imports and dependencies** with cleaner module structure
- **Enhanced logging** for debugging function calls and mode selection
- **Improved tool descriptions** for better model understanding

---

*This document reflects the current simplified architecture of TableTalk focused on core design decisions and implementation details.*
