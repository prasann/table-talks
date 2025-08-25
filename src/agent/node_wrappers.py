"""LangGraph node wrappers for existing TableTalk tools."""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage

from ..tools.tool_registry import ToolRegistry
from ..utils.logger import get_logger
from .langgraph_state import TableTalkState


class ToolNodeWrapper:
    """Wrapper to convert existing TableTalk tools into LangGraph nodes."""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self.logger = get_logger("tabletalk.tool_node_wrapper")
        
    def create_query_analyzer_node(self):
        """Create a node that analyzes the user query and determines tools to use."""
        
        def query_analyzer_node(state: TableTalkState) -> Dict[str, Any]:
            """Analyze query and determine execution strategy."""
            query = state["original_request"]
            self.logger.debug(f"Analyzing query: {query}")
            
            # Simple keyword-based analysis for now (Phase 1)
            # This will be enhanced in later phases with LLM-based analysis
            selected_tools = []
            request_type = "schema"  # default
            
            query_lower = query.lower()
            
            # Pattern matching to determine tools and request type
            if any(word in query_lower for word in ["files", "list", "what files", "show files"]):
                selected_tools.append("get_files")
                request_type = "files"
                
            elif any(word in query_lower for word in ["schema", "structure", "columns", "table"]):
                # For schema queries, first get files then schemas
                selected_tools.append("get_schemas") 
                request_type = "schema"
                
            elif any(word in query_lower for word in ["search", "find", "contains", "where"]):
                selected_tools.append("search_metadata")
                request_type = "search"
                
            elif any(word in query_lower for word in ["statistics", "stats", "count", "size"]):
                selected_tools.append("get_statistics")
                request_type = "analysis"
                
            elif any(word in query_lower for word in ["relationship", "connections", "related"]):
                selected_tools.append("find_relationships")
                request_type = "analysis"
                
            elif any(word in query_lower for word in ["inconsistent", "issues", "problems", "quality"]):
                selected_tools.append("detect_inconsistencies")
                request_type = "analysis"
                
            elif any(word in query_lower for word in ["compare", "difference", "similar"]):
                selected_tools.append("compare_items")
                request_type = "comparison"
                
            elif any(word in query_lower for word in ["analyze", "analysis"]):
                selected_tools.append("run_analysis")
                request_type = "analysis"
            
            # Default to file listing if no clear intent
            if not selected_tools:
                selected_tools = ["get_files"]
                request_type = "files"
                
            self.logger.info(f"Query analysis: type={request_type}, tools={selected_tools}")
            
            return {
                "request_type": request_type,
                "selected_tools": selected_tools,
                "parsed_query": {"keywords": query_lower.split()},
                "workflow_stage": "planning",
                "messages": state.get("messages", []) + [HumanMessage(content=query)]
            }
            
        return query_analyzer_node
    
    def create_tool_execution_node(self):
        """Create a node that executes the selected tools."""
        
        def tool_execution_node(state: TableTalkState) -> Dict[str, Any]:
            """Execute the selected tools and collect results."""
            selected_tools = state.get("selected_tools", [])
            tool_results = {}
            execution_history = []
            
            self.logger.info(f"Executing {len(selected_tools)} tools: {selected_tools}")
            self.logger.debug(f"Current state keys: {list(state.keys())}")
            
            for tool_name in selected_tools:
                try:
                    self.logger.debug(f"Executing tool: {tool_name}")
                    
                    # Extract relevant arguments from query context
                    # For Phase 1, use simple defaults - will enhance in later phases
                    kwargs = self._extract_tool_arguments(state, tool_name)
                    self.logger.debug(f"Tool arguments for {tool_name}: {kwargs}")
                    
                    result = self.tool_registry.execute_tool(tool_name, **kwargs)
                    tool_results[tool_name] = result
                    execution_history.append(tool_name)
                    
                    self.logger.debug(f"Tool {tool_name} executed successfully")
                    
                except Exception as e:
                    error_msg = f"Error executing {tool_name}: {str(e)}"
                    self.logger.error(error_msg)
                    import traceback
                    self.logger.error(f"Full traceback: {traceback.format_exc()}")
                    tool_results[tool_name] = error_msg
                    execution_history.append(f"{tool_name}_error")
            
            # Update specific result fields based on tools executed
            updates = {
                "tool_results": tool_results,
                "execution_history": execution_history,
                "workflow_stage": "formatting"
            }
            
            # Set specific result fields for backward compatibility (only for successful results)
            if "get_files" in tool_results and not tool_results["get_files"].startswith("Error"):
                updates["file_list"] = self._extract_file_list(tool_results["get_files"])
            if "get_schemas" in tool_results and not tool_results["get_schemas"].startswith("Error"):
                updates["schema_data"] = self._extract_schema_data(tool_results["get_schemas"])
            if "search_metadata" in tool_results and not tool_results["search_metadata"].startswith("Error"):
                updates["search_results"] = self._extract_search_results(tool_results["search_metadata"])
            
            # Analysis results (only for successful results)
            analysis_tools = ["get_statistics", "find_relationships", "detect_inconsistencies", "run_analysis"]
            successful_analysis = {tool: result for tool, result in tool_results.items() 
                                 if tool in analysis_tools and not str(result).startswith("Error")}
            if successful_analysis:
                updates["analysis_results"] = successful_analysis
            
            return updates
            
        return tool_execution_node
    
    def create_response_formatter_node(self):
        """Create a node that formats the final response."""
        
        def response_formatter_node(state: TableTalkState) -> Dict[str, Any]:
            """Format the tool results into a user-friendly response."""
            tool_results = state.get("tool_results", {})
            request_type = state.get("request_type", "schema")
            
            if not tool_results:
                formatted_response = "I couldn't find any results for your query."
            else:
                # Simple formatting for Phase 1 - will enhance with LLM-based formatting later
                formatted_response = self._format_results_simple(tool_results, request_type)
            
            # Determine if result should be exported
            export_ready = len(formatted_response) > 100  # Simple heuristic for Phase 1
            
            self.logger.info(f"Response formatted: {len(formatted_response)} characters")
            
            return {
                "formatted_response": formatted_response,
                "export_ready": export_ready,
                "workflow_stage": "complete",
                "messages": state.get("messages", []) + [AIMessage(content=formatted_response)]
            }
            
        return response_formatter_node
    
    def _extract_tool_arguments(self, state: TableTalkState, tool_name: str) -> Dict[str, Any]:
        """Extract arguments for tool execution from state."""
        # For Phase 1, use simple defaults
        # This will be enhanced with LLM-based argument extraction in later phases
        
        query = state.get("original_request", "").lower()
        parsed_query = state.get("parsed_query") or {}  # Handle None case
        keywords = parsed_query.get("keywords", [])
        
        # Default arguments for each tool
        if tool_name == "search_metadata":
            # Look for search terms in keywords
            search_terms = [word for word in keywords if len(word) > 2 and word not in ["the", "and", "for", "with", "search", "find"]]
            return {"query": " ".join(search_terms[:3]) if search_terms else ""}
            
        elif tool_name == "get_schemas":
            # Look for specific file patterns in the original query
            # Skip generic terms and focus on actual file indicators
            file_indicators = ["customers", "orders", "users", "products", "sales"]
            for indicator in file_indicators:
                if indicator in query:
                    return {"file_pattern": indicator}
            return {}  # No arguments - will return all schemas
            
        elif tool_name == "compare_items":
            return {"item_type": "files", "comparison_criteria": "schema"}
            
        # Default empty args for other tools that don't require arguments
        return {}
    
    def _extract_file_list(self, result: str) -> List[str]:
        """Extract file list from get_files result."""
        # Simple parsing - will enhance later
        lines = result.split('\n')
        files = []
        for line in lines:
            if line.strip() and not line.startswith('Found') and not line.startswith('Total'):
                # Extract filename from formatted output
                if ' - ' in line:
                    filename = line.split(' - ')[0].strip()
                    if filename:
                        files.append(filename)
        return files
    
    def _extract_schema_data(self, result: str) -> Dict[str, Any]:
        """Extract schema data from get_schemas result."""
        return {"raw_schema": result}  # Simple for Phase 1
    
    def _extract_search_results(self, result: str) -> Dict[str, Any]:
        """Extract search results from search_metadata result."""
        return {"raw_results": result}  # Simple for Phase 1
        
    def _format_results_simple(self, tool_results: Dict[str, Any], request_type: str) -> str:
        """Simple result formatting for Phase 1."""
        if len(tool_results) == 1:
            # Single tool result
            tool_name, result = next(iter(tool_results.items()))
            return str(result)
        else:
            # Multiple tool results
            formatted_parts = []
            for tool_name, result in tool_results.items():
                formatted_parts.append(f"## {tool_name.replace('_', ' ').title()}\n{result}\n")
            return "\n".join(formatted_parts)