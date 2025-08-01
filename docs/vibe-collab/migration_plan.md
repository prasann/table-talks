# 🗺️ TableTalk Tool Architecture Migration Plan

## 📊 Current State Analysis

### Current Structure
```
src/tools/
├── atomic_schema_tools.py     # 5 methods + helpers
├── composite_schema_tools.py  # 4 methods + helpers  
├── schema_tools.py           # Wrapper class
└── __init__.py

src/agent/
└── schema_agent.py           # Dual tool definitions (function calling + structured)
```

### Problems with Current Architecture
1. **Tool Definition Duplication**: Same tools defined in multiple places (tools/*.py + schema_agent.py)
2. **Complex Layer Structure**: 3 classes (Atomic + Composite + SchemaTools wrapper)
3. **Dual Processing Modes**: Function calling + structured output adds complexity
4. **Maintenance Overhead**: Changes require updates in multiple files
5. **Limited Extensibility**: Hard to add new analysis types without creating new tools
6. **Over-engineering**: Too much abstraction for 100-150 files use case

## 🎯 Target Architecture

### New Structure
```
src/tools/
├── unified_tools.py          # 8 tool classes  
├── core/                     # Strategy pattern implementations
│   ├── __init__.py
│   ├── base_components.py    # Abstract base classes
│   ├── searchers.py         # ColumnSearcher, FileSearcher, TypeSearcher
│   ├── analyzers.py         # RelationshipAnalyzer, ConsistencyChecker
│   └── formatters.py        # TableFormatter, TextFormatter
└── __init__.py

src/agent/
└── schema_agent.py          # Function calling only (simplified)
```

### Target Tool Set (8 Unified Tools)

#### **1. `get_files(pattern=None)`**
- **Purpose**: List files with optional filtering
- **Replaces**: `list_files()`
- **Examples**: `get_files()`, `get_files("customer")`

#### **2. `get_schemas(file_pattern=None, detailed=True)`**
- **Purpose**: Get schema info for files
- **Replaces**: `get_file_schema()`, parts of `get_database_summary()`
- **Examples**: `get_schemas("customers")`, `get_schemas()` (all files)

#### **3. `search_metadata(search_term, search_type="column")`**
- **Purpose**: Universal search across all metadata
- **Replaces**: `search_columns()`, `get_column_data_types()`
- **Examples**: `search_metadata("customer", "column")`, `search_metadata("INTEGER", "type")`

#### **4. `get_statistics(scope="database", target=None)`**
- **Purpose**: Get stats at various levels
- **Replaces**: `get_database_summary()`
- **Examples**: `get_statistics("database")`, `get_statistics("file", "customers.csv")`

#### **5. `find_relationships(analysis_type="common_columns", threshold=2)`**
- **Purpose**: Find various relationships between files/columns
- **Replaces**: `find_common_columns()`, parts of similar schema detection
- **Examples**: `find_relationships("common_columns")`, `find_relationships("similar_schemas")`

#### **6. `detect_inconsistencies(check_type="data_types")`**
- **Purpose**: Find various types of data inconsistencies
- **Replaces**: `detect_type_mismatches()`
- **Examples**: `detect_inconsistencies("data_types")`, `detect_inconsistencies("naming_patterns")`

#### **7. `compare_items(item1, item2, comparison_type="schemas")`**
- **Purpose**: Compare any two items (files, columns, etc.)
- **Replaces**: `compare_two_files()`
- **Examples**: `compare_items("file1.csv", "file2.csv", "schemas")`

#### **8. `run_analysis(description)`**
- **Purpose**: Handle complex analysis requests that don't fit standard patterns
- **Replaces**: Complex composite logic, provides escape hatch
- **Examples**: `run_analysis("find files with most similar column structures")`

## 🚀 Migration Strategy: 4-Phase Approach

### **Phase 1: Create New Tool Architecture (No Breaking Changes)** ✅ **COMPLETED**
**Duration**: ✅ **Completed in ~2 hours** (August 1, 2025)  
**Goal**: ✅ Build new tools alongside existing ones

#### Step 1.1: Create Core Infrastructure
```
src/tools/core/
├── __init__.py
├── base_components.py       # Abstract base classes
├── searchers.py            # Search strategy implementations
├── analyzers.py            # Analysis strategy implementations
└── formatters.py           # Output formatting strategies
```

**Core Components to Implement:**
- `BaseSearcher` - Abstract searcher interface
- `BaseAnalyzer` - Abstract analyzer interface  
- `BaseFormatter` - Abstract formatter interface
- `ColumnSearcher` - Extract logic from `search_columns()` + `get_column_data_types()`
- `FileSearcher` - Extract logic from `list_files()` + `get_file_schema()`
- `RelationshipAnalyzer` - Extract logic from composite tools
- `TableFormatter` - Clean table output formatting
- `TextFormatter` - Current text-based formatting

#### Step 1.4: **📚 Update Documentation (Phase 1)**
```markdown
# Create/Update the following documentation files:

## docs/vibe-collab/phase1_progress.md
- ✅ Core infrastructure created
- ✅ Base classes implemented  
- ✅ Strategy components working
- 🔄 Current status and next steps
- ⚠️ Known issues and blockers

## docs/ARCHITECTURE.md (new file)
- New tool architecture overview
- Strategy pattern explanation
- Component interaction diagrams
- Migration status tracker

## docs/DEVELOPMENT.md (new file)  
- Development setup for new architecture
- How to add new tools
- Testing strategy during migration
- Code organization guidelines

## Update docs/USAGE.md
- Add note about migration in progress
- Document any temporary limitations
- Link to migration progress docs
```

#### Step 1.2: Create Unified Tools Module
```python
# src/tools/unified_tools.py
from .core.searchers import ColumnSearcher, FileSearcher
from .core.analyzers import RelationshipAnalyzer, ConsistencyChecker
from .core.formatters import TableFormatter, TextFormatter

class BaseTool:
    """Base class for all tools - optimized for Ollama function calling."""
    def __init__(self, metadata_store):
        self.store = metadata_store
        
    def get_parameters_schema(self) -> Dict:
        """Return JSON schema for tool parameters (for Ollama function calling)."""
        raise NotImplementedError
        
    def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters."""
        raise NotImplementedError

class SearchMetadataTool(BaseTool):
    description = "Search across metadata. search_type: 'column', 'file', 'type'"
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "search_term": {"type": "string", "description": "Term to search for"},
                "search_type": {"type": "string", "enum": ["column", "file", "type"], "default": "column"}
            },
            "required": ["search_term"]
        }
    
    def execute(self, search_term: str, search_type: str = "column") -> str:
        # Delegate to appropriate searcher
        searchers = {
            "column": ColumnSearcher(self.store),
            "file": FileSearcher(self.store),
            "type": TypeSearcher(self.store)
        }
        return searchers[search_type].search(search_term)

class GetSchemasTool(BaseTool):
    description = "Get schema info for files, optionally filtered by pattern"
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object", 
            "properties": {
                "file_pattern": {"type": "string", "description": "Optional file pattern to filter"},
                "detailed": {"type": "boolean", "default": True}
            },
            "required": []
        }
    
    def execute(self, file_pattern: str = None, detailed: bool = True) -> str:
        # Implementation
        pass

# ... other 6 tools
```

#### Step 1.5: **📚 Complete Phase 1 Documentation**
```markdown
# After implementing all Phase 1 components:

## docs/vibe-collab/phase1_complete.md
- ✅ All core infrastructure implemented
- ✅ Tool registry working
- ✅ Basic tool classes created
- ✅ Import resolution verified
- 📝 Manual testing results
- ➡️ Ready for Phase 2

## Update docs/vibe-collab/migration_plan.md
- Mark Phase 1 tasks as complete
- Note any deviations from original plan
- Update Phase 2 start date

## docs/TROUBLESHOOTING.md updates
- Add common Phase 1 issues and solutions
- Import path problems
- Strategy component initialization issues
- Tool registry debugging tips
```

#### Step 1.3: Create Tool Registry
```python
# src/tools/tool_registry.py
class ToolRegistry:
    """Registry for unified tools - generates schemas for Ollama function calling."""
    
    def __init__(self, metadata_store):
        self.store = metadata_store
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, BaseTool]:
        """Register all available tools."""
        return {
            'search_metadata': SearchMetadataTool(self.store),
            'get_schemas': GetSchemasTool(self.store),
            'get_files': GetFilesTool(self.store),
            'get_statistics': GetStatisticsTool(self.store),
            'find_relationships': FindRelationshipsTool(self.store),
            'detect_inconsistencies': DetectInconsistenciesTool(self.store),
            'compare_items': CompareItemsTool(self.store),
            'run_analysis': RunAnalysisTool(self.store)
        }
    
    def get_ollama_function_schemas(self) -> List[Dict]:
        """Generate Ollama function calling schemas."""
        schemas = []
        for name, tool in self.tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": tool.get_parameters_schema()
                }
            })
        return schemas
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name."""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"
        return self.tools[tool_name].execute(**kwargs)
```

### **Phase 2: Update Agent Integration**
**Duration**: 1 day  
**Goal**: Switch agent to use new tools while keeping old ones as backup

#### Step 2.1: Update SchemaAgent
```python
# Simplify schema_agent.py - remove structured output mode entirely
class SchemaAgent:
    def __init__(self, metadata_store, model_name="phi3", base_url="http://localhost:11434"):
        self.tool_registry = ToolRegistry(metadata_store)  # Single source
        self.model_name = model_name
        self.base_url = base_url
        
        # Auto-detect function calling support only
        self.supports_function_calling = self._detect_function_calling()
        if not self.supports_function_calling:
            raise ValueError(f"Model {model_name} doesn't support function calling. Please use a function calling enabled model like phi4-mini-fc")
        
    def _detect_function_calling(self) -> bool:
        """Detect if model supports native function calling."""
        function_calling_indicators = ["phi4-mini-fc", "phi4-mini:fc", "phi4:fc"]
        return any(indicator in self.model_name.lower() for indicator in function_calling_indicators)
        
    def _get_function_calling_tools(self) -> List[Dict]:
        return self.tool_registry.get_ollama_function_schemas()
        
    def query(self, user_query: str) -> str:
        """Process a user query using function calling only."""
        return self._process_with_function_calling(user_query)
        
    def _execute_function_calls(self, response_data: dict, original_query: str) -> str:
        # Use tool_registry.execute_tool() instead of manual dispatch
        results = []
        for tool_call in response_data.get("tool_calls", []):
            tool_name = tool_call["function"]["name"]
            args = tool_call["function"]["arguments"]
            result = self.tool_registry.execute_tool(tool_name, **args)
            results.append(result)
        return "\n\n".join(results)
```
```

#### Step 2.3: **📚 Phase 2 Documentation Updates**
```markdown
# Document Phase 2 progress and agent integration:

## docs/vibe-collab/phase2_progress.md
- ✅ SchemaAgent simplified (function calling only)
- ✅ Tool registry integration working
- ✅ LangChain dependencies removed
- 🔄 Agent testing status
- ⚠️ Integration issues and solutions

## Update docs/ARCHITECTURE.md
- Add agent-tool integration flow diagram
- Document function calling schema generation
- Note removed structured output mode

## Update docs/DEVELOPMENT.md
- How to test agent integration
- Manual testing procedures
- Debugging agent-tool communication

## Update docs/USAGE.md
- Document model requirements (phi4-mini-fc)
- Remove references to structured output mode
- Update installation instructions (remove LangChain)
```

#### Step 2.2: Remove LangChain Dependencies
```python
# Clean up imports and remove LangChain structured output code
# Remove from requirements.txt:
# - langchain
# - langchain_community  
# - langchain_experimental

# Keep only:
# - requests (for Ollama API)
# - duckdb (for metadata store)
# - Optional: pandas, tabulate (for enhanced functionality)
```

### **Phase 3: Testing & Validation**
**Duration**: 1-2 days  
**Goal**: Ensure new tools provide same functionality

#### Step 3.1: Focus on Code Quality First
```python
# Priority: Get code working, not tests passing
# 1. Ensure all imports resolve correctly
# 2. Verify tool registry initializes without errors
# 3. Test basic tool execution manually
# 4. Fix compilation errors and import issues

# Simple smoke test approach:
def manual_smoke_test():
    from tools.tool_registry import ToolRegistry
    from metadata.metadata_store import MetadataStore
    
    store = MetadataStore("test.db")
    registry = ToolRegistry(store)
    
    # Test tool registration
    assert len(registry.tools) == 8
    
    # Test schema generation
    schemas = registry.get_ollama_function_schemas()
    assert len(schemas) == 8
    
    print("✅ Basic tool architecture working")
```

#### Step 3.2: Manual Integration Testing
```python
# Skip automated tests during migration - focus on core functionality
# Test new agent integration manually:

# 1. Test tool registry initialization
from src.tools.tool_registry import ToolRegistry
from src.metadata.metadata_store import MetadataStore

store = MetadataStore("data/metadata.db")
registry = ToolRegistry(store)
print(f"✅ Registry created with {len(registry.tools)} tools")

# 2. Test schema generation
schemas = registry.get_ollama_function_schemas()
print(f"✅ Generated {len(schemas)} function schemas")

# 3. Test basic tool execution
result = registry.execute_tool("get_files")
print(f"✅ get_files result: {result[:100]}...")

# 4. Test agent integration
from src.agent.schema_agent import SchemaAgent
agent = SchemaAgent(store, "phi4-mini-fc")
print("✅ Agent initialized successfully")

# Fix issues as they arise, don't worry about full test suite yet
```

#### Step 3.3: Performance Testing
```bash
# Focus on basic functionality during migration
# 1. Activate virtual environment
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Install new dependencies if needed
pip install pandas tabulate

# 3. Manual testing workflow:
# - Ensure imports work: python -c "from src.tools.tool_registry import ToolRegistry; print('✅ Imports work')"
# - Test basic functionality manually (see Step 3.2)
# - Fix compilation errors as they arise

# 4. Skip automated tests until Phase 4 - focus on getting code working
# Note: Current tests are failing, will fix after migration is complete
```

#### Step 3.4: **📚 Phase 3 Documentation Updates**
```markdown
# Document Phase 3 manual testing and validation:

## docs/vibe-collab/phase3_progress.md
- ✅ Manual smoke tests passing
- ✅ Tool registry initialization working
- ✅ Basic tool execution verified
- ✅ Agent integration tested manually
- 🔄 Performance validation status
- ⚠️ Issues found and resolved

## docs/vibe-collab/phase3_complete.md
- ✅ All core functionality working
- ✅ Manual integration tests passing
- ✅ Import resolution verified
- ✅ Performance acceptable
- 📝 Detailed testing results
- ➡️ Ready for Phase 4 cleanup

## Update docs/TROUBLESHOOTING.md
- Add Phase 3 testing issues and solutions
- Manual testing procedures
- Performance debugging tips
- Agent integration problems

## Update docs/DEVELOPMENT.md
- Add manual testing guidelines
- Document testing without automated tests
- Smoke test procedures
```

### **Phase 4: Cleanup & Fix Tests**
**Duration**: 1 day  
**Goal**: Remove old tools, fix tests, optimize performance

#### Step 4.1: Remove Old Tool Classes
- Delete `src/tools/atomic_schema_tools.py`
- Delete `src/tools/composite_schema_tools.py`
- Delete `src/tools/schema_tools.py`
- Clean up imports throughout codebase

#### Step 4.2: Add Optional Dependencies
```python
# Update venv with new optional dependencies
# Activate environment: source venv/bin/activate (Linux/Mac) or venv\Scripts\activate (Windows)
# Add to requirements.txt or install directly:

pip install pandas        # For complex data analysis operations
pip install tabulate      # For better table formatting

# Remove LangChain dependencies from venv:
pip uninstall langchain langchain_community langchain_experimental

# Core dependencies remain:
# - requests (for Ollama API)
# - duckdb (for metadata store)  
# - pytest (for testing)

# Use pandas when available, fallback to current logic
class RelationshipAnalyzer:
    def find_similar_schemas(self) -> List[Dict]:
        if HAS_PANDAS:
            return self._find_similar_schemas_pandas()
        else:
            return self._find_similar_schemas_basic()
```

#### Step 4.3: Fix Tests & Documentation
```python
# Now that code is working, fix the test suite
# 1. Update test_end_to_end.py to work with new tools
# 2. Fix failing tests one by one
# 3. Add new tests for edge cases if needed
# 4. Ensure: python scripts/run_tests.py passes

# Update EXPECTED_RESPONSES to work with new tools:
EXPECTED_RESPONSES = {
    "what files do we have": {           # → get_files()
        "should_contain": ["scanned files", "customers.csv", "orders.csv"],
        "should_not_contain": ["error", "failed"],
        "min_length": 100,
    },
    "show me the customers schema": {    # → get_schemas("customers")  
        "should_contain": ["customers.csv", "customer_id", "email"],
        "should_not_contain": ["error", "not found"],
        "min_length": 150,
    },
    # ... update all test expectations
}
```

#### Step 4.4: **📚 Complete Migration Documentation**
```markdown
# Final documentation updates and migration completion:

## docs/vibe-collab/phase4_complete.md
- ✅ All old tools removed
- ✅ Dependencies cleaned up
- ✅ Test suite fixed and passing
- ✅ Performance verified
- 📝 Final migration summary
- 🎉 Migration completed successfully

## docs/vibe-collab/migration_complete.md
- Complete migration summary
- Before/after architecture comparison
- Performance improvements achieved
- Lessons learned
- Future extension guidelines

## Update all core documentation:
### docs/USAGE.md
- Remove migration notes
- Update with new tool capabilities
- Add examples using new tools
- Update troubleshooting section

### docs/ARCHITECTURE.md
- Complete new architecture documentation
- Remove old architecture sections
- Add performance characteristics
- Document extension points

### docs/DEVELOPMENT.md
- Complete development guidelines for new architecture
- How to add new tools (step-by-step)
- Testing procedures
- Code organization standards

### docs/TROUBLESHOOTING.md
- Comprehensive troubleshooting guide
- Common issues and solutions
- Performance optimization tips
- Debug procedures

## Update docs/todo.txt
- Mark migration tasks as complete
- Add any follow-up tasks identified
- Note future enhancement opportunities
```

## 📋 Implementation Priority Order

### **High-Value, Low-Risk (Start Here):**
1. **`get_files()`** ← `list_files()` (simple mapping)
2. **`get_statistics()`** ← `get_database_summary()` (simple extension)
3. **`compare_items()`** ← `compare_two_files()` (parameterize existing logic)

### **Medium Complexity:**
4. **`get_schemas()`** ← `get_file_schema()` (extend to handle multiple files)
5. **`search_metadata()`** ← `search_columns()` + `get_column_data_types()` (merge + parameterize)

### **High Complexity (Do Last):**
6. **`find_relationships()`** ← `find_common_columns()` + new similar schema logic
7. **`detect_inconsistencies()`** ← `detect_type_mismatches()` + new checks
8. **`run_analysis()`** ← completely new escape hatch

## 🔧 Technical Implementation Patterns

### Tool Registration Pattern
```python
# All tools follow this pattern (Native Ollama approach)
class SearchMetadataTool(BaseTool):
    description = "Search across metadata"
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "search_term": {"type": "string", "description": "Term to search for"},
                "search_type": {"type": "string", "enum": ["column", "file", "type"], "default": "column"}
            },
            "required": ["search_term"]
        }
    
    def execute(self, search_term: str, search_type: str = "column") -> str:
        try:
            # Delegate to strategy component
            handler = ColumnSearcher(self.store)
            result = handler.search(search_term)
            formatter = TextFormatter()
            return formatter.format(result)
        except Exception as e:
            logger.error(f"Error in search_metadata: {e}")
            return f"Error: {e}"
```

### Strategy Component Pattern
```python
class ColumnSearcher(BaseSearcher):
    def __init__(self, metadata_store):
        self.store = metadata_store
        
    def search(self, term: str) -> List[Dict]:
        # Extract current search logic from search_columns()
        files = self.store.list_all_files()
        matches = []
        # ... existing logic ...
        return matches
```

### Formatter Pattern
```python
class TableFormatter(BaseFormatter):
    def format_search_results(self, matches: List[Dict], search_term: str) -> str:
        # Extract current formatting logic
        if HAS_TABULATE:
            return tabulate(matches, headers="keys", tablefmt="simple")
        else:
            return self._format_text(matches, search_term)
```

## 📊 Success Metrics

### **Phase 1 Success:**
- ✅ All 8 new tools created and callable
- ✅ No existing functionality broken
- ✅ Strategy components isolated and testable
- ✅ Tool registry auto-generates function calling schemas

### **Phase 2 Success:**
- ✅ Agent uses new tools successfully
- ✅ Single source of truth for tool definitions
- ✅ Function calling schemas auto-generated from @tool decorators
- ✅ Backward compatibility working

### **Phase 3 Success:**
- ✅ All existing test queries pass with new tools
- ✅ Performance equal or better than current (< 100ms per tool call)
- ✅ New tools handle edge cases properly
- ✅ End-to-end tests passing

### **Phase 4 Success:**
- ✅ Codebase simplified (3 files → 1 main + strategy components)
- ✅ Easy to add new tool types (just add @tool function)
- ✅ Optional pandas integration working
- ✅ Documentation updated

## ⚠️ Risk Mitigation

### **Rollback Strategy**
1. **Keep old tools until Phase 4** - Easy rollback if issues arise
2. **Feature flags** - Allow switching between old/new tools during migration
3. **Parallel testing** - Run both old and new tools, compare results

### **Performance Monitoring**
1. **Benchmark current tools** before migration
2. **Monitor tool execution times** during migration
3. **Memory usage tracking** with new strategy components

### **Error Handling**
1. **Graceful degradation** - Fall back to old tools if new ones fail
2. **Comprehensive logging** - Track migration issues
3. **Validation checks** - Ensure output format consistency

## 🔄 Post-Migration Benefits

### **Developer Experience**
- ✅ **Single file to modify** when adding new tools
- ✅ **Auto-generated schemas** - no more dual definitions
- ✅ **Type safety** with tool class structure
- ✅ **Easy testing** - isolated strategy components

### **Extensibility**
- ✅ **Add new search types** by extending searchers
- ✅ **Add new analysis types** by extending analyzers
- ✅ **Add new output formats** by extending formatters
- ✅ **Complex queries** via run_analysis() escape hatch

### **Maintainability**
- ✅ **Reduced code duplication** (9 tools → 8, cleaner structure)
- ✅ **Clear separation of concerns** (search vs analyze vs format)
- ✅ **Optional dependencies** handled gracefully
- ✅ **Future-proof architecture** for data analysis expansion

---

**Next Steps**: Start with Phase 1, implementing the base infrastructure and highest-value, lowest-risk tools first.