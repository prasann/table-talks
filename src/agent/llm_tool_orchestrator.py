"""LLM-based tool orchestrator for intelligent function calling."""

import json
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage

from ..utils.logger import get_logger
from .langgraph_state import TableTalkState
from .model_manager import ModelManager


class LLMToolOrchestrator:
    """Orchestrates tool execution using LLM function calling capabilities."""
    
    def __init__(self, tool_registry, model_manager: Optional[ModelManager] = None):
        self.tool_registry = tool_registry
        self.model_manager = model_manager
        self.logger = get_logger("tabletalk.llm_tool_orchestrator")
        
        # Define available tools for LLM function calling
        self.available_tools = self._define_tool_schemas()
        
    def _define_tool_schemas(self) -> Dict[str, Any]:
        """Define tool schemas for LLM function calling."""
        return {
            "get_files": {
                "name": "get_files",
                "description": "List all available data files in the system",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "get_schemas": {
                "name": "get_schemas",
                "description": "Get schema information for data files",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "file_pattern": {
                            "type": "string",
                            "description": "Optional pattern to filter files (e.g., 'customer', 'orders')"
                        }
                    },
                    "required": []
                }
            },
            "search_metadata": {
                "name": "search_metadata",
                "description": "Search for specific columns, data types, or patterns in metadata",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "Term to search for in column names, data types, etc."
                        }
                    },
                    "required": ["search_term"]
                }
            },
            "run_analysis": {
                "name": "run_analysis",
                "description": "Perform complex analysis on the dataset",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Natural language description of the analysis needed"
                        }
                    },
                    "required": ["description"]
                }
            },
            "find_relationships": {
                "name": "find_relationships",
                "description": "Find relationships and common columns between files",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "detect_inconsistencies": {
                "name": "detect_inconsistencies",
                "description": "Detect data quality issues and inconsistencies",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "get_statistics": {
                "name": "get_statistics",
                "description": "Get statistical information about the dataset",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "compare_items": {
                "name": "compare_items",
                "description": "Compare two items (files, schemas, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "item1": {
                            "type": "string",
                            "description": "First item to compare"
                        },
                        "item2": {
                            "type": "string",
                            "description": "Second item to compare"
                        },
                        "comparison_type": {
                            "type": "string",
                            "enum": ["schemas"],
                            "description": "Type of comparison",
                            "default": "schemas"
                        }
                    },
                    "required": ["item1", "item2"]
                }
            }
        }
    
    async def orchestrate_tools_with_llm(self, state: TableTalkState) -> Dict[str, Any]:
        """Use LLM to intelligently select and execute tools based on the query."""
        
        query = state["original_request"]
        self.logger.info(f"LLM orchestrating tools for: {query}")
        
        if not self.model_manager or not self.model_manager.is_available:
            self.logger.warning("Model manager not available, falling back to simple orchestration")
            return self._fallback_orchestration(state)
        
        try:
            # Create function calling prompt
            function_calling_prompt = self._create_function_calling_prompt(query, state)
            
            # Get LLM to select tools and parameters
            response = await self.model_manager.generate_function_calls(
                function_calling_prompt,
                available_functions=self.available_tools,
                context={"query": query, "state": state}
            )
            
            if response.success and response.function_calls:
                return await self._execute_llm_selected_tools(response.function_calls, state)
            else:
                self.logger.warning("LLM function calling failed, falling back")
                return self._fallback_orchestration(state)
                
        except Exception as e:
            self.logger.error(f"LLM orchestration failed: {e}")
            return self._fallback_orchestration(state)
    
    def _create_function_calling_prompt(self, query: str, state: TableTalkState) -> str:
        """Create a prompt for LLM function calling."""
        
        tool_descriptions = []
        for tool_name, tool_info in self.available_tools.items():
            tool_descriptions.append(f"- {tool_name}: {tool_info['description']}")
        
        return f"""
You are a data analysis assistant helping users explore and analyze datasets. 
Based on the user's query, select the most appropriate tools to use and provide the parameters.

User Query: "{query}"

Available Tools:
{chr(10).join(tool_descriptions)}

Instructions:
1. Analyze the user's intent carefully
2. Select the most appropriate tool(s) to answer their question
3. Provide accurate parameters for each tool
4. If multiple tools are needed, order them logically
5. Consider what information might be needed as prerequisites

Respond with a JSON object containing:
{{
    "reasoning": "Explain your tool selection logic",
    "function_calls": [
        {{
            "name": "tool_name",
            "parameters": {{ "param1": "value1", "param2": "value2" }}
        }}
    ]
}}

Focus on providing the most helpful and accurate response to the user's question.
"""
    
    async def _execute_llm_selected_tools(self, function_calls: List[Dict[str, Any]], state: TableTalkState) -> Dict[str, Any]:
        """Execute the tools selected by the LLM."""
        
        tool_results = {}
        execution_history = []
        
        for func_call in function_calls:
            tool_name = func_call.get("name")
            parameters = func_call.get("parameters", {})
            
            if tool_name in self.available_tools:
                try:
                    self.logger.info(f"Executing LLM-selected tool: {tool_name} with params: {parameters}")
                    
                    result = self.tool_registry.execute_tool(tool_name, **parameters)
                    tool_results[tool_name] = result
                    execution_history.append(f"{tool_name}_llm_selected")
                    
                    self.logger.debug(f"Tool {tool_name} executed successfully")
                    
                except Exception as e:
                    error_msg = f"Error executing LLM-selected tool {tool_name}: {str(e)}"
                    self.logger.error(error_msg)
                    tool_results[tool_name] = error_msg
                    execution_history.append(f"{tool_name}_error")
            else:
                self.logger.warning(f"LLM selected unknown tool: {tool_name}")
        
        # Update state with results
        updates = {
            "tool_results": tool_results,
            "execution_history": execution_history,
            "workflow_stage": "formatting",
            "orchestration_method": "llm_function_calling"
        }
        
        # Set specific result fields for backward compatibility
        if "get_files" in tool_results and not tool_results["get_files"].startswith("Error"):
            updates["file_list"] = self._extract_file_list(tool_results["get_files"])
        if "get_schemas" in tool_results and not tool_results["get_schemas"].startswith("Error"):
            updates["schema_data"] = {"raw_schema": tool_results["get_schemas"]}
        if "search_metadata" in tool_results and not tool_results["search_metadata"].startswith("Error"):
            updates["search_results"] = {"raw_results": tool_results["search_metadata"]}
        
        # Analysis results
        analysis_tools = ["get_statistics", "find_relationships", "detect_inconsistencies", "run_analysis"]
        successful_analysis = {tool: result for tool, result in tool_results.items() 
                             if tool in analysis_tools and not str(result).startswith("Error")}
        if successful_analysis:
            updates["analysis_results"] = successful_analysis
        
        return updates
    
    def _fallback_orchestration(self, state: TableTalkState) -> Dict[str, Any]:
        """Fallback to simple tool orchestration when LLM is unavailable."""
        
        # Use the intelligent pattern matching from node_wrappers as fallback
        from .node_wrappers import ToolNodeWrapper
        
        wrapper = ToolNodeWrapper(self.tool_registry)
        analyzer_node = wrapper.create_query_analyzer_node()
        executor_node = wrapper.create_tool_execution_node()
        
        # Analyze and execute
        analyzed_state = analyzer_node(state)
        execution_result = executor_node(analyzed_state)
        
        # Add orchestration method marker
        execution_result["orchestration_method"] = "intelligent_pattern_matching_fallback"
        
        return execution_result
    
    def _extract_file_list(self, result: str) -> List[str]:
        """Extract file list from get_files result."""
        lines = result.split('\n')
        files = []
        for line in lines:
            if line.strip() and not line.startswith('Found') and not line.startswith('Total'):
                if ' - ' in line:
                    filename = line.split(' - ')[0].strip()
                    if filename:
                        files.append(filename)
        return files
    
    def create_llm_orchestrated_execution_node(self):
        """Create a LangGraph node that uses LLM for tool orchestration."""
        
        def llm_orchestrated_execution_node(state: TableTalkState) -> Dict[str, Any]:
            """Execute tools using LLM orchestration."""
            
            # Run async LLM orchestration
            try:
                import asyncio
                
                # Get or create event loop
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Run orchestration
                result = loop.run_until_complete(
                    self.orchestrate_tools_with_llm(state)
                )
                
                return result
                
            except Exception as e:
                self.logger.error(f"LLM orchestration node failed: {e}")
                return self._fallback_orchestration(state)
        
        return llm_orchestrated_execution_node