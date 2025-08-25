"""WorkflowAgent - LangGraph-based replacement for SchemaAgent."""

import time
from typing import Dict, Any, List, Tuple, Optional

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from ..utils.logger import get_logger
from ..tools.tool_registry import ToolRegistry
from .langgraph_state import TableTalkState
from .node_wrappers import ToolNodeWrapper  
from .workflows.common_patterns import WorkflowPatterns


class WorkflowAgent:
    """LangGraph-based agent that replaces SchemaAgent.
    
    This agent provides the same interface as SchemaAgent but uses
    LangGraph workflows for reliable sequential function calling
    and better orchestration.
    """
    
    def __init__(self, metadata_store, model_name: str = "phi4-mini-fc", base_url: str = "http://localhost:11434", timeout: int = 120):
        """Initialize WorkflowAgent.
        
        Args:
            metadata_store: Store for metadata operations
            model_name: Name of the model (for compatibility, not used in Phase 1)
            base_url: Base URL (for compatibility, not used in Phase 1)  
            timeout: Timeout for operations
        """
        self.tool_registry = ToolRegistry(metadata_store)
        self.model_name = model_name
        self.base_url = base_url
        self.timeout = timeout
        self.logger = get_logger("tabletalk.workflow_agent")
        
        # Initialize LangGraph components
        self.tool_wrapper = ToolNodeWrapper(self.tool_registry)
        self.workflow_patterns = WorkflowPatterns(self.tool_wrapper)
        
        # Build workflows
        self._build_workflows()
        
        # State for compatibility with existing interface
        self._last_tools_used = []
        self._last_execution_time = 0
        
        self.logger.info(f"WorkflowAgent initialized with LangGraph orchestration (model: {model_name}, timeout: {timeout}s)")
        
    def _build_workflows(self):
        """Build all workflow patterns."""
        self.workflows = {
            "basic_query": self.workflow_patterns.create_basic_query_workflow().compile(),
            "schema_exploration": self.workflow_patterns.create_schema_exploration_workflow().compile(),
            "data_discovery": self.workflow_patterns.create_data_discovery_workflow().compile(),
            "analysis": self.workflow_patterns.create_analysis_workflow().compile()
        }
        
        self.router = self.workflow_patterns.create_conditional_router()
        self.logger.debug(f"Built {len(self.workflows)} workflow patterns")
    
    def query(self, user_query: str) -> str:
        """Process a user query using LangGraph workflows.
        
        This is the main interface method that maintains compatibility
        with the existing SchemaAgent interface.
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Formatted response string
        """
        start_time = time.time()
        
        try:
            # Initialize state
            initial_state = self._create_initial_state(user_query)
            
            # Route to appropriate workflow
            workflow_type = self.router(initial_state)
            workflow = self.workflows[workflow_type]
            
            self.logger.info(f"Processing query with {workflow_type} workflow: {user_query}")
            
            # Execute workflow
            final_state = workflow.invoke(initial_state)
            
            # Extract results for compatibility
            self._last_tools_used = final_state.get("execution_history", [])
            self._last_execution_time = time.time() - start_time
            
            response = final_state.get("formatted_response", "No response generated.")
            
            self.logger.info(f"Query processed successfully in {self._last_execution_time:.2f}s using tools: {self._last_tools_used}")
            return response
            
        except Exception as e:
            self.logger.error(f"Query processing failed: {e}")
            return f"I encountered an error while processing your query: {str(e)}"
    
    def _create_initial_state(self, query: str) -> TableTalkState:
        """Create initial state for workflow execution."""
        return TableTalkState(
            original_request=query,
            request_type="unknown",
            parsed_query=None,
            selected_tools=[],
            tool_results={},
            search_results=None,
            file_list=None,
            schema_data=None,
            analysis_results=None,
            workflow_stage="start",
            execution_history=[],
            error_context=None,
            retry_count=0,
            formatted_response="",
            export_ready=False,
            messages=[],
            next_action=None
        )
    
    # Compatibility methods to maintain interface with existing CLI
    
    def get_last_tools_used(self) -> List[str]:
        """Get tools used in last query execution."""
        return self._last_tools_used
    
    def check_llm_availability(self) -> bool:
        """Check if the agent is available (always True for workflow agent)."""
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information for compatibility."""
        return {
            "agent_type": "WorkflowAgent",
            "mode": "LangGraph Workflows", 
            "model_name": self.model_name,
            "llm_available": True,
            "function_calling": True,  # LangGraph provides structured execution
            "capabilities": [
                "Sequential function calling",
                "Workflow orchestration", 
                "Error handling",
                "Multi-step reasoning"
            ],
            "workflows_available": list(self.workflows.keys()),
            "tools_available": len(self.tool_registry.tools),
            "last_execution_time": self._last_execution_time
        }
    
    def _process_with_function_calling(self, query: str) -> Tuple[str, List[str]]:
        """Compatibility method - redirects to main query method."""
        response = self.query(query)
        return response, self._last_tools_used
        
    def _detect_function_calling(self) -> bool:
        """Compatibility method - WorkflowAgent always supports structured execution."""
        return True