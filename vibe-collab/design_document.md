# 🏗️ TableTalk Design Document

## 📋 Overview

This document outlines the design choices, architectural decisions, and low-level implementation details for TableTalk - a conversational EDA assistant for exploring data schemas using local Small Language Models.

---

## 🎯 Design Philosophy

### Core Principles
1. **Local-First**: All processing happens locally for privacy and cost control
2. **Conversational Interface**: Natural language queries over traditional CLI commands
3. **Schema-Focused**: Emphasize data structure understanding over data analysis
4. **Extensible Architecture**: Modular design for easy feature additions
5. **Developer-Friendly**: Clear abstractions and comprehensive error handling

### Technology Stack Rationale
- **Python**: Ecosystem strength for data processing and ML integration
- **DuckDB**: Fast, embedded analytics database perfect for metadata storage
- **LangChain**: Mature framework for LLM tool integration
- **Ollama**: Local LLM serving with excellent model management
- **Phi-3**: Microsoft's efficient small language model optimized for reasoning

---

## 🏛️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   CLI Interface │  │  Future: Web UI │  │ Future: API  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   Agent Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Context Manager │  │   LLM Agent     │  │    Memory    │ │
│  │   (Intent)      │  │  (Phi-3 + LC)  │  │ Management   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Tool Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Schema Tools    │  │  File Tools     │  │ Analysis     │ │
│  │ (6 functions)   │  │                 │  │ Tools        │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   Data Layer                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Schema Extractor│  │  Metadata Store │  │ File System  │ │
│  │ (CSV/Parquet)   │  │    (DuckDB)     │  │   Access     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Design Choices & Rationale

### 1. **DuckDB for Metadata Storage**

**Choice**: DuckDB over SQLite, PostgreSQL, or in-memory storage

**Rationale**:
- **Performance**: Columnar storage optimized for analytics queries
- **Simplicity**: Embedded database, no server management
- **SQL Compatibility**: Rich SQL features for complex schema queries
- **Python Integration**: Excellent pandas/PyArrow integration
- **Scalability**: Handles millions of rows efficiently

**Implementation**:
```sql
-- Normalized schema with indexes for performance
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

CREATE INDEX idx_file_name ON schema_info(file_name);
CREATE INDEX idx_column_name ON schema_info(column_name);
```

### 2. **Modular Tool Architecture**

**Choice**: Discrete function-based tools over monolithic query processor

**Rationale**:
- **LangChain Compatibility**: Natural fit with LangChain's tool paradigm
- **Testability**: Each tool function can be tested independently
- **Extensibility**: Easy to add new tools without modifying existing code
- **Debugging**: Clear separation of concerns for troubleshooting

**Tool Design Pattern**:
```python
def tool_function(parameter: str) -> str:
    """
    1. Validate input
    2. Query metadata store
    3. Format results for LLM consumption
    4. Handle errors gracefully
    """
    try:
        # Business logic
        result = self.store.query_method(parameter)
        
        # Format for user display
        return self._format_result(result)
    except Exception as e:
        return f"Error: {str(e)}"
```

### 3. **Intent-Based Context Management**

**Choice**: Explicit intent detection over pure LLM interpretation

**Rationale**:
- **Reliability**: Regex patterns more predictable than LLM parsing
- **Performance**: Fast local processing vs. LLM round-trips
- **Control**: Explicit tool routing for consistent behavior
- **Fallback**: Can still handle general queries via LLM

**Intent Patterns**:
```python
self.intent_patterns = {
    'schema_query': [
        r'schema\s+(?:of\s+|for\s+)?(.+)',
        r'structure\s+(?:of\s+|for\s+)?(.+)',
        r'columns?\s+(?:in\s+|of\s+|for\s+)?(.+)'
    ],
    'file_list': [
        r'(?:what\s+)?files?\s+(?:do\s+)?(?:we\s+)?(?:have|available)',
        r'list\s+(?:all\s+)?files?'
    ]
    # ... more patterns
}
```

### 4. **Pandas-Based Schema Extraction**

**Choice**: Pandas over custom parsers or other libraries

**Rationale**:
- **Robustness**: Mature CSV/Parquet parsing with edge case handling
- **Type Inference**: Automatic data type detection
- **Sampling**: Built-in sampling for large files
- **Ecosystem**: Consistent with data science workflows

**Extraction Strategy**:
```python
def _extract_schema_info(self, df: pd.DataFrame) -> List[Dict]:
    """
    For each column:
    1. Get basic statistics (nulls, uniques)
    2. Normalize data types
    3. Calculate percentages
    4. Store metadata consistently
    """
```

### 5. **Conversation Memory Management**

**Choice**: Sliding window memory over persistent storage

**Rationale**:
- **Context Relevance**: Recent exchanges more important than full history
- **Token Efficiency**: Prevents context window overflow
- **Performance**: Faster inference with shorter context
- **Privacy**: No permanent conversation storage

**Memory Configuration**:
```python
self.memory = ConversationBufferWindowMemory(
    k=5,  # Last 5 exchanges
    memory_key="chat_history",
    return_messages=True
)
```

---

## 🔍 Low-Level Design Details

### 1. **MetadataStore Class Architecture**

```python
class MetadataStore:
    """
    Responsibilities:
    - Database connection management
    - Schema CRUD operations
    - Complex analytical queries
    - Data consistency
    """
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._init_database()
    
    # Connection Pattern: Context manager for safety
    def _query(self, sql: str, params: List = None):
        with duckdb.connect(str(self.db_path)) as conn:
            return conn.execute(sql, params or []).fetchall()
    
    # Atomic Operations: Clear + Insert for consistency
    def store_schema_info(self, schema_data: List[Dict]):
        with duckdb.connect(str(self.db_path)) as conn:
            file_name = schema_data[0]['file_name']
            conn.execute("DELETE FROM schema_info WHERE file_name = ?", [file_name])
            conn.executemany("INSERT INTO schema_info ...", schema_data)
```

**Key Design Decisions**:
- **Atomic Updates**: Delete + Insert to prevent partial updates
- **Connection Pooling**: Context managers for automatic cleanup
- **Parameterized Queries**: SQL injection prevention
- **Graceful Degradation**: Continue on individual column failures

### 2. **SchemaExtractor Class Architecture**

```python
class SchemaExtractor:
    """
    Responsibilities:
    - File format detection
    - Smart CSV parsing (encoding/separator detection)
    - Data type normalization
    - Large file handling via sampling
    """
    
    def extract_from_file(self, file_path: str) -> List[Dict]:
        # 1. Validation Layer
        self._validate_file(file_path)
        
        # 2. Format-Specific Loading
        df = self._load_data(file_path)
        
        # 3. Schema Analysis
        return self._extract_schema_info(df, file_path)
    
    # Robust CSV Parsing: Try multiple configurations
    def _load_csv(self, path: Path) -> pd.DataFrame:
        encodings = ['utf-8', 'latin-1', 'cp1252']
        separators = [',', ';', '\t']
        
        for encoding in encodings:
            for sep in separators:
                try:
                    # Test with small sample first
                    sample = pd.read_csv(path, encoding=encoding, sep=sep, nrows=10)
                    if len(sample.columns) > 1:  # Reasonable parse
                        return pd.read_csv(path, encoding=encoding, sep=sep, 
                                         nrows=self.sample_size)
                except:
                    continue
```

**Key Design Decisions**:
- **Progressive Fallback**: Try optimal configs first, fallback gracefully
- **Sample-First Strategy**: Test parsing on small chunks
- **File Size Limits**: Prevent memory exhaustion
- **Error Isolation**: Individual column failures don't stop extraction

### 3. **LLM Agent Integration Pattern**

```python
class LLMAgent:
    """
    Orchestrates:
    - Ollama connection management
    - LangChain agent lifecycle
    - Tool registration and execution
    - Error handling and recovery
    """
    
    def __init__(self, model_name: str, schema_tools: SchemaTools):
        self._init_llm()      # Ollama connection
        self._init_agent()    # LangChain setup
    
    def query(self, user_input: str) -> str:
        # 1. Intent Detection (fast local processing)
        intent, param = self.context_manager.detect_intent(user_input)
        
        # 2. Agent Execution (LLM + tools)
        response = self.agent.run(user_input)
        
        # 3. Response Filtering (token management)
        return self.context_manager.filter_context_for_llm(response)
```

**Integration Strategy**:
- **Fail-Fast Validation**: Test Ollama connection at startup
- **Graceful Degradation**: CLI works even if LLM unavailable
- **Tool Registration**: Dynamic tool discovery from SchemaTools
- **Context Management**: Automatic prompt engineering

### 4. **Error Handling Strategy**

**Layered Error Handling**:
```python
# Layer 1: Component Level (e.g., MetadataStore)
try:
    result = conn.execute(sql, params)
except DatabaseError as e:
    self.logger.error(f"Database error: {e}")
    raise

# Layer 2: Service Level (e.g., SchemaTools)
try:
    return self.store.get_file_schema(file_name)
except Exception as e:
    return f"Error retrieving schema: {str(e)}"

# Layer 3: Interface Level (e.g., CLI)
try:
    response = self.agent.query(user_input)
except Exception as e:
    print(f"❌ Error: {str(e)}")
```

**Error Categories**:
- **User Errors**: File not found, invalid commands
- **System Errors**: Database connection, Ollama unavailable
- **Data Errors**: Corrupted files, parsing failures
- **LLM Errors**: Model failures, token limits

---

## 📊 Data Flow Diagrams

### Schema Extraction Flow
```
File Input → Format Detection → Pandas Loading → Schema Analysis → DuckDB Storage
     ↓              ↓              ↓              ↓              ↓
  Validation   CSV/Parquet    Sampling &      Type Normal.   Atomic Update
  File Size    Auto-detect    Encoding        Statistics     (Delete+Insert)
  Format       Separators     Detection       Calculation
```

### Query Processing Flow
```
User Input → Intent Detection → Tool Selection → Database Query → Response Format
     ↓              ↓              ↓              ↓              ↓
  Natural       Regex Pattern   Function        DuckDB SQL     User-Friendly
  Language      Matching        Routing         Execution      Display
```

### LLM Agent Flow
```
Query → Context Prep → Agent Execution → Tool Calls → Response Assembly
  ↓         ↓              ↓              ↓              ↓
History   Intent +      LangChain      Schema Tools   Filter &
Memory    Parameters    ReAct Loop     Database Ops   Format
```

---

## 🔧 Configuration Management

### Configuration Strategy
```yaml
# config.yaml - Environment-specific settings
database:
  path: "./database/metadata.duckdb"

llm:
  model: "phi3:mini"
  base_url: "http://localhost:11434"
  temperature: 0.1

scanner:
  max_file_size_mb: 100
  sample_size: 1000
```

**Design Principles**:
- **Environment Separation**: Dev/Prod configs
- **Sensible Defaults**: Work out-of-box
- **Override Capability**: Environment variables
- **Validation**: Type checking and bounds

---

## 🧪 Testing Strategy

### Test Architecture
```python
# Unit Tests: Component isolation
class TestMetadataStore:
    def setup_method(self):
        self.temp_db = create_temp_database()
    
    def test_store_and_retrieve_schema(self):
        # Test atomic operations

# Integration Tests: Component interaction
class TestSchemaExtraction:
    def test_csv_to_database_flow(self):
        # End-to-end file processing

# System Tests: Full workflow
class TestCLIInterface:
    def test_complete_user_journey(self):
        # Scan → Query → Response
```

### Testing Principles
- **Isolation**: Each test creates clean state
- **Realistic Data**: Use representative CSV/Parquet files
- **Error Scenarios**: Test failure modes explicitly
- **Performance**: Benchmark large file handling

---

## 🚀 Performance Considerations

### Database Optimization
- **Indexes**: On file_name and column_name for fast lookups
- **Columnar Storage**: DuckDB's strength for analytics
- **Query Optimization**: Parameterized queries, batch operations

### Memory Management
- **File Sampling**: Process subsets of large files
- **Connection Pooling**: Reuse database connections
- **LLM Context**: Sliding window memory management

### Scalability Targets
- **Files**: 1000+ files in database
- **Columns**: 10,000+ columns total
- **File Size**: Up to 100MB per file
- **Response Time**: <3 seconds for typical queries

---

## 🔮 Future Extensibility

### Planned Extension Points

**1. Additional File Formats**
```python
# New extractor classes following same interface
class JSONExtractor(BaseExtractor):
    def extract_from_file(self, file_path: str) -> List[Dict]:
        # JSON schema extraction logic
```

**2. Enhanced Analysis Tools**
```python
# New tool categories
class DataQualityTools:
    def detect_anomalies(self, file_name: str) -> str:
        # Statistical outlier detection
    
class RelationshipTools:
    def find_foreign_keys(self) -> str:
        # Cross-table relationship inference
```

**3. Alternative Interfaces**
```python
# Web interface via Streamlit
class WebInterface:
    def create_dashboard(self):
        # Interactive web UI
        
# REST API via FastAPI
class APIInterface:
    def create_endpoints(self):
        # HTTP API for integrations
```

**4. Advanced LLM Features**
- **Embedding-based context**: Semantic search over schemas
- **Multi-turn planning**: Complex query decomposition
- **Code generation**: SQL/Python code for data analysis

---

## 📝 Conclusion

TableTalk's design emphasizes **modularity**, **reliability**, and **extensibility**. The architecture supports the MVP requirements while providing clear paths for future enhancements. Key strengths include:

- **Robust data processing** with comprehensive error handling
- **Flexible LLM integration** that works with any Ollama model
- **Efficient metadata storage** optimized for schema queries
- **Intuitive user experience** through natural language interaction

The design successfully balances **simplicity** for the MVP with **architectural flexibility** for future growth.

---

*This document serves as the technical foundation for TableTalk development and should be updated as the system evolves.*
