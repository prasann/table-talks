"""Context management with pure LLM-based query parsing for TableTalk."""

import json
import logging
import re
from typing import Dict, List, Optional, Any

try:
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.logger import get_logger


class ContextManager:
    """Manages conversation context and LLM-based query parsing."""
    
    def __init__(self, llm_agent=None):
        """Initialize the context manager."""
        self.llm = llm_agent
        self.logger = get_logger("tabletalk.context")
        
        # Available tools and their descriptions
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
                "examples": ["type mismatches", "data type inconsistencies", "conflicting types", "discrepancies with data types"]
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
            "detect_semantic_type_issues": {
                "description": "Detect columns with incorrect data types based on naming patterns",
                "parameters": [],
                "examples": ["semantic type issues", "data quality problems", "type validation"]
            },
            "detect_column_name_variations": {
                "description": "Detect columns that represent same field but have different naming conventions",
                "parameters": [],
                "examples": ["column name variations", "naming inconsistencies", "standardization issues"]
            }
        }

    def parse_query(self, query: str, available_files: List[str] = None) -> Dict[str, Any]:
        """Parse query using LLM."""
        if not self.llm:
            self.logger.error("LLM not available for query parsing")
            return {
                "intent": "LLM not available",
                "steps": [{"tool": "list_files", "params": {}, "desc": "Default action - list files"}],
                "insights": ["LLM required for query parsing"],
                "error": True
            }
        
        return self._llm_parse(query, available_files)

    def _llm_parse(self, query: str, available_files: List[str] = None) -> Dict[str, Any]:
        """Use LLM to parse all queries."""
        try:
            # Build tool descriptions for the LLM
            tools_description = self._build_tools_description()
            files_context = f"\nAvailable files: {', '.join(available_files[:10])}" if available_files else ""
            
            prompt = f"""You are a data exploration assistant. Analyze this query and determine the best tool to use.

Query: "{query}"

Available Tools:
{tools_description}
{files_context}

Respond with EXACTLY ONE valid JSON object. NO extra text, NO comments, NO explanations outside the JSON.

Required format:
{{
    "intent": "brief description",
    "tool": "exact_tool_name_from_list",
    "parameters": {{}},
    "confidence": 0.9,
    "reasoning": "brief explanation"
}}

CRITICAL RULES:
- Return ONLY the JSON object
- NO comments (// or /* */)
- NO multiple objects
- NO text before or after the JSON
- Use exactly ONE of these tools: {', '.join(self.available_tools.keys())}
- Parameters can be empty {{}} if tool requires no parameters

Examples:
Query: "schema of users" → {{"intent": "Get schema", "tool": "get_file_schema", "parameters": {{"file_name": "users.csv"}}, "confidence": 0.9, "reasoning": "User wants file schema"}}
Query: "type mismatches" → {{"intent": "Find type issues", "tool": "detect_type_mismatches", "parameters": {{}}, "confidence": 0.9, "reasoning": "User wants type mismatch detection"}}"""

            response = self.llm.llm.invoke(prompt)
            self.logger.debug(f"LLM response: {response}")
            
            # Extract content from AIMessage object
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON from response - try multiple approaches
            # First try to find a complete JSON object
            json_start = response_text.find('{')
            if json_start != -1:
                # Look for the first complete JSON object
                brace_count = 0
                json_end = json_start
                for i, char in enumerate(response_text[json_start:], json_start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i
                            break
                
                if json_end > json_start:
                    json_str = response_text[json_start:json_end+1]
                    try:
                        result = json.loads(json_str)
                        # Validate and format the result
                        return self._format_llm_result(result, query)
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"JSON parse error: {e}, trying to clean: {json_str[:100]}")
                        # Try to clean common issues
                        cleaned_json = self._clean_json_response(json_str)
                        if cleaned_json:
                            try:
                                result = json.loads(cleaned_json)
                                return self._format_llm_result(result, query)
                            except json.JSONDecodeError:
                                pass
            
            self.logger.error(f"No valid JSON found in LLM response: {response_text}")
            return self._default_fallback(query)
                
        except Exception as e:
            self.logger.error(f"LLM parsing failed: {e}")
            return self._default_fallback(query)

    def _clean_json_response(self, json_str: str) -> Optional[str]:
        """Try to clean common JSON formatting issues from LLM responses."""
        try:
            # Remove trailing commas and extra braces
            cleaned = json_str.strip()
            
            # Remove JSON comments (// ... and /* ... */)
            import re
            cleaned = re.sub(r'//.*?$', '', cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
            
            # Fix confidence values like "00.95" -> "0.95"
            cleaned = re.sub(r'"confidence":\s*00\.(\d+)', r'"confidence": 0.\1', cleaned)
            
            # Remove any duplicate field declarations (keep the first occurrence)
            # This handles cases where "intent" or "tool" appear multiple times
            fields_seen = set()
            lines = cleaned.split('\n')
            clean_lines = []
            skip_until_comma = False
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('}'):
                    clean_lines.append(line)
                    continue
                
                # Check for field declarations
                field_match = re.match(r'"(\w+)":\s*', line)
                if field_match:
                    field_name = field_match.group(1)
                    if field_name in fields_seen:
                        skip_until_comma = True
                        continue
                    else:
                        fields_seen.add(field_name)
                        skip_until_comma = False
                        clean_lines.append(line)
                elif not skip_until_comma:
                    clean_lines.append(line)
                elif line.endswith(','):
                    skip_until_comma = False
            
            cleaned = '\n'.join(clean_lines)
            
            # Remove any content after the first complete JSON object
            brace_count = 0
            end_pos = 0
            for i, char in enumerate(cleaned):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break
            
            if end_pos > 0:
                cleaned = cleaned[:end_pos]
            
            return cleaned
        except Exception as e:
            self.logger.warning(f"JSON cleaning failed: {e}")
            return None

    def _build_tools_description(self) -> str:
        """Build a formatted description of all available tools."""
        descriptions = []
        for tool_name, tool_info in self.available_tools.items():
            desc = f"{tool_name}: {tool_info['description']}"
            if tool_info['parameters']:
                desc += f" (params: {', '.join(tool_info['parameters'])})"
            descriptions.append(desc)
        return "\n".join(descriptions)

    def _format_llm_result(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Format and validate LLM result."""
        tool_name = result.get("tool", "list_files")
        parameters = result.get("parameters", {})
        intent = result.get("intent", "Data exploration")
        
        # Validate tool exists
        if tool_name not in self.available_tools:
            self.logger.warning(f"LLM suggested unknown tool: {tool_name}")
            tool_name = "list_files"
            parameters = {}
        
        # Handle file name parameter - ensure .csv extension
        if "file_name" in parameters:
            file_name = parameters["file_name"]
            if not file_name.endswith(('.csv', '.parquet')):
                parameters["file_name"] = f"{file_name}.csv"
        
        return {
            "intent": intent,
            "steps": [{
                "tool": tool_name,
                "params": parameters,
                "desc": result.get("reasoning", f"Execute {tool_name}")
            }],
            "insights": [f"LLM analysis: {intent}"],
            "llm_mode": True
        }

    def _default_fallback(self, query: str) -> Dict[str, Any]:
        """Default fallback when LLM fails - use pattern matching."""
        query_lower = query.lower()
        
        # Pattern-based fallbacks for common queries
        if "schema" in query_lower and "compare" in query_lower:
            return {
                "intent": "Compare schemas across files",
                "steps": [{"tool": "detect_type_mismatches", "params": {}, "desc": "Detect type mismatches across files"}],
                "insights": ["Fallback: Schema comparison"],
                "fallback": True
            }
        elif "type" in query_lower and ("mismatch" in query_lower or "inconsisten" in query_lower):
            return {
                "intent": "Find type mismatches",
                "steps": [{"tool": "detect_type_mismatches", "params": {}, "desc": "Detect type mismatches"}],
                "insights": ["Fallback: Type mismatch detection"],
                "fallback": True
            }
        elif "files" in query_lower and "have" in query_lower:
            return {
                "intent": "List available files",
                "steps": [{"tool": "list_files", "params": {}, "desc": "List all files"}],
                "insights": ["Fallback: File listing"],
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
                "fallback": True
            }
        else:
            return {
                "intent": "Default fallback",
                "steps": [{"tool": "list_files", "params": {}, "desc": "Show available files"}],
                "insights": ["Fallback action due to parsing error"],
                "error": True
            }

    def execute_plan(self, plan: Dict[str, Any], schema_tools) -> str:
        """Execute plan and return results."""
        if plan.get("error"):
            return schema_tools.list_all_files()
        
        # Simple tool execution - just handle the single tool case
        steps = plan.get("steps", [])
        if not steps:
            return schema_tools.list_all_files()
        
        # Execute single tool (simplified from multi-step)
        step = steps[0]  # Take first step only
        tool_name = step.get("tool", "list_files")
        params = step.get("params", {})
        
        # Tool mapping with parameter handling
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
                return schema_tools.list_all_files()  # Default fallback
        except Exception as e:
            self.logger.error(f"Error executing {tool_name}: {e}")
            return f"Error executing {tool_name}: {str(e)}"
    
    def synthesize_response(self, results: str, query: str, plan: Dict[str, Any]) -> str:
        """Format results for user display."""
        return results  # Simple pass-through since results are already formatted
    
    def _default_fallback(self, query: str) -> Dict[str, Any]:
        """Fallback to basic file listing when parsing fails."""
        return {
            "intent": "Basic file listing",
            "steps": [{"tool": "list_files", "params": {}, "desc": "List all available files"}],
            "insights": ["Basic file overview when unable to parse query"],
            "error": False
        }
    
    def _basic_suggestions(self, results: str) -> List[str]:
        """Generate basic suggestions when LLM unavailable."""
        suggestions = []
        
        if "mismatch" in results.lower():
            suggestions.append("Investigate the cause of these type mismatches")
        if "null" in results.lower():
            suggestions.append("Check data quality issues with null values")
        if "files" in results.lower():
            suggestions.append("Explore specific file schemas")
        
        if not suggestions:
            suggestions = [
                "Check for data quality issues",
                "Look for common columns across files", 
                "Explore your largest files"
            ]
        
        return suggestions[:3]

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
  
Advanced Queries (with LLM):
  • "Compare schemas across all files and find inconsistencies"
  • "Check data quality issues and suggest fixes"
  • "Find relationships between files"

Tips: Start with /scan data/ then ask questions in natural language.
        """.strip()
