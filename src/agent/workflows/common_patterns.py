"""Common workflow patterns for TableTalk LangGraph implementation."""

from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage

from ..langgraph_state import TableTalkState
from ..node_wrappers import ToolNodeWrapper
from ...utils.logger import get_logger


class WorkflowPatterns:
    """Pre-built workflow patterns for common TableTalk operations."""
    
    def __init__(self, tool_node_wrapper: ToolNodeWrapper):
        self.tool_wrapper = tool_node_wrapper
        self.logger = get_logger("tabletalk.workflow_patterns")
        self.model_manager = None  # Phase 2: Will be set by WorkflowAgent
    
    def set_model_manager(self, model_manager):
        """Set the model manager for Phase 2 multi-model support."""
        self.model_manager = model_manager
        self.logger.info("Model manager configured for workflow patterns")
    
    def create_llm_orchestrated_workflow(self) -> StateGraph:
        """Create an advanced workflow using LLM function calling for tool orchestration.
        
        This workflow leverages LLM capabilities for intelligent tool selection:
        1. Analyze user query with LLM
        2. Use LLM to select and orchestrate tools 
        3. Format response with LLM assistance
        """
        workflow = StateGraph(TableTalkState)
        
        # Import LLM orchestrator
        from ..llm_tool_orchestrator import LLMToolOrchestrator
        
        # Create LLM orchestrator
        llm_orchestrator = LLMToolOrchestrator(
            self.tool_wrapper.tool_registry, 
            self.model_manager
        )
        
        # Add nodes
        workflow.add_node("llm_query_analyzer", self._create_llm_query_analyzer_node())
        workflow.add_node("llm_tool_orchestrator", llm_orchestrator.create_llm_orchestrated_execution_node())
        workflow.add_node("llm_response_formatter", self._create_llm_response_formatter_node())
        
        # Define workflow edges
        workflow.add_edge(START, "llm_query_analyzer")
        workflow.add_edge("llm_query_analyzer", "llm_tool_orchestrator")
        workflow.add_edge("llm_tool_orchestrator", "llm_response_formatter")
        workflow.add_edge("llm_response_formatter", END)
        
        self.logger.info("LLM-orchestrated workflow created")
        return workflow
    
    def _create_llm_query_analyzer_node(self):
        """Create a node that uses LLM to analyze queries."""
        
        def llm_query_analyzer_node(state: TableTalkState) -> Dict[str, Any]:
            """Analyze query using LLM reasoning."""
            query = state["original_request"]
            
            self.logger.debug(f"LLM analyzing query: {query}")
            
            # Enhanced analysis using LLM if available
            if self.model_manager and self.model_manager.is_available:
                try:
                    import asyncio
                    
                    # Get event loop
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Use LLM for query understanding
                    analysis_prompt = f"""
                    Analyze this user query and provide insights about what they're asking for:
                    
                    Query: "{query}"
                    
                    Please provide:
                    1. The main intent (what they want to know)
                    2. The complexity level (simple, moderate, complex)
                    3. Any specific entities mentioned (file names, column names, etc.)
                    4. The expected response format they might want
                    
                    Be concise but thorough in your analysis.
                    """
                    
                    response = loop.run_until_complete(
                        self.model_manager.get_best_response(analysis_prompt)
                    )
                    
                    if response.success:
                        self.logger.debug(f"LLM query analysis: {response.content[:100]}...")
                    
                except Exception as e:
                    self.logger.error(f"LLM query analysis failed: {e}")
            
            return {
                "request_type": "llm_analyzed", 
                "selected_tools": [],  # Will be selected by LLM orchestrator
                "parsed_query": {"keywords": query.lower().split()},
                "workflow_stage": "llm_orchestration",
                "messages": state.get("messages", []) + [HumanMessage(content=query)]
            }
            
        return llm_query_analyzer_node
    
    def _create_llm_response_formatter_node(self):
        """Create a node that uses LLM to format responses."""
        
        def llm_response_formatter_node(state: TableTalkState) -> Dict[str, Any]:
            """Format response using LLM assistance."""
            tool_results = state.get("tool_results", {})
            request_type = state.get("request_type", "query")
            original_query = state["original_request"]
            
            if not tool_results:
                formatted_response = "I couldn't find any results for your query."
            else:
                # Try LLM-enhanced formatting if available
                if self.model_manager and self.model_manager.is_available:
                    try:
                        formatted_response = self._llm_format_response(
                            original_query, tool_results, request_type
                        )
                    except Exception as e:
                        self.logger.error(f"LLM formatting failed: {e}")
                        formatted_response = self._simple_format_response(tool_results)
                else:
                    formatted_response = self._simple_format_response(tool_results)
            
            export_ready = len(formatted_response) > 100
            
            self.logger.info(f"LLM-formatted response: {len(formatted_response)} characters")
            
            return {
                "formatted_response": formatted_response,
                "export_ready": export_ready,
                "workflow_stage": "complete",
                "messages": state.get("messages", []) + [
                    type('AIMessage', (), {'content': formatted_response})()
                ]
            }
            
        return llm_response_formatter_node
    
    def _llm_format_response(self, query: str, tool_results: Dict[str, Any], request_type: str) -> str:
        """Use LLM to format the response."""
        import asyncio
        
        # Prepare results summary
        results_summary = []
        for tool_name, result in tool_results.items():
            # Truncate long results for the prompt
            result_str = str(result)
            if len(result_str) > 500:
                result_str = result_str[:497] + "..."
            results_summary.append(f"{tool_name}: {result_str}")
        
        formatting_prompt = f"""
        Format a user-friendly response based on the following:
        
        User Query: "{query}"
        Tool Results:
        {chr(10).join(results_summary)}
        
        Please provide a clear, well-formatted response that:
        1. Directly answers the user's question
        2. Uses the tool results appropriately
        3. Is easy to read and understand
        4. Includes relevant details but isn't overwhelming
        
        Format the response professionally and concisely.
        """
        
        try:
            # Get event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(
                self.model_manager.get_best_response(formatting_prompt)
            )
            
            if response.success and response.content.strip():
                return response.content.strip()
            
        except Exception as e:
            self.logger.error(f"LLM formatting error: {e}")
        
        # Fallback to simple formatting
        return self._simple_format_response(tool_results)
    
    def _simple_format_response(self, tool_results: Dict[str, Any]) -> str:
        """Simple response formatting as fallback."""
        if len(tool_results) == 1:
            tool_name, result = next(iter(tool_results.items()))
            return str(result)
        else:
            formatted_parts = []
            for tool_name, result in tool_results.items():
                formatted_parts.append(f"## {tool_name.replace('_', ' ').title()}\n{result}\n")
            return "\n".join(formatted_parts)
    
    def set_model_manager(self, model_manager):
        """Set the model manager for Phase 2 multi-model support."""
        self.model_manager = model_manager
        self.logger.info("Model manager configured for workflow patterns")
    
    def create_basic_query_workflow(self) -> StateGraph:
        """Create the basic query processing workflow.
        
        This workflow handles the majority of TableTalk queries:
        1. Analyze user query
        2. Execute selected tools  
        3. Format response
        """
        workflow = StateGraph(TableTalkState)
        
        # Add nodes
        workflow.add_node("query_analyzer", self.tool_wrapper.create_query_analyzer_node())
        workflow.add_node("tool_executor", self.tool_wrapper.create_tool_execution_node())
        workflow.add_node("response_formatter", self.tool_wrapper.create_response_formatter_node())
        
        # Define workflow edges
        workflow.add_edge(START, "query_analyzer")
        workflow.add_edge("query_analyzer", "tool_executor")
        workflow.add_edge("tool_executor", "response_formatter")
        workflow.add_edge("response_formatter", END)
        
        self.logger.debug("Basic query workflow created")
        return workflow
    
    def create_schema_exploration_workflow(self) -> StateGraph:
        """Create workflow optimized for schema exploration queries."""
        workflow = StateGraph(TableTalkState)
        
        # Specialized analyzer for schema queries
        def schema_analyzer_node(state: TableTalkState) -> Dict[str, Any]:
            query = state["original_request"]
            self.logger.debug(f"Schema analysis for: {query}")
            
            # Schema-specific tool selection - focus on schemas only
            selected_tools = ["get_schemas"]
            
            # Add statistics if requested
            if any(word in query.lower() for word in ["stats", "count", "size"]):
                selected_tools.append("get_statistics")
                
            return {
                "request_type": "schema",
                "selected_tools": selected_tools,
                "workflow_stage": "planning",
                "messages": state.get("messages", []) + [HumanMessage(content=query)]
            }
        
        workflow.add_node("schema_analyzer", schema_analyzer_node)
        workflow.add_node("tool_executor", self.tool_wrapper.create_tool_execution_node())
        workflow.add_node("response_formatter", self.tool_wrapper.create_response_formatter_node())
        
        workflow.add_edge(START, "schema_analyzer")
        workflow.add_edge("schema_analyzer", "tool_executor")
        workflow.add_edge("tool_executor", "response_formatter")
        workflow.add_edge("response_formatter", END)
        
        self.logger.debug("Schema exploration workflow created")
        return workflow
    
    def create_data_discovery_workflow(self) -> StateGraph:
        """Create workflow for data discovery and search queries."""
        workflow = StateGraph(TableTalkState)
        
        def discovery_analyzer_node(state: TableTalkState) -> Dict[str, Any]:
            query = state["original_request"]
            self.logger.debug(f"Data discovery analysis for: {query}")
            
            # Start with search, then get additional context
            selected_tools = ["search_metadata"]
            
            # Add file listing for context
            if any(word in query.lower() for word in ["files", "which", "what"]):
                selected_tools.insert(0, "get_files")
                
            # Add relationship analysis if relevant
            if any(word in query.lower() for word in ["related", "connection", "link"]):
                selected_tools.append("find_relationships")
                
            return {
                "request_type": "search",
                "selected_tools": selected_tools,
                "workflow_stage": "planning", 
                "messages": state.get("messages", []) + [HumanMessage(content=query)]
            }
        
        workflow.add_node("discovery_analyzer", discovery_analyzer_node)
        workflow.add_node("tool_executor", self.tool_wrapper.create_tool_execution_node())
        workflow.add_node("response_formatter", self.tool_wrapper.create_response_formatter_node())
        
        workflow.add_edge(START, "discovery_analyzer")
        workflow.add_edge("discovery_analyzer", "tool_executor")
        workflow.add_edge("tool_executor", "response_formatter")
        workflow.add_edge("response_formatter", END)
        
        self.logger.debug("Data discovery workflow created")
        return workflow
    
    def create_analysis_workflow(self) -> StateGraph:
        """Create workflow for analysis and data quality queries."""
        workflow = StateGraph(TableTalkState)
        
        def analysis_analyzer_node(state: TableTalkState) -> Dict[str, Any]:
            query = state["original_request"]
            self.logger.debug(f"Analysis workflow for: {query}")
            
            selected_tools = []
            
            # Determine analysis type
            if any(word in query.lower() for word in ["quality", "issues", "problems", "inconsistent"]):
                selected_tools.append("detect_inconsistencies")
            
            if any(word in query.lower() for word in ["statistics", "stats", "summary"]):
                selected_tools.append("get_statistics")
                
            if any(word in query.lower() for word in ["relationship", "connected", "related"]):
                selected_tools.append("find_relationships")
                
            # Generic analysis if nothing specific
            if not selected_tools:
                selected_tools = ["run_analysis"]
                
            return {
                "request_type": "analysis",
                "selected_tools": selected_tools,
                "workflow_stage": "planning",
                "messages": state.get("messages", []) + [HumanMessage(content=query)]
            }
        
        workflow.add_node("analysis_analyzer", analysis_analyzer_node)
        workflow.add_node("tool_executor", self.tool_wrapper.create_tool_execution_node())
        workflow.add_node("response_formatter", self.tool_wrapper.create_response_formatter_node())
        
        workflow.add_edge(START, "analysis_analyzer")
        workflow.add_edge("analysis_analyzer", "tool_executor")
        workflow.add_edge("tool_executor", "response_formatter")
        workflow.add_edge("response_formatter", END)
        
        self.logger.debug("Analysis workflow created")
        return workflow
    
    def create_conditional_router(self) -> callable:
        """Create a router that selects the appropriate workflow based on query type."""
        
        def route_query(state: TableTalkState) -> str:
            """Route query to appropriate workflow based on content analysis."""
            query = state["original_request"].lower()
            
            # Simple keyword-based routing for Phase 1
            if any(word in query for word in ["schema", "structure", "columns", "table"]):
                return "schema_exploration"
            elif any(word in query for word in ["search", "find", "contains", "where"]):
                return "data_discovery"  
            elif any(word in query for word in ["analyze", "analysis", "quality", "issues", "statistics"]):
                return "analysis"
            else:
                return "basic_query"  # Default workflow
                
        return route_query