"""SchemaAgent - Modern agent using SQLAlchemy + Great Expectations."""

import json
import logging
import requests
from typing import Dict, List, Optional, Any
from enum import Enum

from src.utils.logger import get_logger
from src.analysis.schema_analyzer import SchemaAnalyzer, create_schema_analyzer


class ProcessingMode(Enum):
    """Processing modes for SchemaAgent."""
    FUNCTION_CALLING = "function_calling"
    STRUCTURED_OUTPUT = "structured_output"


class SchemaAgent:
    """Modern schema agent using SQLAlchemy + Great Expectations.
    
    Provides comprehensive schema analysis and data quality assessment
    using mature libraries instead of custom implementations.
    """
    
    def __init__(self, database_path: str, model_name: str = "phi3", base_url: str = "http://localhost:11434"):
        """Initialize SchemaAgent with auto-capability detection."""
        self.database_path = database_path
        self.model_name = model_name
        self.base_url = base_url
        self.logger = get_logger("tabletalk.schema_agent")
        
        # Initialize the schema analyzer
        self.analyzer = create_schema_analyzer(database_path)
        if not self.analyzer:
            raise RuntimeError(f"Failed to create schema analyzer for: {database_path}")
        
        # Auto-detect capabilities once at startup
        self.supports_function_calling = self._detect_function_calling()
        self.structured_llm = self._init_structured_llm() if not self.supports_function_calling else None
        
        # Determine processing mode
        if self.supports_function_calling:
            self.mode = ProcessingMode.FUNCTION_CALLING
        elif self.structured_llm:
            self.mode = ProcessingMode.STRUCTURED_OUTPUT
        else:
            raise RuntimeError("No compatible model found. Please ensure you have phi4-mini-fc or a compatible model.")
            
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
            else:  # ProcessingMode.STRUCTURED_OUTPUT
                result = self._process_with_structured_output(user_query)
            
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
                return f"I'm having trouble connecting to the language model. Please try again."
                
        except Exception as e:
            self.logger.error(f"Function calling failed: {e}")
            return f"I'm having trouble with function calling. Please try rephrasing your question."
    
    def _process_with_structured_output(self, query: str) -> str:
        """Process query using LangChain structured output."""
        self.logger.debug("Starting structured output processing")
        
        try:
            prompt = f"""Analyze this query about data schemas and respond with JSON:

Query: {query}

Available tools:
- get_file_schema: Get detailed schema for a specific file (requires file_name)
- list_files: List all available files
- search_columns: Search for columns containing a term (requires search_term)
- get_column_data_types: Get data types for a column across files (requires column_name)
- get_database_summary: Get overall database statistics
- detect_type_mismatches: Find columns with inconsistent types across files
- find_common_columns: Find columns that appear in multiple files
- compare_two_files: Compare schemas between two files (requires file1, file2)
- analyze_data_quality: Comprehensive data quality analysis report

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
                return f"I'm having trouble parsing the model response. Please try rephrasing your question."
                
        except Exception as e:
            self.logger.warning(f"Structured output failed: {e}")
            return f"I'm having trouble with structured output. Please try rephrasing your question."
    
    def _get_function_calling_tools(self) -> List[Dict]:
        """Get tool definitions for function calling from the schema analyzer."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List all available tables/files in the database",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_file_schema",
                    "description": "Get detailed schema information for a specific table/file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_name": {
                                "type": "string",
                                "description": "Name of the table/file to get schema for"
                            }
                        },
                        "required": ["file_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_columns",
                    "description": "Search for columns containing a specific term across all tables",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "Term to search for in column names"
                            }
                        },
                        "required": ["search_term"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_column_data_types",
                    "description": "Get data types for a specific column across all tables",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column_name": {
                                "type": "string",
                                "description": "Name of the column to analyze"
                            }
                        },
                        "required": ["column_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_database_summary",
                    "description": "Get comprehensive database summary with statistics",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_type_mismatches",
                    "description": "Find columns with inconsistent types across tables",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_common_columns",
                    "description": "Find columns that appear in multiple tables",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compare_two_files",
                    "description": "Compare schemas between two specific tables",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file1": {
                                "type": "string",
                                "description": "Name of the first table to compare"
                            },
                            "file2": {
                                "type": "string",
                                "description": "Name of the second table to compare"
                            }
                        },
                        "required": ["file1", "file2"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_data_quality",
                    "description": "Perform comprehensive data quality analysis across all tables",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
    
    def _execute_function_calls(self, response_data: dict, original_query: str) -> str:
        """Execute function calls using the schema analyzer."""
        try:
            message = response_data.get("message", {})
            tool_calls = message.get("tool_calls", [])
            content = message.get("content", "")
            
            # Handle case where LLM returns JSON in content instead of proper tool_calls
            if not tool_calls and content:
                # Try to parse JSON from content
                try:
                    import json
                    import re
                    
                    # Extract JSON from markdown code blocks if present
                    json_match = re.search(r'```json\s*(\[.*?\])\s*```', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        json_str = content.strip()
                    
                    # Parse the JSON
                    parsed_json = json.loads(json_str)
                    
                    # Convert the parsed JSON to tool_calls format
                    if isinstance(parsed_json, list) and len(parsed_json) > 0:
                        synthetic_tool_calls = []
                        for item in parsed_json:
                            if isinstance(item, dict):
                                # Handle different JSON formats
                                function_name = None
                                arguments = {}
                                
                                # Check for various formats
                                if "functools invasiveMarker" in item:
                                    function_name = item["functools invasiveMarker"]
                                    arguments = item.get("arguments", {})
                                elif "function" in item:
                                    function_name = item["function"]
                                    arguments = item.get("arguments", {})
                                elif "tool" in item:
                                    function_name = item["tool"]
                                    arguments = item.get("parameters", {})
                                
                                if function_name:
                                    synthetic_tool_calls.append({
                                        "function": {
                                            "name": function_name,
                                            "arguments": arguments
                                        }
                                    })
                        
                        if synthetic_tool_calls:
                            tool_calls = synthetic_tool_calls
                            self.logger.info(f"Converted content JSON to {len(tool_calls)} function calls")
                
                except (json.JSONDecodeError, KeyError, AttributeError) as e:
                    self.logger.warning(f"Failed to parse JSON from content: {e}")
            
            if not tool_calls:
                # No function calls, return direct response
                self.logger.debug(f"LLM chose not to call any functions. Direct response: {content[:100]}...")
                return content
            
            self.logger.info(f"LLM decided to call {len(tool_calls)} functions:")
            for i, tool_call in enumerate(tool_calls):
                function = tool_call.get("function", {})
                function_name = function.get("name")
                arguments = function.get("arguments", {})
                self.logger.info(f"  Function {i+1}: {function_name}({arguments})")
            
            self.logger.debug(f"Executing {len(tool_calls)} function calls")
            results = []
            
            for i, tool_call in enumerate(tool_calls):
                function = tool_call.get("function", {})
                function_name = function.get("name")
                arguments = function.get("arguments", {})
                
                self.logger.debug(f"Function call {i+1}: {function_name} with args: {arguments}")
                
                try:
                    # Execute the function using the schema analyzer
                    result = self._call_analyzer_method(function_name, arguments)
                    self.logger.debug(f"Function {function_name} result length: {len(result)} characters")
                    results.append(result)
                    
                except Exception as e:
                    error_msg = f"Function execution failed: {str(e)}"
                    self.logger.error(f"Function execution failed: {str(e)}")
                    results.append(error_msg)
            
            combined_result = "\n\n".join(results)
            self.logger.debug(f"Combined function call results length: {len(combined_result)} characters")
            return combined_result
            
        except Exception as e:
            self.logger.error(f"Function execution failed: {e}")
            return f"Error executing functions: {e}"
    
    def _execute_structured_plan(self, plan: dict, original_query: str) -> str:
        """Execute structured plan using the schema analyzer."""
        try:
            tool_name = plan.get("tool")
            parameters = plan.get("parameters", {})
            explanation = plan.get("explanation", "")
            
            self.logger.debug(f"Executing structured plan - Tool: {tool_name}, Params: {parameters}, Explanation: {explanation}")
            
            result = self._call_analyzer_method(tool_name, parameters)
            self.logger.debug(f"Structured plan execution result length: {len(result)} characters")
            return result
                
        except Exception as e:
            self.logger.error(f"Structured plan execution failed: {e}")
            return f"Error executing plan: {e}"
    
    def _call_analyzer_method(self, function_name: str, arguments: dict) -> str:
        """Call the appropriate method on the schema analyzer."""
        if function_name == "list_files":
            return self.analyzer.list_files()
        elif function_name == "get_file_schema":
            return self.analyzer.get_file_schema(arguments.get("file_name", ""))
        elif function_name == "search_columns":
            return self.analyzer.search_columns(arguments.get("search_term", ""))
        elif function_name == "get_column_data_types":
            return self.analyzer.get_column_data_types(arguments.get("column_name", ""))
        elif function_name == "get_database_summary":
            return self.analyzer.get_database_summary()
        elif function_name == "detect_type_mismatches":
            return self.analyzer.detect_type_mismatches()
        elif function_name == "find_common_columns":
            return self.analyzer.find_common_columns()
        elif function_name == "compare_two_files":
            return self.analyzer.compare_two_files(
                arguments.get("file1", ""), arguments.get("file2", "")
            )
        elif function_name == "analyze_data_quality":
            return self.analyzer.analyze_data_quality()
        else:
            return f"Unknown function: {function_name}"
    
    def check_llm_availability(self) -> bool:
        """Check if LLM is available."""
        return self.structured_llm is not None or self.supports_function_calling
    
    def get_status(self) -> dict:
        """Get agent status information."""
        if self.mode == ProcessingMode.FUNCTION_CALLING:
            capabilities = ["native_function_calling", "parameter_extraction", "optimal_reliability"]
        else:  # ProcessingMode.STRUCTURED_OUTPUT
            capabilities = ["structured_prompting", "json_parsing"]
        
        # Add library-specific capabilities
        analyzer_status = self.analyzer.get_status()
        capabilities.extend(analyzer_status.get('capabilities', []))
        
        return {
            'agent_type': 'SchemaAgent',
            'mode': self.mode.value,
            'model_name': self.model_name,
            'base_url': self.base_url,
            'llm_available': self.structured_llm is not None, 
            'function_calling': self.supports_function_calling,
            'capabilities': capabilities,
            'analyzer_status': analyzer_status
        }
    
    def close(self):
        """Clean up resources."""
        if self.analyzer:
            self.analyzer.close()
        self.logger.debug("SchemaAgent closed")
