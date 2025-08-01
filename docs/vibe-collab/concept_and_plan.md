# 🧠 TableTalk: Concept & Implementation Plan

## 🔍 Problem Statement

Our datasets are spread across multiple files (CSV, Parquet, etc.), each representing different tables. Manually inspecting their schemas, understanding commonalities, detecting inconsistencies, and exploring anomalies is time-consuming.

**Solution**: A **Python-based CLI assistant**, backed by a **local Small Language Model (SLM)**, that enables **natural language exploration of data schemas**.

---

## 🎯 Core Concept & Goals

### Vision
A **schema-aware, conversational EDA system** running fully locally with intelligent query understanding and multi-step analysis capabilities.

### Key Goals
- Extract and store schema metadata across files
- Identify schema mismatches, commonalities, and data quality issues
- Enable **natural language questions** via CLI chat with LLM-powered understanding
- Support **complex multi-step analysis** through intelligent tool orchestration
- **Local-first processing** with privacy and cost control
- **Graceful fallback** to basic mode when LLM unavailable

---

## 🏗️ Architecture Overview

```
                ┌────────────────────┐
                │   CLI Interface    │
                └────────┬───────────┘
                         ↓
                ┌────────────────────┐
                │   SchemaAgent      │  ← Unified agent with function calling
                └────────┬───────────┘
                         ↓
         ┌───────────────────────────────────────┐
         │         ToolRegistry                  │  ← Single source of truth
         └───────────┬───────────────────────────┘
                     ↓
    ┌────────────────────────────────────────────────────┐
    │  8 Unified Tools with Strategy Components          │  ← Clean architecture
    └────────┬───────────────────────────────────────────┘
             ↓
         ┌──────────────────────────────┐
         │ Metadata Store (DuckDB)      │  ← schema_info table
         └──────────────────────────────┘
```

---

## 🧰 Component Details

### 1. **SchemaAgent** (Simplified Intelligence Layer)
**Function calling only with ToolRegistry integration:**
- **Function Calling Mode**: Native Ollama function calling with phi4-mini-fc
- **Automatic Tool Selection**: ToolRegistry provides function schemas
- **Clean Architecture**: No LangChain dependencies, direct tool execution

```python
# Simplified agent with ToolRegistry
class SchemaAgent:
    def __init__(self, metadata_store, model_name="phi4-mini-fc"):
        self.tool_registry = ToolRegistry(metadata_store)
        self.supports_function_calling = self._detect_function_calling()
    
    def query(self, user_query: str) -> str:
        return self._process_with_function_calling(user_query)
```

### 2. **Schema Tools** (8 Unified Tools)
- `get_files(pattern=None)` - List files with optional filtering
- `get_schemas(file_pattern=None, detailed=True)` - Schema info for files  
- `search_metadata(search_term, search_type="column")` - Universal search across metadata
- `get_statistics(scope="database", target=None)` - Stats at various levels
- `find_relationships(analysis_type="common_columns", threshold=2)` - Find relationships between files/columns
- `detect_inconsistencies(check_type="data_types")` - Find data inconsistencies
- `compare_items(item1, item2, comparison_type="schemas")` - Compare files, columns, etc.
- `run_analysis(description)` - Handle complex analysis requests

### 3. **Metadata Store** (DuckDB)
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

### 4. **LLM Integration** (Ollama + Phi-4)
- Local model serving via Ollama
- Native function calling (no LangChain dependency)
- Direct tool registry integration
- Context-aware follow-up suggestions

---

## 🔄 Query Processing Examples

### Function Calling Mode (phi4-mini-fc) - Primary Mode
```
Input: "What files do we have?"
Processing: ToolRegistry → get_files() → Formatted Response
Output: "📁 Found 4 files: customers.csv (6 columns)..."
```

### Complex Multi-Tool Analysis
```
Input: "Find data quality issues and suggest fixes"
Processing: Native Ollama → Auto tool selection → Response
Tools Called:
1. detect_inconsistencies(check_type="data_types") → "is_active: boolean vs string"
2. find_relationships(analysis_type="common_columns") → "customer_id in 3 files"
3. run_analysis(description="data quality summary") → Comprehensive recommendations
Output: Detailed analysis with actionable recommendations
```

### Schema Comparison
```
Input: "Compare schemas between orders and customers"
Processing: ToolRegistry tool selection → Direct execution
Tools Called:
1. compare_items(item1="customers.csv", item2="orders.csv", comparison_type="schemas")
Output: Side-by-side comparison with shared/unique columns
```

---

## 🎯 Key Features

### Natural Language Understanding
- **Simple queries**: Direct regex pattern matching
- **Complex queries**: LLM-powered semantic parsing
- **Multi-part questions**: Automatic tool orchestration
- **Context awareness**: Previous conversation understanding

### Intelligent Analysis
- **Dynamic tool selection**: Choose optimal analysis approach
- **Multi-step pipelines**: Combine tools for comprehensive insights
- **Response synthesis**: Coherent insights from multiple sources
- **Proactive suggestions**: Intelligent follow-up recommendations

### Local-First Design
- **Privacy**: All processing happens locally
- **Cost control**: No external API calls
- **Reliability**: Works offline
- **Performance**: Fast local inference with phi4-mini-fc

### Clean Architecture
- **Single source of truth**: ToolRegistry eliminates duplication
- **Strategy pattern**: Pluggable searchers, analyzers, formatters
- **No complex fallbacks**: Function calling only
- **Simplified dependencies**: Core packages only (no LangChain)
