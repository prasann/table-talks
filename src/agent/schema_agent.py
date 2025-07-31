"""SchemaAgent - Unified agent for DuckDB schema queries with auto-capability detection."""

import json
import logging
import requests
from typing import Dict, List, Optional, Any
from enum import Enum
import os
import sys

# Ensure src is in Python path for consistent imports
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Always use absolute imports from src
from utils.logger import get_logger
from tools.schema_tools import SchemaTools


class ProcessingMode(Enum):
    """Processing modes for SchemaAgent."""
    FUNCTION_CALLING = "function_calling"
    STRUCTURED_OUTPUT = "structured_output"
    PATTERN_MATCHING = "pattern_matching"


class SchemaAgent:
    """Unified agent for processing natural language queries about data schemas.
    
    Auto-detects model capabilities and uses the best approach:
    - Function calling for phi4-mini-fc models
    - Structured output for phi3/phi4 models  
    - Pattern matching fallback
    """
    
    def __init__(self, schema_tools: SchemaTools, model_name: str = "phi3", base_url: str = "http://localhost:11434"):
        """Initialize SchemaAgent with auto-capability detection."""
        self.schema_tools = schema_tools
        self.model_name = model_name
        self.base_url = base_url
        self.logger = get_logger("tabletalk.schema_agent")
        
        # Auto-detect capabilities once at startup
        self.supports_function_calling = self._detect_function_calling()
        self.structured_llm = self._init_structured_llm() if not self.supports_function_calling else None
        
        # Determine processing mode
        if self.supports_function_calling:
            self.mode = ProcessingMode.FUNCTION_CALLING
        elif self.structured_llm:
            self.mode = ProcessingMode.STRUCTURED_OUTPUT
        else:
            self.mode = ProcessingMode.PATTERN_MATCHING
            
        self.logger.info(f"SchemaAgent initialized with {self.mode.value} mode for model: {model_name}")
    
    def _detect_function_calling(self) -> bool:
        """Detect if model supports native function calling."""
        function_calling_indicators = ["phi4-mini-fc", "phi4-mini:fc", "phi4:fc"]
        
        # Exact match for known function calling models
        if self.model_name in function_calling_indicators:
            return True
            
        # Pattern-based detection
        if "phi4" in self.model_name.lower() and ("fc" in self.model_name.lower() or "function" in self.model_name.lower()):
            return True
            
        return False
    
    def _init_structured_llm(self):
        """Initialize LLM for structured output (only when needed)."""
        try:
            from langchain_ollama import ChatOllama
            
            # Test Ollama availability
            test_response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if test_response.status_code == 200:
                llm = ChatOllama(
                    model=self.model_name,
                    base_url=self.base_url,
                    temperature=0.1
                )
                self.logger.info(f"Structured LLM initialized: {self.model_name}")
                return llm
            else:
                self.logger.warning("Ollama not available")
                return None
                
        except Exception as e:
            self.logger.warning(f"Failed to initialize structured LLM: {e}")
            return None
    
    def query(self, user_query: str) -> str:
        """Process a user query and return a response."""
        self.logger.info(f"Processing query in {self.mode.value} mode: {user_query[:100]}...")
        
        try:
            if self.mode == ProcessingMode.FUNCTION_CALLING:
                result = self._process_with_function_calling(user_query)
            elif self.mode == ProcessingMode.STRUCTURED_OUTPUT:
                result = self._process_with_structured_output(user_query)
            else:  # ProcessingMode.PATTERN_MATCHING
                result = self._process_with_patterns(user_query)
            
            self.logger.debug(f"Query result length: {len(result)} characters")
            return result
            
        except Exception as e:
            self.logger.error(f"Query processing failed: {e}")
            return f"I encountered an error: {e}\n\nPlease try rephrasing your question."
    
    def _process_with_function_calling(self, query: str) -> str:
        """Process query using native Ollama function calling."""
        self.logger.debug("Starting function calling processing")
        tools = self._get_function_calling_tools()
        
        try:
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a data schema analysis assistant. Use the provided functions to analyze database schemas and answer questions about data files, columns, types, and quality issues. Choose the most appropriate function based on the user's question."
                    },
                    {
                        "role": "user", 
                        "content": query
                    }
                ],
                "tools": tools,
                "stream": False
            }
            self.logger.debug(f"Sending function calling request with {len(tools)} tools")
            
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                self.logger.debug(f"Function calling API response: {response_data}")
                
                # Debug: Show what the LLM decided to do
                message = response_data.get("message", {})
                if message.get("tool_calls"):
                    tool_calls = message.get("tool_calls", [])
                    self.logger.debug(f"LLM decided to call {len(tool_calls)} functions:")
                    for i, tool_call in enumerate(tool_calls):
                        func_name = tool_call.get("function", {}).get("name", "unknown")
                        func_args = tool_call.get("function", {}).get("arguments", {})
                        self.logger.debug(f"  Function {i+1}: {func_name}({func_args})")
                else:
                    self.logger.debug(f"LLM chose not to call any functions. Direct response: {message.get('content', 'No content')[:200]}...")
                
                return self._execute_function_calls(response_data, query)
            else:
                self.logger.error(f"Function calling API error: {response.status_code} - {response.text}")
                self.logger.debug("Falling back to pattern matching")
                return self._process_with_patterns(query)  # Fallback
                
        except Exception as e:
            self.logger.error(f"Function calling failed: {e}")
            self.logger.debug("Falling back to pattern matching")
            return self._process_with_patterns(query)  # Fallback
    
    def _process_with_structured_output(self, query: str) -> str:
        """Process query using LangChain structured output."""
        self.logger.debug("Starting structured output processing")
        
        try:
            prompt = f"""Analyze this query about data schemas and respond with JSON:

Query: {query}

Available tools:
- get_file_schema: Get detailed schema for a specific file (requires file_name)
- list_files: List all available files
- find_columns: Find files containing a specific column (requires column_name)  
- detect_type_mismatches: Find columns with inconsistent types across files
- find_common_columns: Find columns that appear in multiple files
- database_summary: Get overall database statistics
- detect_semantic_type_issues: Find semantic type inconsistencies
- detect_column_name_variations: Find similar column names with different conventions

Response format:
{{
    "tool": "tool_name", 
    "parameters": {{"param": "value"}},
    "explanation": "why this tool was selected"
}}

If no specific tool fits, respond with {{"tool": "list_files", "parameters": {{}}, "explanation": "general information request"}}"""
            
            self.logger.debug("Sending structured output request to LLM")
            response = self.structured_llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            self.logger.debug(f"LLM response received (length: {len(content)}): {content[:200]}...")
            
            # Extract JSON from response
            try:
                # Try to find JSON in the response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    parsed = json.loads(json_str)
                    self.logger.debug(f"Successfully parsed JSON: {parsed}")
                else:
                    # Fallback parsing
                    parsed = json.loads(content)
                    self.logger.debug(f"Fallback JSON parsing successful: {parsed}")
                    
                return self._execute_structured_plan(parsed, query)
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON parsing failed: {e}, LLM response: {content[:100]}...")
                self.logger.debug("Falling back to pattern matching")
                return self._process_with_patterns(query)
                
        except Exception as e:
            self.logger.warning(f"Structured output failed: {e}")
            self.logger.debug("Falling back to pattern matching")
            return self._process_with_patterns(query)
    
    def _process_with_patterns(self, query: str) -> str:
        """Process query using simple pattern matching (fallback)."""
        self.logger.debug(f"Using pattern matching for query: {query}")
        query_lower = query.lower()
        
        try:
            if any(word in query_lower for word in ["files", "tables", "datasets", "what do we have"]):
                self.logger.debug("Pattern matched: list files")
                return self.schema_tools.list_all_files()
            
            elif "schema" in query_lower:
                self.logger.debug("Pattern matched: get schema")
                # Try to extract filename
                words = query.split()
                for word in words:
                    if ".csv" in word.lower() or ".parquet" in word.lower():
                        self.logger.debug(f"Extracted filename: {word}")
                        return self.schema_tools.get_file_schema(word)
                return "Please specify a filename, e.g., 'schema of customers.csv'"
            
            elif any(word in query_lower for word in ["columns", "column"]):
                self.logger.debug("Pattern matched: find columns")
                # Try to extract column name
                words = query.split()
                for word in words:
                    if len(word) > 2 and word not in ["columns", "column", "have", "with", "find"]:
                        self.logger.debug(f"Extracted column name: {word}")
                        return self.schema_tools.find_columns_with_name(word)
                return "Please specify a column name to search for"
            
            elif any(word in query_lower for word in ["type", "mismatch", "inconsistent"]):
                self.logger.debug("Pattern matched: detect type mismatches")
                return self.schema_tools.detect_type_mismatches()
            
            elif any(word in query_lower for word in ["common", "shared", "across"]):
                self.logger.debug("Pattern matched: find common columns")
                return self.schema_tools.find_common_columns()
            
            elif any(word in query_lower for word in ["summary", "overview", "statistics"]):
                self.logger.debug("Pattern matched: database summary")
                return self.schema_tools.get_database_summary()
            
            elif any(word in query_lower for word in ["quality", "issues", "problems"]):
                self.logger.debug("Pattern matched: data quality analysis")
                result = []
                result.append("🔍 Data Quality Analysis:")
                result.append(self.schema_tools.detect_type_mismatches())
                result.append(self.schema_tools.detect_semantic_type_issues())
                result.append(self.schema_tools.detect_column_name_variations())
                return "\n\n".join(result)
            
            else:
                self.logger.debug("No pattern matched, returning help")
                return (
                    "I can help you explore your data schemas. Try asking:\n"
                    "• 'What files do we have?'\n"
                    "• 'Show me the schema of customers.csv'\n"
                    "• 'Find columns with customer_id'\n"
                    "• 'Detect type mismatches'\n"
                    "• 'Find data quality issues'"
                )
                
        except Exception as e:
            self.logger.error(f"Pattern matching failed: {e}")
            return f"Error processing query: {e}"
    
    def _get_function_calling_tools(self) -> List[Dict]:
        """Get tool definitions for function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_file_schema",
                    "description": "Get detailed schema information for a specific file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_name": {
                                "type": "string",
                                "description": "Name of the file to analyze (e.g., 'customers.csv')"
                            }
                        },
                        "required": ["file_name"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "list_files",
                    "description": "List all available files in the database - use this when user asks 'what files do we have' or wants to see available files",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_columns",
                    "description": "Find files that contain a specific column name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column_name": {
                                "type": "string", 
                                "description": "Name of the column to search for"
                            }
                        },
                        "required": ["column_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_type_mismatches", 
                    "description": "Find data type discrepancies and inconsistencies across tables - use this for detecting type mismatches, discrepancies, or inconsistent data types between files",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_common_columns",
                    "description": "Find columns that appear in multiple files", 
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "database_summary",
                    "description": "Get overall statistics about the database",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_semantic_type_issues",
                    "description": "Find semantic type problems like numeric data stored as text, dates as strings, etc. - use for data quality analysis",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "detect_column_name_variations",
                    "description": "Find similar column names with different naming conventions",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]
    
    def _execute_function_calls(self, response_data: dict, original_query: str) -> str:
        """Execute function calls and return formatted results."""
        try:
            message = response_data.get("message", {})
            tool_calls = message.get("tool_calls", [])
            
            if not tool_calls:
                # No function calls, return direct response
                content = message.get("content", "No response generated")
                self.logger.debug(f"No function calls made, returning direct response: {content[:100]}...")
                return content
            
            self.logger.debug(f"Executing {len(tool_calls)} function calls")
            results = []
            for i, tool_call in enumerate(tool_calls):
                function = tool_call.get("function", {})
                function_name = function.get("name")
                arguments = function.get("arguments", {})
                
                self.logger.debug(f"Function call {i+1}: {function_name} with args: {arguments}")
                
                # Execute the function
                if function_name == "get_file_schema":
                    result = self.schema_tools.get_file_schema(arguments.get("file_name", ""))
                elif function_name == "list_files":
                    result = self.schema_tools.list_all_files()
                elif function_name == "find_columns":
                    result = self.schema_tools.find_columns_with_name(arguments.get("column_name", ""))
                elif function_name == "detect_type_mismatches":
                    result = self.schema_tools.detect_type_mismatches()
                elif function_name == "find_common_columns":
                    result = self.schema_tools.find_common_columns()
                elif function_name == "database_summary":
                    result = self.schema_tools.get_database_summary()
                elif function_name == "detect_semantic_type_issues":
                    result = self.schema_tools.detect_semantic_type_issues()
                elif function_name == "detect_column_name_variations":
                    result = self.schema_tools.detect_column_name_variations()
                else:
                    result = f"Unknown function: {function_name}"
                
                self.logger.debug(f"Function {function_name} result length: {len(result)} characters")
                results.append(result)
            
            combined_result = "\n\n".join(results)
            self.logger.debug(f"Combined function call results length: {len(combined_result)} characters")
            return combined_result
            
        except Exception as e:
            self.logger.error(f"Function execution failed: {e}")
            return f"Error executing functions: {e}"
    
    def _execute_structured_plan(self, plan: dict, original_query: str) -> str:
        """Execute structured plan and return formatted results."""
        try:
            tool_name = plan.get("tool")
            parameters = plan.get("parameters", {})
            explanation = plan.get("explanation", "")
            
            self.logger.debug(f"Executing structured plan - Tool: {tool_name}, Params: {parameters}, Explanation: {explanation}")
            
            if tool_name == "get_file_schema":
                result = self.schema_tools.get_file_schema(parameters.get("file_name", ""))
            elif tool_name == "list_files":
                result = self.schema_tools.list_all_files()
            elif tool_name == "find_columns":
                result = self.schema_tools.find_columns_with_name(parameters.get("column_name", ""))
            elif tool_name == "detect_type_mismatches":
                result = self.schema_tools.detect_type_mismatches()
            elif tool_name == "find_common_columns":
                result = self.schema_tools.find_common_columns()
            elif tool_name == "database_summary":
                result = self.schema_tools.get_database_summary()
            elif tool_name == "detect_semantic_type_issues":
                result = self.schema_tools.detect_semantic_type_issues()
            elif tool_name == "detect_column_name_variations":
                result = self.schema_tools.detect_column_name_variations()
            else:
                result = f"Unknown tool: {tool_name}"
            
            self.logger.debug(f"Structured plan execution result length: {len(result)} characters")
            return result
                
        except Exception as e:
            self.logger.error(f"Structured plan execution failed: {e}")
            return f"Error executing plan: {e}"
    
    def check_llm_availability(self) -> bool:
        """Check if LLM is available."""
        return self.structured_llm is not None or self.supports_function_calling
    
    def get_status(self) -> dict:
        """Get agent status information."""
        if self.mode == ProcessingMode.FUNCTION_CALLING:
            capabilities = ["native_function_calling", "parameter_extraction", "optimal_reliability"]
        elif self.mode == ProcessingMode.STRUCTURED_OUTPUT:
            capabilities = ["structured_prompting", "json_parsing", "pattern_fallback"]
        else:  # ProcessingMode.PATTERN_MATCHING
            capabilities = ["pattern_matching", "basic_queries"]
        
        return {
            'agent_type': 'SchemaAgent',
            'mode': self.mode.value,
            'model_name': self.model_name,
            'base_url': self.base_url,
            'llm_available': self.structured_llm is not None, 
            'function_calling': self.supports_function_calling,
            'capabilities': capabilities
        }
