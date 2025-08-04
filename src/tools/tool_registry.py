"""Tool registry for organizing and managing available tools."""

import logging
from typing import Dict, Any, List

# Internal imports
from .basic_tools import GetFilesTool, GetSchemasTool, GetStatisticsTool
from .search_tools import SearchMetadataTool
from .comparison_tools import FindRelationshipsTool, DetectInconsistenciesTool
from .utility_tools import CompareItemsTool, RunAnalysisTool
from ..utils.logger import get_logger


class ToolRegistry:
    """Registry for unified tools - generates schemas for Ollama function calling."""
    
    def __init__(self, metadata_store):
        self.store = metadata_store
        self.logger = get_logger("tabletalk.tool_registry")
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Any]:
        """Register all available tools."""
        tools = {
            'get_files': GetFilesTool(self.store),
            'get_schemas': GetSchemasTool(self.store),
            'search_metadata': SearchMetadataTool(self.store),
            'get_statistics': GetStatisticsTool(self.store),
            'find_relationships': FindRelationshipsTool(self.store),
            'detect_inconsistencies': DetectInconsistenciesTool(self.store),
            'compare_items': CompareItemsTool(self.store),
            'run_analysis': RunAnalysisTool(self.store)
        }
        
        self.logger.info(f"Registered {len(tools)} tools: {list(tools.keys())}")
        return tools
    
    def get_ollama_function_schemas(self) -> List[Dict]:
        """Generate Ollama function calling schemas."""
        schemas = []
        
        for name, tool in self.tools.items():
            try:
                schema = {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": tool.description,
                        "parameters": tool.get_parameters_schema()
                    }
                }
                schemas.append(schema)
                
            except Exception as e:
                self.logger.error(f"Error generating schema for tool {name}: {str(e)}")
        
        self.logger.info(f"Generated {len(schemas)} function calling schemas")
        return schemas
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name."""
        if tool_name not in self.tools:
            available_tools = ", ".join(self.tools.keys())
            return f"Tool '{tool_name}' not found. Available tools: {available_tools}"
        
        try:
            result = self.tools[tool_name].execute(**kwargs)
            self.logger.debug(f"Tool {tool_name} executed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def get_tool_names(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions for all tools."""
        return {name: tool.description for name, tool in self.tools.items()}
