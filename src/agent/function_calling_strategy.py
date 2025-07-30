"""Function calling strategy using native Ollama API for TableTalk."""

import json
import logging
import requests
from typing import Dict, List, Optional, Any

try:
    from ..utils.logger import get_logger
    from .query_strategy import QueryProcessingStrategy
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.logger import get_logger
    from agent.query_strategy import QueryProcessingStrategy


class FunctionCallingStrategy(QueryProcessingStrategy):
    """Query processing strategy using native Ollama function calling."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "phi4-mini-fc", schema_tools=None):
        """Initialize with Ollama connection."""
        self.base_url = base_url
        self.model = model
        self.schema_tools = schema_tools
        self.logger = get_logger("tabletalk.function_calling")
        self.api_url = f"{base_url}/api/chat"
        
        # Define our schema analysis tools for function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_file_schema",
                    "description": "Get detailed schema for a SPECIFIC file by name (columns, data types, statistics). Only use when user asks about ONE specific file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_name": {
                                "type": "string",
                                "description": "The exact name of the file to analyze (e.g. 'customers.csv')"
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
                    "description": "List all scanned files with basic statistics",
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
                    "name": "find_columns", 
                    "description": "Find all files that contain a column with a specific name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column_name": {
                                "type": "string",
                                "description": "The name of the column to search for"
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
                    "description": "Compare schemas across ALL files and detect columns with same name but different data types. Use this to compare schemas between files or find inconsistencies.",
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
                    "description": "Find columns that appear in multiple files",
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
                    "name": "database_summary", 
                    "description": "Get overall database statistics (total files, columns, summary)",
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
                    "name": "detect_semantic_type_issues",
                    "description": "Detect columns with incorrect data types based on naming patterns",
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
                    "name": "detect_column_name_variations",
                    "description": "Detect columns that represent same field but have different naming conventions", 
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    def parse_query(self, query: str, available_files: List[str] = None) -> Dict[str, Any]:
        """Parse user query and identify intent and steps using function calling.
        
        Returns:
            Dictionary with success/error status and parsed query
        """
        try:
            self.logger.info(f"Parsing query with function calling: {query[:100]}...")
            
            # Get available files context
            files_context = ""
            if available_files:
                files_context = f"Available files: {', '.join(available_files)}"
            
            # Create payload for Ollama API
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are a data exploration assistant. {files_context}"
                    },
                    {
                        "role": "user", 
                        "content": query
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 1.0
                },
                "tools": self.tools
            }
            
            # Make API call to Ollama
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            self.logger.debug(f"Ollama response: {result}")
            
            # Extract tool calls
            if "message" in result and "tool_calls" in result["message"]:
                tool_calls = result["message"]["tool_calls"]
                self.logger.info(f"Found {len(tool_calls)} tool calls")
                if tool_calls:
                    # Use the first tool call
                    tool_call = tool_calls[0]
                    function_info = tool_call["function"]
                    self.logger.info(f"Using function: {function_info['name']}")
                    
                    # Parse arguments if they exist
                    arguments = function_info.get("arguments", {})
                    if isinstance(arguments, str):
                        try:
                            import json
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            self.logger.warning(f"Failed to parse arguments: {arguments}")
                            arguments = {}
                    
                    self.logger.info(f"Function arguments: {arguments}")
                    
                    # Validate the function call makes sense
                    function_name = function_info['name']
                    if function_name == "get_file_schema" and not arguments.get("file_name"):
                        self.logger.warning("get_file_schema called without file_name, using fallback")
                        fallback_result = self._default_fallback(query)
                        return {
                            "success": True,
                            "parsed_query": fallback_result
                        }
                    
                    parsed_query = {
                        "intent": f"Using {function_info['name']} to answer query",
                        "steps": [{
                            "tool": function_info["name"],
                            "params": arguments,
                            "desc": f"Execute {function_info['name']}"
                        }],
                        "insights": [f"Function calling selected: {function_info['name']}"],
                        "strategy": "function_calling",
                        "llm_mode": True
                    }
                    
                    return {
                        "success": True,
                        "parsed_query": parsed_query
                    }
            else:
                self.logger.warning("No tool_calls found in Ollama response")
                if "message" in result:
                    message = result["message"]
                    self.logger.debug(f"Message content: {message.get('content', 'No content')}")
                    self.logger.debug(f"Message keys: {list(message.keys())}")
            
            # If no tool calls, fall back
            self.logger.warning("No tool calls in response, falling back")
            fallback_result = self._default_fallback(query)
            return {
                "success": True,
                "parsed_query": fallback_result
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing query: {e}")
            return {
                "success": False,
                "error": f"Failed to parse query: {str(e)}"
            }
            
        except Exception as e:
            self.logger.error(f"Function calling failed: {str(e)}")
            return self._default_fallback(query)

    def execute_plan(self, plan: Dict[str, Any], schema_tools=None) -> Dict[str, Any]:
        """Execute the plan using schema tools.
        
        Returns:
            Dictionary with success/error status and results
        """
        try:
            # Use passed schema_tools or fallback to instance variable
            tools = schema_tools or self.schema_tools
            if not tools:
                return {
                    "success": False,
                    "error": "No schema tools available"
                }
            
            steps = plan.get("steps", [])
            if not steps:
                result = tools.list_all_files()
                return {
                    "success": True,
                    "result": result
                }
            
            step = steps[0]
            tool_name = step.get("tool", "list_files")
            params = step.get("params", {})
            
            # Execute the appropriate tool
            self.logger.debug(f"Executing tool: {tool_name} with params: {params}")
            
            if tool_name == "get_file_schema":
                result = tools.get_file_schema(params.get("file_name", ""))
            elif tool_name == "list_files":
                result = tools.list_all_files()
            elif tool_name == "find_columns":
                result = tools.find_columns_with_name(params.get("column_name", ""))
            elif tool_name == "detect_type_mismatches":
                result = tools.detect_type_mismatches()
            elif tool_name == "find_common_columns":
                result = tools.find_common_columns()
            elif tool_name == "database_summary":
                result = tools.get_database_summary()
            elif tool_name == "detect_semantic_type_issues":
                result = tools.detect_semantic_type_issues()
            elif tool_name == "detect_column_name_variations":
                result = tools.detect_column_name_variations()
            else:
                self.logger.warning(f"Unknown tool: {tool_name}, defaulting to list_files")
                result = tools.list_all_files()
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Error executing plan: {e}")
            return {
                "success": False,
                "error": f"Error executing plan: {str(e)}"
            }

    def synthesize_response(self, query: str, plan: Dict[str, Any], results: str) -> Dict[str, Any]:
        """Simple pass-through since schema tools already format responses.
        
        Returns:
            Dictionary with success status and response
        """
        try:
            return {
                "success": True,
                "response": results
            }
        except Exception as e:
            self.logger.error(f"Error synthesizing response: {e}")
            return {
                "success": False,
                "error": f"Error synthesizing response: {str(e)}"
            }

    def get_help_text(self) -> str:
        """Get help text for function calling strategy."""
        return """
TableTalk - Advanced Function Calling Mode

Commands:
  /scan <directory>  - Scan files for schema information
  /help              - Show this help
  /exit              - Exit TableTalk

Example Queries:
  • "Show me the schema of orders.csv"
  • "What files do we have?"
  • "Which files have a user_id column?"
  • "Find data type inconsistencies"
  • "What columns are common across files?"
  • "Give me a database summary"
  
Advanced Features:
  • Native function calling for precise tool selection
  • Optimal parameter extraction
  • Reliable query understanding

Tips: Ask complex questions - the function calling will handle them intelligently!
        """.strip()

    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about this strategy."""
        return {
            "name": "Function Calling Strategy",
            "type": "function_calling",
            "model": self.model,
            "base_url": self.base_url,
            "capabilities": ["native_function_calling", "parameter_extraction", "tool_selection"],
            "reliability": "high",
            "performance": "optimal"
        }

    def _check_ollama(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _default_fallback(self, query: str) -> Dict[str, Any]:
        """Simple pattern-based fallback when function calling fails."""
        query_lower = query.lower()
        
        if "file" in query_lower and ("list" in query_lower or "have" in query_lower):
            tool, params = "list_files", {}
        elif "compare" in query_lower and "schema" in query_lower:
            # "compare schemas across files" should detect type mismatches
            tool, params = "detect_type_mismatches", {}
        elif "schema" in query_lower:
            tool, params = "get_file_schema", {}
            # Try to extract filename
            for word in query.split():
                if word.endswith(('.csv', '.parquet')):
                    params["file_name"] = word
                    break
        elif "type" in query_lower and "mismatch" in query_lower:
            tool, params = "detect_type_mismatches", {}
        elif "common" in query_lower and "column" in query_lower:
            tool, params = "find_common_columns", {}
        elif "summary" in query_lower or "overview" in query_lower:
            tool, params = "database_summary", {}
        else:
            tool, params = "list_files", {}
        
        self.logger.info(f"Fallback selected tool: {tool} with params: {params}")
        
        return {
            "intent": f"Fallback to {tool}",
            "steps": [{"tool": tool, "params": params, "desc": f"Execute {tool}"}],
            "insights": ["Pattern-based fallback (function calling unavailable)"],
            "strategy": "function_calling_fallback",
            "fallback": True
        }
