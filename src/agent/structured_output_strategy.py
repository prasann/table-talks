"""Structured output strategy using LangChain integration for TableTalk."""

import json
import logging
import re
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

from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.messages import AIMessage


class StructuredOutputStrategy(QueryProcessingStrategy):
    """Query processing strategy using LangChain with structured output."""
    
    def __init__(self, llm_agent=None):
        """Initialize the structured output strategy."""
        self.llm = llm_agent
        self.logger = get_logger("tabletalk.structured_output")
        
        # Keep tool definitions for fallback and reference
        self.available_tools = {
            "get_file_schema": {
                "description": "Get detailed schema information for a specific file (columns, data types, statistics)",
                "parameters": ["file_name"],
                "examples": ["schema of customers.csv", "columns in orders", "describe legacy_users"]
            },
            "list_files": {
                "description": "List all scanned files with basic statistics (column count, row count, file size)",
                "parameters": [],
                "examples": ["what files do we have", "list all files", "show me files"]
            },
            "find_columns": {
                "description": "Find all files that contain a column with a specific name",
                "parameters": ["column_name"],
                "examples": ["which files have user_id", "find customer_id column", "search for email"]
            },
            "detect_type_mismatches": {
                "description": "Detect columns with same name but different data types across files",
                "parameters": [],
                "examples": ["type mismatches", "data type inconsistencies", "conflicting types"]
            },
            "find_common_columns": {
                "description": "Find columns that appear in multiple files",
                "parameters": [],
                "examples": ["common columns", "shared columns", "overlapping fields"]
            },
            "database_summary": {
                "description": "Get overall database statistics (total files, columns, summary)",
                "parameters": [],
                "examples": ["database summary", "overview", "how many files", "stats"]
            },
            "search_column_values": {
                "description": "Search for specific values in all columns across all files",
                "parameters": ["search_term"],
                "examples": ["find gmail.com", "search for 2023", "look for NULL values"]
            }
        }
        
        # Define structured tool schemas for LangChain
        self.tools = self._setup_tools()

    def _setup_tools(self) -> List[StructuredTool]:
        """Define structured tools for LangChain integration."""
        tools = []
        
        # Define parameter models
        class FileNameSchema(BaseModel):
            file_name: str = Field(..., description="The name of the file to analyze")
            
        class ColumnNameSchema(BaseModel):
            column_name: str = Field(..., description="The name of the column to search for")
        
        # Define tools with their schemas
        tools.append(
            StructuredTool.from_function(
                func=lambda file_name: {"tool": "get_file_schema", "params": {"file_name": file_name}},
                name="get_file_schema",
                description="Get detailed schema for a specific file (columns, data types, statistics)",
                args_schema=FileNameSchema
            )
        )
        
        tools.append(
            StructuredTool.from_function(
                func=lambda: {"tool": "list_files", "params": {}},
                name="list_files",
                description="List all scanned files with basic statistics (column count, row count, file size)"
            )
        )
        
        tools.append(
            StructuredTool.from_function(
                func=lambda column_name: {"tool": "find_columns", "params": {"column_name": column_name}},
                name="find_columns",
                description="Find all files that contain a column with a specific name",
                args_schema=ColumnNameSchema
            )
        )
        
        # Add remaining tools without parameters
        for tool_name in ["detect_type_mismatches", "find_common_columns", "database_summary"]:
            tools.append(
                StructuredTool.from_function(
                    func=lambda: {"tool": tool_name, "params": {}},
                    name=tool_name,
                    description=self.available_tools[tool_name]["description"]
                )
            )
        
        return tools

    def parse_query(self, query: str, available_files: List[str] = None) -> Dict[str, Any]:
        """Parse query using LLM with structured output.
        
        Returns:
            Dictionary with success/error status and parsed query
        """
        try:
            if not self.llm:
                self.logger.error("LLM not available for query parsing")
                fallback_result = {
                    "intent": "LLM not available",
                    "steps": [{"tool": "list_files", "params": {}, "desc": "Default action - list files"}],
                    "insights": ["LLM required for query parsing"],
                    "strategy": "structured_output_unavailable",
                    "error": True
                }
                return {
                    "success": True,  # Still successful, just using fallback
                    "parsed_query": fallback_result
                }

            parsed_result = self._structured_output_parse(query, available_files)
            return {
                "success": True,
                "parsed_query": parsed_result
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing query: {e}")
            return {
                "success": False,
                "error": f"Failed to parse query: {str(e)}"
            }
    
    def _structured_output_parse(self, query: str, available_files: List[str] = None) -> Dict[str, Any]:
        """Use LLM to parse queries with structured output."""
        try:
            # Create context with available files if provided
            files_context = f"Available files: {', '.join(available_files[:10])}" if available_files else "No files scanned yet."
            
            # Build tool descriptions for the prompt
            tool_descriptions = "\n".join([
                f"- {tool.name}: {tool.description}" 
                for tool in self.tools
            ])
            
            prompt = f"""You are a data exploration assistant helping users analyze their data files.
            
{files_context}

Available tools:
{tool_descriptions}

Analyze the user's query and select ONE tool that best matches what the user wants.
Your response must be in JSON format with this structure:
{{
  "tool": "tool_name",
  "parameters": {{...}} 
}}

User query: {query}"""
            
            # Call LLM with standard invoke
            self.logger.debug(f"Calling LLM with query: {query}")
            
            response = self.llm.llm.invoke(prompt)
            self.logger.debug(f"LLM response: {response}")
            
            # For LangChain, the response is an AIMessage with content
            if hasattr(response, "content"):
                content = response.content
                self.logger.debug(f"LLM content: {content[:100]}...")
                
                # Try to parse JSON from the response
                try:
                    # Find JSON object in the response
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        tool_info = json.loads(json_str)
                        
                        tool_name = tool_info.get("tool")
                        parameters = tool_info.get("parameters", {})
                        
                        self.logger.debug(f"Successfully parsed tool: {tool_name} with params: {parameters}")
                        
                        # Validate the tool exists
                        if tool_name in self.available_tools:
                            # Format file name parameter if needed
                            if "file_name" in parameters and not parameters["file_name"].endswith(('.csv', '.parquet')):
                                parameters["file_name"] = f"{parameters['file_name']}.csv"
                            
                            return {
                                "intent": f"Using {tool_name} to answer query",
                                "steps": [{
                                    "tool": tool_name,
                                    "params": parameters,
                                    "desc": f"Execute {tool_name} with parameters"
                                }],
                                "insights": [f"Structured output selected: {tool_name}"],
                                "strategy": "structured_output",
                                "llm_mode": True
                            }
                    
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON from response: {e}")
                
                # Fallback: Look for tool name mentions in content
                for tool_name in self.available_tools.keys():
                    if tool_name in content.lower():
                        self.logger.info(f"Found tool mention in content: {tool_name}")
                        # Extract potential parameters
                        params = {}
                        if "file_name" in self.available_tools[tool_name]["parameters"]:
                            # Try to find filename mentions
                            for file in (available_files or []):
                                if file.lower() in content.lower():
                                    params["file_name"] = file
                                    break
                        
                        if "column_name" in self.available_tools[tool_name]["parameters"]:
                            # Simple extraction
                            col_match = re.search(r"column[:\s]+(\w+)", content, re.IGNORECASE)
                            if col_match:
                                params["column_name"] = col_match.group(1)
                        
                        return {
                            "intent": f"Using {tool_name} (content extraction)",
                            "steps": [{
                                "tool": tool_name,
                                "params": params,
                                "desc": f"Execute {tool_name}"
                            }],
                            "insights": ["Extracted from text response"],
                            "strategy": "structured_output_extraction",
                            "llm_mode": True
                        }
            
            # If no tool found or parsing failed, fall back to default
            self.logger.warning("Could not parse a valid tool from the response")
            return self._default_fallback(query)
                
        except Exception as e:
            self.logger.error(f"Structured output parsing failed: {str(e)}")
            return self._default_fallback(query)

    def execute_plan(self, plan: Dict[str, Any], schema_tools) -> Dict[str, Any]:
        """Execute plan and return results.
        
        Returns:
            Dictionary with success/error status and results
        """
        try:
            if plan.get("error"):
                result = schema_tools.list_all_files()
                return {
                    "success": True,
                    "result": result
                }
            
            # Simple tool execution - just handle the single tool case
            steps = plan.get("steps", [])
            if not steps:
                result = schema_tools.list_all_files()
                return {
                    "success": True,
                    "result": result
                }
            
            # Execute single tool (simplified from multi-step)
            step = steps[0]  # Take first step only
            tool_name = step.get("tool", "list_files")
            params = step.get("params", {})
            
            # Tool mapping with parameter handling
            self.logger.debug(f"Executing tool: {tool_name} with params: {params}")
            
            if tool_name == "get_file_schema":
                result = schema_tools.get_file_schema(params.get("file_name", ""))
            elif tool_name == "list_files":
                result = schema_tools.list_all_files()
            elif tool_name == "find_columns":
                result = schema_tools.find_columns_with_name(params.get("column_name", ""))
            elif tool_name == "detect_type_mismatches":
                result = schema_tools.detect_type_mismatches()
            elif tool_name == "find_common_columns":
                result = schema_tools.find_common_columns()
            elif tool_name == "database_summary":
                result = schema_tools.get_database_summary()
            elif tool_name == "detect_semantic_type_issues":
                result = schema_tools.detect_semantic_type_issues()
            elif tool_name == "detect_column_name_variations":
                result = schema_tools.detect_column_name_variations()
            else:
                self.logger.warning(f"Unknown tool: {tool_name}, defaulting to list_files")
                result = schema_tools.list_all_files()
            
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
            self.logger.error(f"Error executing {tool_name}: {e}")
            return f"Error executing {tool_name}: {str(e)}"
    
    def synthesize_response(self, query: str, plan: Dict[str, Any], results: str) -> Dict[str, Any]:
        """Format results for user display.
        
        Returns:
            Dictionary with success status and response
        """
        try:
            return {
                "success": True,
                "response": results  # Simple pass-through since results are already formatted
            }
        except Exception as e:
            self.logger.error(f"Error synthesizing response: {e}")
            return {
                "success": False,
                "error": f"Error synthesizing response: {str(e)}"
            }

    def get_help_text(self) -> str:
        """Get help text for structured output strategy."""
        return """
TableTalk - Structured Output Mode

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
  
Advanced Queries:
  • "Compare schemas across all files and find inconsistencies"
  • "Check data quality issues and suggest fixes"
  • "Find relationships between files"

Tips: Start with /scan data/ then ask questions in natural language.
        """.strip()

    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about this strategy."""
        llm_available = self.llm is not None
        return {
            "name": "Structured Output Strategy", 
            "type": "structured_output",
            "llm_available": llm_available,
            "capabilities": ["structured_prompting", "json_parsing", "tool_selection"] if llm_available else ["pattern_matching"],
            "reliability": "medium" if llm_available else "low",
            "performance": "good" if llm_available else "basic"
        }

    def _default_fallback(self, query: str) -> Dict[str, Any]:
        """Fallback to basic pattern matching when LLM fails."""
        query_lower = query.lower()
        
        # Pattern-based fallbacks for common queries
        if "schema" in query_lower and "compare" in query_lower:
            return {
                "intent": "Compare schemas across files",
                "steps": [{"tool": "detect_type_mismatches", "params": {}, "desc": "Detect type mismatches across files"}],
                "insights": ["Fallback: Schema comparison"],
                "strategy": "structured_output_fallback",
                "fallback": True
            }
        elif "type" in query_lower and ("mismatch" in query_lower or "inconsisten" in query_lower):
            return {
                "intent": "Find type mismatches",
                "steps": [{"tool": "detect_type_mismatches", "params": {}, "desc": "Detect type mismatches"}],
                "insights": ["Fallback: Type mismatch detection"],
                "strategy": "structured_output_fallback",
                "fallback": True
            }
        elif "files" in query_lower and "have" in query_lower:
            return {
                "intent": "List available files",
                "steps": [{"tool": "list_files", "params": {}, "desc": "List all files"}],
                "insights": ["Fallback: File listing"],
                "strategy": "structured_output_fallback",
                "fallback": True
            }
        elif "schema" in query_lower and any(word in query_lower for word in ["customer", "order", "review", "legacy"]):
            # Try to extract filename
            filename = None
            for word in ["customer", "order", "review", "legacy"]:
                if word in query_lower:
                    filename = f"{word}s.csv" if not word.endswith('s') else f"{word}.csv"
                    break
            return {
                "intent": f"Get schema for {filename}",
                "steps": [{"tool": "get_file_schema", "params": {"file_name": filename}, "desc": f"Get schema for {filename}"}],
                "insights": [f"Fallback: Schema for {filename}"],
                "strategy": "structured_output_fallback",
                "fallback": True
            }
        else:
            return {
                "intent": "Default fallback",
                "steps": [{"tool": "list_files", "params": {}, "desc": "Show available files"}],
                "insights": ["Fallback action due to parsing error"],
                "strategy": "structured_output_fallback",
                "error": True
            }
