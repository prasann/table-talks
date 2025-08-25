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