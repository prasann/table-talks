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
                │    LLM Agent       │  ← Orchestrates everything
                └────────┬───────────┘
                         ↓
                ┌────────────────────┐
                │ Context Manager    │  ← LLM parsing + regex fallback
                └────────┬───────────┘
                         ↓
              ┌────────────────────────┐
              │   Schema Tools         │  ← 8 specialized functions
              └────────┬───────────────┘
                       ↓
         ┌──────────────────────────────┐
         │ Metadata Store (DuckDB)      │  ← schema_info table
         └──────────────────────────────┘
```

---

## 🧰 Component Details

### 1. **Context Manager** (Intelligence Layer)
**Dual-mode query processing:**
- **LLM Mode**: Complex query parsing, multi-step planning, response synthesis
- **Basic Mode**: Regex pattern matching for simple queries

```python
# Example LLM parsing
"Find data quality issues and suggest fixes" → 
{
  "steps": [
    {"tool": "detect_type_mismatches"},
    {"tool": "detect_semantic_type_issues"}, 
    {"tool": "detect_column_name_variations"}
  ],
  "synthesis": "Combine findings with recommendations"
}
```

### 2. **Schema Tools** (8 Functions)
- `get_file_schema(file_name)` - Detailed schema for specific file
- `list_files()` - All scanned files with statistics
- `find_columns(column_name)` - Files containing specific columns
- `detect_type_mismatches()` - Same column, different types
- `find_common_columns()` - Shared columns across files
- `database_summary()` - Overall statistics
- `detect_semantic_type_issues()` - Type vs naming mismatches
- `detect_column_name_variations()` - Similar names, different conventions

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

### 4. **LLM Integration** (Ollama + Phi-3)
- Local model serving via Ollama
- LangChain integration for tool orchestration
- Intelligent query understanding and response synthesis
- Context-aware follow-up suggestions

---

## 🔄 Query Processing Examples

### Simple Queries (Basic Mode)
```
Input: "What files do we have?"
Processing: Regex → list_files() → Response
Output: "📁 Found 5 files: orders.csv (8 columns)..."
```

### Complex Queries (LLM Mode)
```
Input: "Find data quality issues and suggest fixes"
Processing: LLM Parse → Multi-tool execution → Synthesis
Steps:
1. detect_type_mismatches() → "user_id: int64 vs string"
2. detect_semantic_type_issues() → "amount stored as text"
3. detect_column_name_variations() → "cust_id vs customer_id"
Output: Synthesized insights + actionable recommendations
```

---

## 🚀 Implementation Plan

### Phase 1: Core Infrastructure ✅
- [x] Project structure and dependencies
- [x] DuckDB metadata storage with schema
- [x] CSV/Parquet schema extraction
- [x] Basic tool functions

### Phase 2: Intelligence Layer ✅  
- [x] Context manager with LLM integration
- [x] Ollama + Phi-3 setup
- [x] Query parsing (LLM + regex fallback)
- [x] Multi-step analysis capabilities

### Phase 3: Enhanced Features ✅
- [x] 8 comprehensive schema tools
- [x] Intelligent response synthesis
- [x] Follow-up suggestion generation
- [x] Error handling and graceful degradation

### Phase 4: User Experience ✅
- [x] CLI interface with status monitoring
- [x] Natural language conversation flow
- [x] Help system and documentation
- [x] Testing and refinement

### Phase 5: Simplification ✅
- [x] Consolidated architecture (removed "enhanced" complexity)
- [x] Single context manager with dual-mode operation
- [x] Streamlined codebase (~40% reduction)
- [x] Clean documentation

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
- **Performance**: Fast local inference

### Graceful Degradation
- **LLM optional**: Full functionality without Ollama
- **Progressive enhancement**: Better experience with LLM
- **Error resilience**: Continues working despite failures
- **Clear status**: Users know current capabilities

---

## 📊 Success Metrics

### Functional Requirements ✅
- Extract schemas from CSV/Parquet files
- Natural language query processing
- Multi-step analysis for complex questions
- Local LLM integration with fallback

### Performance Requirements ✅
- Schema extraction: < 5 seconds for 10MB files
- Query response: < 3 seconds typical
- Memory usage: < 500MB for normal datasets
- File support: Up to 100MB per file

### User Experience ✅
- Intuitive natural language interface
- Clear error messages and guidance
- Helpful follow-up suggestions
- Status monitoring and help system

---

## 🔮 Future Extensions

### Short-term Enhancements
- **Advanced file formats**: JSON, XML schema extraction
- **Data profiling**: Statistical analysis and anomaly detection
- **Export capabilities**: Generate data dictionaries and reports
- **Batch processing**: Directory-wide analysis

### Medium-term Features  
- **Web interface**: Streamlit-based dashboard
- **Visualization**: Schema diagrams and data flow charts
- **Collaboration**: Team sharing and annotation
- **Integration**: API endpoints for external tools

### Long-term Vision
- **Embedding search**: Semantic similarity across schemas
- **Code generation**: Auto-generate SQL/Python for analysis
- **ML integration**: Automated data quality scoring
- **Enterprise features**: Role-based access, audit trails

---

## 🛠️ Technology Stack

### Core Technologies
- **Python 3.11+**: Primary language
- **DuckDB**: Fast embedded analytics database
- **Pandas/PyArrow**: Data processing and file I/O
- **LangChain**: LLM framework and tool integration

### LLM Stack
- **Ollama**: Local model serving
- **Phi-3**: Microsoft's efficient reasoning model
- **Fallback**: Regex patterns for basic queries

### Development Tools
- **pytest**: Testing framework
- **black/flake8**: Code formatting and linting
- **mypy**: Type checking
- **YAML**: Configuration management

---

## 🎉 Current Status

**TableTalk is fully implemented and functional!**

### ✅ Completed Features
- Intelligent query understanding (LLM + fallback)
- 8 comprehensive schema analysis tools
- Multi-step analysis with response synthesis
- Clean CLI interface with status monitoring
- Local-first processing with Ollama integration
- Comprehensive error handling and graceful degradation
- Simplified, maintainable architecture

### 🧪 Ready for Testing
```bash
# Quick start
python src/main.py
/scan data/sample
# Then ask natural language questions!
```

### 📈 Impact
- **Developer productivity**: Natural language data exploration
- **Data quality**: Automated schema analysis and issue detection
- **Local privacy**: No external dependencies for core functionality
- **Extensibility**: Clean architecture for future enhancements

---

**TableTalk transforms schema exploration from manual inspection to intelligent conversation!** 🗣️
