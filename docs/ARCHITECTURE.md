# 🏗️ TableTalk Architecture

**Last Updated**: August 4, 2025  
**Version**: 4.0 (Simplified & Clean)

## 📊 System Overview

TableTalk is a conversational data schema explorer using local AI models. It features a clean 4-layer architecture with function calling integration.

## 🎯 Core Architecture

### **4-Layer Design**
```
┌─────────────────────────────────────────────────────────┐
│                CLI Interface                            │
│         • Natural language chat                        │
│         • Commands (/scan, /help, /status)             │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│               SchemaAgent                               │
│         • Function calling with Ollama                 │
│         • Tool selection and execution                 │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              ToolRegistry                               │
│    • 8 unified tools in 4 organized files             │
│    • Auto-schema generation for function calling       │
│    • Strategy pattern for extensibility                │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│           Data Layer & Components                       │
│  ┌─────────────┐ ┌────────────┐ ┌─────────────┐        │
│  │ Searchers   │ │ Analyzers  │ │ Formatters  │        │
│  │ • Column    │ │ • Relations│ │ • Text      │        │
│  │ • File      │ │ • Quality  │ │ • Table     │        │
│  │ • Semantic  │ │ • Semantic │ │             │        │
│  └─────────────┘ └────────────┘ └─────────────┘        │
│                                                         │
│              MetadataStore (DuckDB)                     │
└─────────────────────────────────────────────────────────┘
```

### **Technology Stack**
- **Python 3.11+** - Primary language with type hints
- **DuckDB** - Embedded analytics database
- **Ollama** - Local LLM serving with function calling
- **Phi-4-mini-fc** - Microsoft's function calling enabled model
- **Optional**: sentence-transformers (semantic search), pandas, tabulate

## 🛠️ Component Overview

### **Tool Organization (8 Tools in 4 Files)**
```
src/tools/
├── basic_tools.py      # GetFiles, GetSchemas, GetStatistics
├── search_tools.py     # SearchMetadata (with semantic search)
├── comparison_tools.py # FindRelationships, DetectInconsistencies  
├── utility_tools.py    # CompareItems, RunAnalysis
├── tool_registry.py    # Central coordination
└── core/              # Strategy components
    ├── base_components.py  # Abstract base classes
    ├── searchers.py        # Search strategies
    ├── analyzers.py        # Analysis strategies
    ├── formatters.py       # Output formatters
    └── semantic_search.py  # AI-powered search (optional)
```

### **Key Features**
- **Function calling only** - Direct Ollama integration
- **Strategy pattern** - Pluggable searchers, analyzers, formatters
- **Semantic intelligence** - Optional AI-powered understanding
- **Auto-discovery** - Tools register themselves automatically
- **Error resilience** - Graceful fallbacks throughout

## 🔄 Data Flow

### **Query Processing**
```
User Query → CLI → SchemaAgent → ToolRegistry → Tool Execution → Response
```

### **Function Calling Integration**
```
"Find columns shared between files"
    ↓
Ollama phi4-mini-fc model processes query
    ↓
Calls: find_relationships(analysis_type="common_columns")
    ↓
ToolRegistry executes FindRelationshipsTool
    ↓
Uses RelationshipAnalyzer + TextFormatter
    ↓
Returns formatted results to user
```

## 📊 Data Storage

### **Metadata Schema (DuckDB)**
```sql
CREATE TABLE schema_info (
    file_name TEXT,
    column_name TEXT,
    data_type TEXT,
    null_count INTEGER,
    unique_count INTEGER,
    total_rows INTEGER,
    file_size_mb REAL,
    last_scanned TIMESTAMP
);
```

**Benefits:**
- Normalized storage for flexible queries
- Performance indexes on common search patterns
- Embedded database for local-first approach

## 🎛️ Configuration

### **Model Requirements**
- **Required**: phi4-mini-fc (function calling enabled)
- **Optional**: sentence-transformers (semantic search)
- **Fallback**: Graceful degradation when dependencies missing

### **Performance Characteristics**
- **Simple queries**: <50ms
- **Analysis queries**: 100-500ms
- **Memory usage**: ~50MB base, ~200MB with semantic models
- **Scalability**: Optimized for 100-500 files

## 🔧 Extension Points

### **Adding New Tools**
```python
class NewTool(BaseTool):
    description = "Tool description for LLM"
    
    def get_parameters_schema(self) -> Dict:
        return {"type": "object", "properties": {...}}
    
    def execute(self, **kwargs) -> str:
        # Implementation using strategy components
        pass

# Register in ToolRegistry._register_tools()
tools['new_tool'] = NewTool(self.store)
```

### **Adding Strategy Components**
```python
class NewSearcher(BaseSearcher):
    def search(self, term: str) -> List[Dict]:
        # Custom search logic
        pass

# Use in tools
searcher = NewSearcher(metadata_store)
results = searcher.search(search_term)
```

## � Design Principles

1. **Single Responsibility** - Each component has one clear purpose
2. **Strategy Pattern** - Pluggable algorithms for flexibility
3. **Local-First** - All processing on user's machine
4. **Fail-Safe Defaults** - Graceful fallbacks for missing dependencies
5. **Function Calling Only** - Simplified processing path
