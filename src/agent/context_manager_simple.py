"""Simplified Context Manager using native Phi-4 function calling."""

import json
import logging
import requests
from typing import Dict, List, Optional, Any

try:
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.logger import get_logger


class SimpleContextManager:
    """Simplified context manager using native Phi-4 function calling."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "phi4-mini:3.8b-fp16"):
        """Initialize with Ollama connection."""
        self.base_url = base_url
        self.model = model
        self.logger = get_logger("tabletalk.context")
        self.api_url = f"{base_url}/api/chat"
        
        # Define our schema analysis tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_file_schema",
                    "description": "Get detailed schema for a specific file (columns, data types, statistics)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_name": {
                                "type": "string",
                                "description": "The name of the file to analyze"
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
                    "description": "Detect columns with same name but different data types across files",
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
        """Parse query using native Phi-4 function calling."""
        try:
            # Check Ollama availability
            if not self._check_ollama():
                return self._default_fallback(query)
                
            # Build context
            files_context = f"Available files: {', '.join(available_files[:10])}" if available_files else "No files scanned yet."
            
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
                if tool_calls:
                    # Use the first tool call
                    tool_call = tool_calls[0]
                    function_info = tool_call["function"]
                    
                    return {
                        "intent": f"Using {function_info['name']} to answer query",
                        "steps": [{
                            "tool": function_info["name"],
                            "params": function_info.get("arguments", {}),
                            "desc": f"Execute {function_info['name']}"
                        }],
                        "insights": [f"Native function calling selected: {function_info['name']}"],
                        "llm_mode": True
                    }
            
            # If no tool calls, fall back
            return self._default_fallback(query)
            
        except Exception as e:
            self.logger.error(f"Function calling failed: {str(e)}")
            return self._default_fallback(query)

    def _check_ollama(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _default_fallback(self, query: str) -> Dict[str, Any]:
        """Simple pattern-based fallback."""
        query_lower = query.lower()
        
        if "file" in query_lower and ("list" in query_lower or "have" in query_lower):
            tool = "list_files"
        elif "schema" in query_lower:
            tool = "get_file_schema"
            # Try to extract filename
            params = {}
            for word in query.split():
                if word.endswith(('.csv', '.parquet')):
                    params["file_name"] = word
                    break
        elif "type" in query_lower and "mismatch" in query_lower:
            tool = "detect_type_mismatches"
        elif "common" in query_lower and "column" in query_lower:
            tool = "find_common_columns"
        elif "summary" in query_lower or "overview" in query_lower:
            tool = "database_summary"
        else:
            tool = "list_files"
        
        return {
            "intent": f"Fallback to {tool}",
            "steps": [{"tool": tool, "params": {}, "desc": f"Execute {tool}"}],
            "insights": ["Pattern-based fallback"],
            "fallback": True
        }

    def execute_plan(self, plan: Dict[str, Any], schema_tools) -> str:
        """Execute the plan using schema tools."""
        steps = plan.get("steps", [])
        if not steps:
            return schema_tools.list_all_files()
        
        step = steps[0]
        tool_name = step.get("tool", "list_files")
        params = step.get("params", {})
        
        # Execute the appropriate tool
        try:
            if tool_name == "get_file_schema":
                return schema_tools.get_file_schema(params.get("file_name", ""))
            elif tool_name == "list_files":
                return schema_tools.list_all_files()
            elif tool_name == "find_columns":
                return schema_tools.find_columns_with_name(params.get("column_name", ""))
            elif tool_name == "detect_type_mismatches":
                return schema_tools.detect_type_mismatches()
            elif tool_name == "find_common_columns":
                return schema_tools.find_common_columns()
            elif tool_name == "database_summary":
                return schema_tools.get_database_summary()
            elif tool_name == "detect_semantic_type_issues":
                return schema_tools.detect_semantic_type_issues()
            elif tool_name == "detect_column_name_variations":
                return schema_tools.detect_column_name_variations()
            else:
                return schema_tools.list_all_files()
        except Exception as e:
            self.logger.error(f"Error executing {tool_name}: {e}")
            return f"Error executing {tool_name}: {str(e)}"

    def synthesize_response(self, results: str, query: str, plan: Dict[str, Any] = None) -> str:
        """Simple pass-through since schema tools already format responses."""
        return results

    def get_help_text(self) -> str:
        """Get help text."""
        return """
TableTalk - Natural Language Data Exploration

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

Tips: Start with /scan data/ then ask questions in natural language.
        """.strip()
