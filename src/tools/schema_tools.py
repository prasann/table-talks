"""Unified schema tools - simplified atomic + composite tools with smart LLM orchestration."""

from typing import List, Dict, Any, Optional
from langchain.tools import Tool
from utils.logger import get_logger
from metadata.metadata_store import MetadataStore
from tools.atomic_schema_tools import AtomicSchemaTools
from tools.composite_schema_tools import CompositeSchemaTools


class SchemaTools:
    """Unified schema tools that provide both atomic and composite operations.
    
    This class provides a clean interface for LLM agents to perform schema analysis
    through multi-turn tool calling. The LLM can use atomic tools for simple operations
    and composite tools for known complex patterns.
    """
    
    def __init__(self, metadata_store: MetadataStore):
        """Initialize unified schema tools.
        
        Args:
            metadata_store: MetadataStore instance
        """
        self.store = metadata_store
        self.logger = get_logger("tabletalk.schema_tools")
        
        # Initialize atomic and composite tools
        self.atomic = AtomicSchemaTools(metadata_store)
        self.composite = CompositeSchemaTools(metadata_store, self.atomic)
    
    # ============================================================================
    # LangChain Tool Interface - Provides tools for LLM agents
    # ============================================================================
    
    def get_tools(self) -> List[Tool]:
        """Get Tool objects for use with agents (framework agnostic).
        
        Returns:
            List of Tool objects combining atomic and composite operations
        """
        
        # Atomic tools - granular, single-purpose operations
        atomic_tools = [
            Tool(
                name="list_files",
                description="List all scanned files with basic information (rows, columns, size). Use for: 'what files do we have', 'show me all tables', 'list available data'",
                func=self.atomic.list_files,
            ),
            Tool(
                name="get_file_schema",
                description="Get detailed schema for a specific file (smart fuzzy matching). ALWAYS use for: 'what data types are in customers file', 'describe customers.csv', 'schema of orders file', 'show me columns in users'",
                func=self.atomic.get_file_schema,
            ),
            Tool(
                name="search_columns",
                description="Smart column search with fuzzy matching (handles customer_id/customerId/cust_id variations). ALWAYS use for: 'which files have customer_id', 'which files have customer id', 'find user columns', 'search for price fields'",
                func=self.atomic.search_columns,
            ),
            Tool(
                name="get_column_data_types",
                description="Get all data types for a column name across files (fuzzy matching). Use for: 'what types does customer_id have', 'data types for price column'",
                func=self.atomic.get_column_data_types,
            ),
            Tool(
                name="get_database_summary",
                description="Get overall database statistics (files, columns, sizes). Use for: 'database overview', 'summary of scanned data', 'general statistics'",
                func=self.atomic.get_database_summary,
            ),
        ]
        
        # Composite tools - simple multi-step operations
        composite_tools = [
            Tool(
                name="detect_type_mismatches",
                description="Find ONLY columns with same name but different types across files (not for general schema comparison). Use for: 'type mismatches', 'type inconsistencies', 'data type conflicts'",
                func=self.composite.detect_type_mismatches,
            ),
            Tool(
                name="find_common_columns",
                description="Find columns that appear in multiple files (potential join keys). Use for: 'shared columns', 'common fields', 'join candidates', 'common columns', 'compare schemas across files'",
                func=self.composite.find_common_columns,
            ),
            Tool(
                name="compare_two_files",
                description="Compare schemas between exactly TWO specific named files only. Use ONLY when user mentions specific file names like: 'compare orders.csv and customers.csv', 'differences between orders.csv and users.csv'",
                func=self.composite.compare_two_files,
            ),
            Tool(
                name="analyze_data_quality",
                description="ALWAYS use for 'compare schemas across files'. Comprehensive data quality analysis report including type mismatches AND common columns analysis. Use for: 'compare schemas across files', 'overall schema comparison', 'find data quality issues', 'analyze data quality', 'quality problems', 'data issues'",
                func=self.composite.analyze_data_quality,
            ),
        ]
        
        return atomic_tools + composite_tools

    def get_function_calling_tools(self) -> List[Dict]:
        """Get function calling tool definitions for Ollama function calling.
        
        Returns:
            List of function calling tool definitions
        """
        tools = self.get_tools()
        function_tools = []
        
        for tool in tools:
            # Define parameters for each tool
            parameters = {"type": "object", "properties": {}}
            
            if tool.name == "get_file_schema":
                parameters = {
                    "type": "object",
                    "properties": {
                        "file_name": {
                            "type": "string",
                            "description": "Name of the file to analyze (e.g., 'customers.csv', 'orders', 'users')"
                        }
                    },
                    "required": ["file_name"]
                }
            elif tool.name == "search_columns":
                parameters = {
                    "type": "object", 
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "Column name to search for (e.g., 'customer_id', 'price', 'email')"
                        }
                    },
                    "required": ["search_term"]
                }
            elif tool.name == "get_column_data_types":
                parameters = {
                    "type": "object",
                    "properties": {
                        "column_name": {
                            "type": "string",
                            "description": "Name of the column to get data types for"
                        }
                    },
                    "required": ["column_name"]
                }
            elif tool.name == "compare_two_files":
                parameters = {
                    "type": "object",
                    "properties": {
                        "file1": {
                            "type": "string", 
                            "description": "Name of the first file"
                        },
                        "file2": {
                            "type": "string",
                            "description": "Name of the second file"
                        }
                    },
                    "required": ["file1", "file2"]
                }
            
            function_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": parameters
                }
            })
        
        return function_tools


# ============================================================================
# Factory Function - For easy initialization
# ============================================================================

def create_schema_tools(metadata_store: MetadataStore) -> SchemaTools:
    """Factory function to create SchemaTools instance.
    
    Args:
        metadata_store: MetadataStore instance
        
    Returns:
        Configured SchemaTools instance
    """
    return SchemaTools(metadata_store)
