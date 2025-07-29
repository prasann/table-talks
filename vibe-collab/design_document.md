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

TableTalk has a simple 3-layer architecture:

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
│         • Ollama connection                    │
│         • Query orchestration                  │
│         • Response formatting                  │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│            Context Manager                     │
│         • Pure LLM query parsing               │
│         • Tool selection                       │
│         • Plan execution                       │
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

### 1. ContextManager - Pure LLM Intelligence

Handles all query processing using LLM:

```python
class ContextManager:
    def parse_query(self, query: str) -> Dict[str, Any]:
        """Pure LLM parsing for all queries"""
        return self._llm_parse(query)
    
    def execute_plan(self, plan: Dict, schema_tools) -> str:
        """Execute single tool and return results"""
        
    def synthesize_response(self, results: str, query: str) -> str:
        """Format results for display"""
```

**Features:**
- Pure LLM approach (no regex patterns)
- Intelligent tool selection from 8 available tools
- Graceful fallback to file listing if LLM unavailable

### 2. LLMAgent - Simple Orchestrator

```python
class LLMAgent:
    def query(self, user_query: str) -> str:
        """Single entry point for all queries"""
        plan = self.context_manager.parse_query(user_query)
        results = self.context_manager.execute_plan(plan, self.schema_tools)
        return self.context_manager.synthesize_response(results, user_query)
```

**Responsibilities:**
- Ollama connection management
- Query routing to ContextManager
- Response formatting

### 3. ChatInterface - CLI

```python
class ChatInterface:
    def start(self):
        """Main interaction loop with commands and natural language"""
```

**Features:**
- Commands: `/scan`, `/help`, `/status`, `/exit`
- Natural language query processing
- Status indicators

---

## 🔧 Design Decisions

### Pure LLM Architecture
- **Single processing path**: All queries handled by LLM
- **No regex patterns**: Consistent intelligent processing
- **Simple codebase**: Easier to understand and maintain
- **Natural language**: Works for any query complexity

### Local-First Processing
- **Privacy**: All data stays local
- **Cost control**: No API calls to external services
- **Fast inference**: Local Phi-3 model
- **Always available**: No internet dependency

### Tool-Based Design
- **8 schema analysis tools**: Each with specific purpose
- **LLM tool selection**: Intelligent choice based on query
- **Extensible**: Easy to add new analysis functions

---

## 📊 Data Flow

### Query Processing
```
Natural Language Query
    ↓
LLM Parsing → Tool Selection
    ↓
Execute Schema Tool
    ↓
Format Response
```

### Examples
```
"What files do we have?" → list_files()
"Find type mismatches" → detect_type_mismatches()
"Schema of orders.csv" → get_file_schema("orders.csv")
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
- Pure LLM architecture with single processing path
- 8 schema analysis tools with intelligent selection
- Local Phi-3 integration via Ollama
- Clean CLI with commands and natural language
- DuckDB metadata storage with CSV/Parquet support
- Graceful fallback when LLM unavailable

### 🎯 Benefits
- **Maintainability**: Simple codebase, no regex patterns
- **Consistency**: All queries handled intelligently
- **Privacy**: Complete local processing
- **Performance**: Fast local inference
- **User Experience**: Natural language for everything

---

*This document reflects the current simplified architecture of TableTalk focused on core design decisions and implementation details.*
