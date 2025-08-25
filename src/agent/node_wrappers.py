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
            """Analyze query and determine execution strategy using intelligent pattern matching."""
            query = state["original_request"]
            self.logger.debug(f"Analyzing query: {query}")
            
            # Enhanced analysis with multiple approaches
            selected_tools = []
            request_type = "schema"  # default
            confidence = 0.5  # confidence in tool selection
            
            query_lower = query.lower()
            tokens = query_lower.split()
            
            # Use intelligent pattern matching with scoring
            analysis_result = self._analyze_query_intent(query_lower, tokens)
            selected_tools = analysis_result["tools"]
            request_type = analysis_result["type"]
            confidence = analysis_result["confidence"]
            
            # Fallback validation - ensure we have at least one tool
            if not selected_tools:
                selected_tools = ["get_files"]
                request_type = "files"
                confidence = 0.3  # Low confidence fallback
                
            self.logger.info(f"Query analysis: type={request_type}, tools={selected_tools}, confidence={confidence:.2f}")
            
            return {
                "request_type": request_type,
                "selected_tools": selected_tools,
                "parsed_query": {
                    "keywords": tokens,
                    "confidence": confidence,
                    "analysis_method": "intelligent_pattern_matching"
                },
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
            # Look for search terms in keywords, but also check the original query for specific terms
            search_terms = [word for word in keywords if len(word) > 2 and word not in ["the", "and", "for", "with", "search", "find"]]
            # Also look for specific identifiers in the original query
            if "customer_id" in query:
                return {"search_term": "customer_id"}
            elif "order_id" in query:
                return {"search_term": "order_id"}
            elif search_terms:
                return {"search_term": " ".join(search_terms[:3])}
            else:
                return {"search_term": ""}
            
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
            
        elif tool_name == "run_analysis":
            # Extract the original request as description for analysis tool
            original_request = state.get("original_request", "")
            return {"description": original_request}
            
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
    
    def _analyze_query_intent(self, query_lower: str, tokens: List[str]) -> Dict[str, Any]:
        """Analyze query intent using intelligent pattern matching with confidence scoring."""
        
        # Define intent patterns with weights and confidence scores
        intent_patterns = {
            "files": {
                "patterns": [
                    (["what", "files"], 0.9),
                    (["files", "list"], 0.85), 
                    (["show", "files"], 0.85),
                    (["all", "files"], 0.8),
                    (["files", "available"], 0.8),
                    (["files", "do", "we", "have"], 0.95)
                ],
                "tools": ["get_files"],
                "exclude_if": ["which"]  # Don't match "which files have" as files query
            },
            "search": {
                "patterns": [
                    (["which", "files", "have"], 0.95),
                    (["files", "have"], 0.9),
                    (["search", "for"], 0.85),
                    (["find", "files"], 0.8),
                    (["contains"], 0.75),
                    (["where"], 0.7)
                ],
                "tools": ["search_metadata"],
                "exclude_if": []
            },
            "schema": {
                "patterns": [
                    (["schema"], 0.95),
                    (["structure"], 0.9),
                    (["columns"], 0.9),
                    (["table", "structure"], 0.85),
                    (["fields"], 0.8),
                    (["format"], 0.7)
                ],
                "tools": ["get_schemas"],
                "exclude_if": []
            },
            "analysis": {
                "patterns": [
                    (["analyze"], 0.95),
                    (["analysis"], 0.9),
                    (["statistics"], 0.9),
                    (["stats"], 0.85),
                    (["issues"], 0.8),
                    (["problems"], 0.8),
                    (["quality"], 0.75),
                    (["relationships"], 0.8),
                    (["connections"], 0.8),
                    (["inconsistent"], 0.85)
                ],
                "tools": ["run_analysis"],
                "exclude_if": []
            },
            "comparison": {
                "patterns": [
                    (["compare"], 0.9),
                    (["difference"], 0.85),
                    (["similar"], 0.85),
                    (["similarities"], 0.9),
                    (["versus"], 0.8),
                    (["vs"], 0.8)
                ],
                "tools": ["compare_items"],
                "exclude_if": []
            }
        }
        
        best_match = {"type": "files", "tools": ["get_files"], "confidence": 0.3}
        
        # Score each intent type
        for intent_type, config in intent_patterns.items():
            score = 0
            matched_patterns = []
            
            # Check exclusion patterns first
            excluded = any(exclude_word in tokens for exclude_word in config["exclude_if"])
            if excluded and intent_type == "files":
                continue
                
            # Score patterns
            for pattern_words, weight in config["patterns"]:
                if all(word in tokens for word in pattern_words):
                    score += weight
                    matched_patterns.append(pattern_words)
                elif any(word in query_lower for word in pattern_words):
                    # Partial match gets partial score
                    score += weight * 0.6
                    matched_patterns.append(pattern_words)
            
            # Bonus for multiple pattern matches
            if len(matched_patterns) > 1:
                score *= 1.2
                
            # Context bonuses
            if intent_type == "analysis":
                # Analysis keywords get bonus in combination
                analysis_indicators = ["data", "dataset", "report", "overview", "insight"]
                if any(indicator in tokens for indicator in analysis_indicators):
                    score *= 1.1
                    
            if intent_type == "search":
                # Search gets bonus with specific identifiers
                identifiers = ["customer_id", "user_id", "order_id", "id", "name"]
                if any(identifier in query_lower for identifier in identifiers):
                    score *= 1.15
            
            # Update best match if this scores higher
            if score > best_match["confidence"]:
                best_match = {
                    "type": intent_type,
                    "tools": config["tools"].copy(),
                    "confidence": score  # Don't cap yet, cap at the end
                }
        
        # Handle multi-tool scenarios for analysis
        if best_match["type"] == "analysis":
            # Analysis might need specific tools based on context
            if any(word in tokens for word in ["relationship", "relationships", "connections", "related"]):
                best_match["tools"] = ["find_relationships"]
            elif any(word in tokens for word in ["inconsistent", "issues", "problems", "quality"]):
                best_match["tools"] = ["detect_inconsistencies"]
            elif any(word in tokens for word in ["statistics", "stats", "count"]):
                best_match["tools"] = ["get_statistics"]
            # Keep run_analysis as default for analysis type
        
        # Cap confidence at 1.0 at the end
        best_match["confidence"] = min(best_match["confidence"], 1.0)
        
        return best_match