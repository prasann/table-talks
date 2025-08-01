# 🛠️ TableTalk Development Guide

**Last Updated**: August 1, 2025  
**Version**: 2.0 (Unified Tool Architecture)

## 🚀 Development Setup

### **Environment Setup**
```bash
# 1. Activate virtual environment
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Install core dependencies
pip install -r requirements.txt

# 3. Install optional dependencies (recommended)
pip install pandas tabulate

# 4. Verify installation
python -c "from src.tools.tool_registry import ToolRegistry; print('✅ Setup complete')"
```

### **Project Structure**
```
src/
├── tools/                    # Unified tool architecture
│   ├── core/                # Strategy pattern components
│   │   ├── base_components.py    # Abstract base classes
│   │   ├── searchers.py         # Search strategies
│   │   ├── analyzers.py         # Analysis strategies
│   │   └── formatters.py        # Output formatters
│   ├── unified_tools.py     # 8 core tool classes
│   ├── tool_registry.py     # Central tool management
│   └── __init__.py          # Package exports
├── agent/
│   └── schema_agent.py      # Function calling agent
├── metadata/
│   ├── metadata_store.py    # DuckDB interface
│   └── schema_extractor.py  # Schema extraction
└── utils/
    └── logger.py            # Logging utilities
```

## 🔧 Adding New Tools

### **Step 1: Create Tool Class**
```python
# src/tools/unified_tools.py

class YourNewTool(BaseTool):
    """Tool for [describe functionality]."""
    
    description = "Clear description for LLM to understand when to use this tool"
    
    def get_parameters_schema(self) -> Dict:
        """Define Ollama function calling schema."""
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Description of parameter"
                },
                "param2": {
                    "type": "integer", 
                    "description": "Description with default",
                    "default": 10
                }
            },
            "required": ["param1"]  # Only required parameters
        }
    
    def execute(self, param1: str, param2: int = 10) -> str:
        """Execute the tool with given parameters."""
        try:
            # 1. Use strategy components for complex logic
            searcher = ColumnSearcher(self.store)
            results = searcher.search(param1)
            
            # 2. Process results
            processed = self._process_results(results, param2)
            
            # 3. Format output
            formatter = TextFormatter()
            context = {'format_type': 'custom', 'param2': param2}
            return formatter.format(processed, context)
            
        except Exception as e:
            self.logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            return f"Error: {str(e)}"
    
    def _process_results(self, results: List[Dict], threshold: int) -> List[Dict]:
        """Private helper method for processing."""
        # Your processing logic here
        return results
```

### **Step 2: Register Tool**
```python
# src/tools/tool_registry.py

def _register_tools(self) -> Dict[str, Any]:
    """Register all available tools."""
    tools = {
        # ... existing tools ...
        'your_new_tool': YourNewTool(self.store),  # Add this line
    }
    return tools
```

### **Step 3: Test Tool**
```python
# Manual testing
from src.tools.tool_registry import ToolRegistry
from src.metadata.metadata_store import MetadataStore

store = MetadataStore('database/metadata.duckdb')
registry = ToolRegistry(store)

# Test tool execution
result = registry.execute_tool('your_new_tool', param1="test_value")
print(result)

# Test schema generation
schemas = registry.get_ollama_function_schemas()
new_tool_schema = [s for s in schemas if s['function']['name'] == 'your_new_tool'][0]
print(new_tool_schema)
```

## 🔍 Adding Strategy Components

### **Adding New Searcher**
```python
# src/tools/core/searchers.py

class YourCustomSearcher(BaseSearcher):
    """Custom search strategy for [specific use case]."""
    
    def search(self, search_term: str) -> List[Dict[str, Any]]:
        """Implement your search logic."""
        try:
            # Access metadata store
            files = self.store.list_all_files()
            matches = []
            
            # Your search logic here
            for file_info in files:
                schema = self.store.get_file_schema(file_info['file_name'])
                # Process schema...
                
            return matches
            
        except Exception as e:
            self.logger.error(f"Error in search: {str(e)}")
            raise
```

### **Adding New Analyzer**
```python
# src/tools/core/analyzers.py

class YourCustomAnalyzer(BaseAnalyzer):
    """Custom analysis strategy for [specific analysis]."""
    
    def analyze(self, analysis_type: str, **kwargs) -> List[Dict[str, Any]]:
        """Perform analysis based on type."""
        if analysis_type == "your_analysis":
            return self._your_custom_analysis(**kwargs)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    def _your_custom_analysis(self, **kwargs) -> List[Dict[str, Any]]:
        """Implement your analysis logic."""
        try:
            # Optional: Use pandas for complex operations
            if HAS_PANDAS:
                return self._analysis_with_pandas(**kwargs)
            else:
                return self._analysis_basic(**kwargs)
                
        except Exception as e:
            self.logger.error(f"Error in analysis: {str(e)}")
            raise
```

### **Adding New Formatter**
```python
# src/tools/core/formatters.py

class YourCustomFormatter(BaseFormatter):
    """Custom formatter for [specific output format]."""
    
    def format(self, data: List[Dict[str, Any]], context: Optional[Dict] = None) -> str:
        """Format data for your specific use case."""
        if not data:
            return "No results found."
        
        context = context or {}
        
        # Your formatting logic here
        result = ["Custom Format Results:", ""]
        
        for item in data:
            # Format each item
            result.append(f"• {item}")
        
        return "\n".join(result)
```

## 🧪 Testing Guidelines

### **Manual Testing Workflow**
```bash
# 1. Activate environment
source venv/bin/activate

# 2. Test imports
python -c "from src.tools.tool_registry import ToolRegistry; print('✅ Imports work')"

# 3. Test registry creation
python -c "
from src.tools.tool_registry import ToolRegistry
from src.metadata.metadata_store import MetadataStore
store = MetadataStore('database/metadata.duckdb')
registry = ToolRegistry(store)
print(f'✅ Registry created with {len(registry.tools)} tools')
"

# 4. Test specific tool
python -c "
from src.tools.tool_registry import ToolRegistry
from src.metadata.metadata_store import MetadataStore
store = MetadataStore('database/metadata.duckdb')
registry = ToolRegistry(store)
result = registry.execute_tool('get_files')
print('✅ Tool execution result:')
print(result[:200] + '...' if len(result) > 200 else result)
"
```

### **Testing Strategy Components**
```python
# Test searcher independently
from src.tools.core.searchers import ColumnSearcher
from src.metadata.metadata_store import MetadataStore

store = MetadataStore('database/metadata.duckdb')
searcher = ColumnSearcher(store)
results = searcher.search("customer")
print(f"Found {len(results)} matches")

# Test analyzer independently  
from src.tools.core.analyzers import RelationshipAnalyzer

analyzer = RelationshipAnalyzer(store)
relationships = analyzer.analyze("common_columns", threshold=2)
print(f"Found {len(relationships)} common columns")

# Test formatter independently
from src.tools.core.formatters import TextFormatter

formatter = TextFormatter()
formatted = formatter.format(results, {'format_type': 'search_results', 'search_term': 'customer'})
print(formatted)
```

### **Function Calling Schema Validation**
```python
# Validate all schemas are well-formed
from src.tools.tool_registry import ToolRegistry
from src.metadata.metadata_store import MetadataStore
import json

store = MetadataStore('database/metadata.duckdb')
registry = ToolRegistry(store)
schemas = registry.get_ollama_function_schemas()

for schema in schemas:
    # Validate schema structure
    assert 'type' in schema
    assert 'function' in schema
    assert 'name' in schema['function']
    assert 'description' in schema['function']
    assert 'parameters' in schema['function']
    
    # Validate parameters schema
    params = schema['function']['parameters']
    assert 'type' in params
    assert 'properties' in params
    
    print(f"✅ {schema['function']['name']} schema valid")
```

## 🔧 Debugging Guidelines

### **Common Issues & Solutions**

#### **Import Errors**
```python
# Problem: ModuleNotFoundError for core components
# Solution: Check relative import paths
from ...utils.logger import get_logger  # 3 levels up from core/
from ..utils.logger import get_logger    # 2 levels up from tools/
```

#### **Tool Registration Issues**
```python
# Problem: Tool not appearing in registry
# Solution: Check _register_tools() method

def _register_tools(self) -> Dict[str, Any]:
    tools = {
        'existing_tool': ExistingTool(self.store),
        'new_tool': NewTool(self.store),  # Make sure this line exists
    }
    return tools
```

#### **Function Schema Issues**
```python
# Problem: Ollama function calling fails
# Solution: Validate schema format

def get_parameters_schema(self) -> Dict:
    return {
        "type": "object",                    # Required
        "properties": {                      # Required
            "param": {
                "type": "string",            # Required: string, integer, boolean, array, object
                "description": "Clear desc", # Required: helps LLM understand
                "default": "value"           # Optional: for non-required params
            }
        },
        "required": ["param"]                # Required: list of required parameter names
    }
```

#### **Strategy Component Issues**
```python
# Problem: Strategy component not working
# Solution: Check base class implementation

class YourSearcher(BaseSearcher):  # Must inherit from base class
    def __init__(self, metadata_store):
        super().__init__(metadata_store)  # Call parent constructor
        
    def search(self, term: str) -> List[Dict[str, Any]]:  # Must implement abstract method
        # Implementation here
        pass
```

### **Logging & Debugging**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check tool registry logs
from src.tools.tool_registry import ToolRegistry
from src.metadata.metadata_store import MetadataStore

store = MetadataStore('database/metadata.duckdb')
registry = ToolRegistry(store)  # Check logs for registration issues

# Check individual tool execution
result = registry.execute_tool('problem_tool', param="value")  # Check logs for execution issues
```

## 📊 Performance Optimization

### **Strategy Component Optimization**

#### **Using Pandas for Large Data Operations**
```python
# Instead of nested loops
def _find_common_columns_basic(self, threshold: int) -> List[Dict]:
    # Slow for large datasets
    for file_info in files:
        for col in schema:
            # ... nested processing

# Use pandas for efficiency  
def _find_common_columns_pandas(self, threshold: int) -> List[Dict]:
    # Fast even for large datasets
    df = pd.DataFrame(all_metadata)
    result = df.groupby('column_name').agg({
        'file_name': lambda x: list(x),
        'data_type': lambda x: list(set(x))
    }).reset_index()
    return result.to_dict('records')
```

#### **Caching Expensive Operations**
```python
class OptimizedSearcher(BaseSearcher):
    def __init__(self, metadata_store):
        super().__init__(metadata_store)
        self._cache = {}
    
    def search(self, term: str) -> List[Dict]:
        # Cache results for repeated searches
        if term in self._cache:
            return self._cache[term]
        
        result = self._perform_search(term)
        self._cache[term] = result
        return result
```

### **Memory Usage Optimization**
```python
# Use generators for large datasets
def _get_all_metadata_generator(self):
    """Generator to avoid loading all data into memory."""
    files = self.store.list_all_files()
    for file_info in files:
        schema = self.store.get_file_schema(file_info['file_name'])
        if schema:
            for col in schema:
                yield {
                    'file_name': file_info['file_name'],
                    'column_name': col['column_name'],
                    'data_type': col['data_type']
                }
```

## 🔄 Migration Assistance

### **Phase 2 Preparation**
```python
# Current agent will be updated to use ToolRegistry
# Prepare by testing agent integration

from src.agent.schema_agent import SchemaAgent
from src.metadata.metadata_store import MetadataStore

store = MetadataStore('database/metadata.duckdb')

# Test current agent (should still work)
agent = SchemaAgent(store, "phi4-mini-fc")
response = agent.query("what files do we have")
print("Current agent response:", response)
```

### **Legacy Tool Comparison**
```python
# Compare outputs between old and new tools
from src.tools import AtomicSchemaTools, ToolRegistry
from src.metadata.metadata_store import MetadataStore

store = MetadataStore('database/metadata.duckdb')

# Old way
old_tools = AtomicSchemaTools(store)
old_result = old_tools.search_columns("customer")

# New way  
registry = ToolRegistry(store)
new_result = registry.execute_tool('search_metadata', search_term="customer", search_type="column")

print("Old result:", old_result[:100] + "...")
print("New result:", new_result[:100] + "...")
```

---

## 📝 Development Best Practices

1. **Follow Strategy Pattern**: Use existing searchers/analyzers when possible
2. **Error Handling**: Always wrap tool execution in try/catch
3. **Logging**: Use self.logger for debugging and monitoring
4. **Testing**: Test components individually before integration
5. **Documentation**: Update function descriptions for LLM clarity
6. **Performance**: Consider pandas for complex data operations
7. **Backward Compatibility**: Test that existing functionality still works
8. **Schema Validation**: Ensure function calling schemas are well-formed

This guide should help you extend and maintain the TableTalk unified tool architecture effectively!
