# 🏗️ TableTalk Design Document

## 📋 Overview

TableTalk is a conversational EDA assistant for exploring data schemas using local Small Language Models. This document outlines the current technical architecture and implementation details.

## 🎯 Design Philosophy

### Core Principles
1. **Simplicity First**: Clean, maintainable code over complex abstractions
2. **Local-First**: All processing happens locally for privacy and cost control
3. **Function Calling Only**: Single processing path using native Ollama function calling
4. **Strategy Pattern**: Pluggable components for extensibility

### Technology Stack
- **Python 3.11+**: Primary language with type hints
- **DuckDB**: Embedded analytics database for metadata storage
- **Ollama**: Local LLM serving with native function calling
- **Phi-4-mini-fc**: Microsoft's function calling enabled model
- **Optional: Pandas/Tabulate**: Enhanced data processing and formatting

---

## 🏛️ Architecture Overview

TableTalk has a clean 4-layer architecture with unified tool registry:

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
│         • Function calling only                │
│         • ToolRegistry integration             │
│         • Simplified query processing          │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              ToolRegistry                      │
│    • Single source of truth                   │
│    • Auto-schema generation                   │
│    • 8 unified tools                          │
│    • Strategy pattern integration             │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│           Tool Components                      │
│  ┌─────────────┐ ┌────────────┐ ┌─────────────┐ │
│  │ Searchers   │ │ Analyzers  │ │ Formatters  │ │
│  │ (Column,    │ │ (Relations,│ │ (Text,      │ │
│  │  File,      │ │  Consist.) │ │  Table)     │ │
│  │  Type)      │ │            │ │             │ │
│  └─────────────┘ └────────────┘ └─────────────┘ │
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

### 1. SchemaAgent - Simplified Query Processing

Single agent with ToolRegistry integration and function calling only:

```python
class SchemaAgent:
    def __init__(self, metadata_store, model_name="phi4-mini-fc", base_url="http://localhost:11434"):
        """Initialize with ToolRegistry integration"""
        self.tool_registry = ToolRegistry(metadata_store)
        self.model_name = model_name
        self.base_url = base_url
        self.supports_function_calling = self._detect_function_calling()
    
    def query(self, user_query: str) -> str:
        """Process query using function calling only"""
        return self._process_with_function_calling(user_query)
```

#### Function Calling Mode (phi4-mini-fc) - Only Mode
- **Native Ollama function calling**: Direct API calls with tool definitions from ToolRegistry
- **Auto-tool selection**: Model chooses appropriate tool from 8 unified options
- **Robust validation**: Parameter checking and error handling
- **Optimal performance**: Direct model-to-tool communication via registry

### 2. ToolRegistry - Single Source of Truth

Central registry managing all 8 unified tools with auto-schema generation:

```python
class ToolRegistry:
    def __init__(self, metadata_store):
        self.store = metadata_store
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, BaseTool]:
        """Register all 8 unified tools"""
        return {
            'get_files': GetFilesTool(self.store),
            'get_schemas': GetSchemasTool(self.store),
            'search_metadata': SearchMetadataTool(self.store),
            'get_statistics': GetStatisticsTool(self.store),
            'find_relationships': FindRelationshipsTool(self.store),
            'detect_inconsistencies': DetectInconsistenciesTool(self.store),
            'compare_items': CompareItemsTool(self.store),
            'run_analysis': RunAnalysisTool(self.store)
        }
    
    def get_ollama_function_schemas(self) -> List[Dict]:
        """Auto-generate function calling schemas"""
        # Returns schemas for all 8 tools
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute tool by name with parameters"""
        return self.tools[tool_name].execute(**kwargs)
```

**Benefits:**
- **Single source of truth**: No tool duplication
- **Auto-schema generation**: Function calling schemas created automatically
- **Clean integration**: SchemaAgent uses registry for all tool operations
- **Easy extension**: Add new tools by extending BaseTool class

### 3. Strategy Pattern Components

Pluggable components for extensible analysis:

```python
# Base classes for strategy pattern
class BaseSearcher:
    def search(self, term: str) -> List[Dict]: pass

class BaseAnalyzer:  
    def analyze(self, analysis_type: str) -> List[Dict]: pass

class BaseFormatter:
    def format(self, data: Any, context: Dict) -> str: pass

# Concrete implementations
class ColumnSearcher(BaseSearcher):
    """Search for columns across files"""
    
class RelationshipAnalyzer(BaseAnalyzer):
    """Find relationships between files/columns"""
    
class TextFormatter(BaseFormatter):
    """Professional text formatting with emojis"""
```

**Benefits:**
- **Pluggable components**: Easy to add new search/analysis/formatting types
- **Clean separation**: Search vs analysis vs formatting concerns
- **Testable**: Each component can be unit tested independently
- **Optional dependencies**: Graceful fallback when pandas/tabulate unavailable

### 4. Interaction Flow

```python
class ChatInterface:
    def start(self):
        """Main interaction loop with commands and natural language"""
```

**Features:**
- Commands: `/scan`, `/help`, `/status`, `/exit`
- Natural language query processing
- Function calling mode only (simplified)
- Status indicators show 8 available tools

#### Function Calling Flow

1. **User Query**: "Find columns that appear in multiple files"
2. **Model Selection**: Detect "phi4-mini-fc" → Function Calling Mode
3. **Function Call**: Model calls `find_relationships(analysis_type="column_overlap")`
4. **Tool Execution**: ToolRegistry executes with appropriate searcher/analyzer
5. **Response**: Formatted results returned to user

#### Error Handling Flow

If model doesn't support function calling:
1. **Detection**: Model name check fails
2. **Error Response**: "Function calling model required (e.g., phi4-mini-fc)"
3. **Graceful Exit**: No attempt to process query

---

## 🔧 Design Decisions

### Unified Tool Architecture
- **Simplified approach**: ToolRegistry replaces complex 3-layer tool system
- **Single source of truth**: All tool definitions in one place
- **Strategy pattern**: Pluggable searchers, analyzers, formatters for extensibility
- **No duplication**: Function calling schemas auto-generated from tool classes
- **Clean dependencies**: Core packages only (duckdb, requests, pyyaml, click)

### Function Calling Only
- **Native tool calling**: Direct Ollama API integration for phi4-mini-fc
- **No LangChain**: Removed structured output complexity and dependencies  
- **Performance**: Faster execution without LangChain overhead
- **Reliability**: Direct model-to-tool communication via ToolRegistry

### Strategy Pattern Benefits
- **Extensible**: Easy to add new search types, analysis types, output formats
- **Testable**: Isolated components for unit testing
- **Optional dependencies**: Graceful degradation when pandas/tabulate unavailable

### Technology Simplification
- **Dependency reduction**: From 10+ packages to 4 core packages
- **Removed complexity**: No LangChain chains, agents, or structured output modes
- **Direct integration**: Ollama function calling API used directly
- **Optional enhancements**: pandas/tabulate improve formatting but aren't required
- **Clean separation**: Search vs analysis vs formatting concerns

### Tool-Based Design
- **8 unified tools**: Each with specific purpose and strategy components
- **Function calling only**: Native Ollama integration with phi4-mini-fc
- **Extensible**: Easy to add new analysis functions via strategy pattern

---

## 📊 Data Flow

### Query Processing with ToolRegistry
```
Natural Language Query
    ↓
SchemaAgent → Detect Function Calling Support (phi4-mini-fc)
    ↓
ToolRegistry → Generate Function Calling Schemas for 8 Tools
    ↓
Native Ollama Function Calling → Tool Selection & Validation
    ↓
Execute Selected Tool(s) via ToolRegistry → Strategy Components
    ↓
Format Response → Return to User
```

### Auto-Detection Examples
```
Model: "phi4-mini-fc" → Function Calling Mode
Model: any other     → Error (function calling required)
```

### Query Processing Examples

#### Function Calling Mode (Primary)
```
"compare schemas across files"      → find_relationships(analysis_type="similar_schemas")
"Which files have customer_id?"     → search_metadata(search_term="customer_id", search_type="column")
"Give me a database summary"        → get_statistics(scope="database")
"Find data quality issues"          → detect_inconsistencies(check_type="data_types")
"What files do we have?"            → get_files()
"Compare customers and orders"      → compare_items(item1="customers.csv", item2="orders.csv")
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