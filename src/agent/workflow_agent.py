"""WorkflowAgent - LangGraph-based replacement for SchemaAgent with Phase 2 multi-model support."""

import time
import asyncio
from typing import Dict, Any, List, Tuple, Optional

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from ..utils.logger import get_logger
from ..tools.tool_registry import ToolRegistry
from .langgraph_state import TableTalkState
from .node_wrappers import ToolNodeWrapper  
from .workflows.common_patterns import WorkflowPatterns
from .model_manager import ModelManager


class WorkflowAgent:
    """LangGraph-based agent that replaces SchemaAgent with Phase 2 multi-model support.
    
    This agent provides the same interface as SchemaAgent but uses:
    - LangGraph workflows for reliable sequential function calling
    - Multi-model architecture for optimal performance and cost
    - Intelligent query routing using LLM-based classification
    """
    
    def __init__(self, metadata_store, model_name: str = "phi4-mini-fc", base_url: str = "http://localhost:11434", timeout: int = 120):
        """Initialize WorkflowAgent with multi-model support.
        
        Args:
            metadata_store: Store for metadata operations
            model_name: Name of the model (for compatibility - actual models managed by ModelManager)
            base_url: Base URL (for compatibility - actual URLs managed by ModelManager)
            timeout: Timeout for operations
        """
        self.tool_registry = ToolRegistry(metadata_store)
        self.model_name = model_name  # Keep for compatibility
        self.base_url = base_url      # Keep for compatibility
        self.timeout = timeout
        self.logger = get_logger("tabletalk.workflow_agent")
        
        # Initialize Phase 2 components
        self.model_manager = ModelManager()
        self.is_initialized = False
        
        # Initialize LangGraph components (will be updated after model manager init)
        self.tool_wrapper = ToolNodeWrapper(self.tool_registry)
        self.workflow_patterns = WorkflowPatterns(self.tool_wrapper)
        
        # State for compatibility with existing interface
        self._last_tools_used = []
        self._last_execution_time = 0
        self._last_classification = None
        
        self.logger.info(f"WorkflowAgent initializing with Phase 2 multi-model architecture (timeout: {timeout}s)")
        
        # Initialize asynchronously
        self._initialize_async()
        
    def _initialize_async(self):
        """Initialize async components in a synchronous context."""
        try:
            # Create event loop if none exists, handle running loop
            loop = None
            try:
                loop = asyncio.get_running_loop()
                # If we're in a running loop, we can't use run_until_complete
                # So we'll skip async initialization and use fallback mode
                self.logger.info("Running in existing event loop, using fallback initialization")
                self._build_workflows_fallback()
                return
            except RuntimeError:
                # No running loop, safe to create one
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
            # Run async initialization
            loop.run_until_complete(self._async_initialize())
        except Exception as e:
            self.logger.error(f"Failed to initialize async components: {e}")
            # Fall back to Phase 1 mode
            self._build_workflows_fallback()
            
    async def _async_initialize(self):
        """Async initialization of model manager and workflows."""
        # Initialize model manager
        if await self.model_manager.initialize():
            self.is_initialized = True
            self.logger.info("Phase 2 multi-model architecture initialized successfully")
            
            # Build workflows with model manager
            self._build_workflows()
        else:
            self.logger.warning("Model manager initialization failed, falling back to Phase 1 mode")
            self._build_workflows_fallback()
            
    def _build_workflows(self):
        """Build workflow patterns with Phase 2 intelligent routing."""
        # Update workflow patterns with model manager
        self.workflow_patterns.set_model_manager(self.model_manager)
        
        # Build workflows
        self.workflows = {
            "basic_query": self.workflow_patterns.create_basic_query_workflow().compile(),
            "schema_exploration": self.workflow_patterns.create_schema_exploration_workflow().compile(),
            "data_discovery": self.workflow_patterns.create_data_discovery_workflow().compile(),
            "analysis": self.workflow_patterns.create_analysis_workflow().compile()
        }
        
        # Use intelligent router instead of simple keyword matching
        self.router = self._create_intelligent_router()
        self.logger.info(f"Phase 2 workflows built with intelligent routing ({len(self.workflows)} workflows)")
        
    def _build_workflows_fallback(self):
        """Fallback workflow building for Phase 1 compatibility."""
        self.workflows = {
            "basic_query": self.workflow_patterns.create_basic_query_workflow().compile(),
            "schema_exploration": self.workflow_patterns.create_schema_exploration_workflow().compile(),
            "data_discovery": self.workflow_patterns.create_data_discovery_workflow().compile(),
            "analysis": self.workflow_patterns.create_analysis_workflow().compile()
        }
        
        self.router = self.workflow_patterns.create_conditional_router()
        self.logger.info(f"Fallback workflows built ({len(self.workflows)} workflows)")
        
    def _create_intelligent_router(self):
        """Create intelligent router using model manager for query classification."""
        
        def intelligent_route(state: TableTalkState) -> str:
            """Route query using LLM-based classification or fallback to keywords."""
            query = state["original_request"]
            
            try:
                # Get event loop
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                # Run async classification
                classification = loop.run_until_complete(
                    self.model_manager.classify_query(query, {"state": state})
                )
                
                # Store classification for debugging/reporting
                self._last_classification = classification
                
                self.logger.info(f"Query classified: {classification.workflow_type} (confidence: {classification.confidence:.2f}) - {classification.reasoning}")
                
                return classification.workflow_type
                
            except Exception as e:
                self.logger.error(f"Intelligent routing failed: {e}")
                
                # Fall back to simple routing
                return self._simple_keyword_route(query)
                
        return intelligent_route
        
    def _simple_keyword_route(self, query: str) -> str:
        """Simple keyword-based routing as ultimate fallback."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["schema", "structure", "columns", "table"]):
            return "schema_exploration"
        elif any(word in query_lower for word in ["search", "find", "contains", "where"]):
            return "data_discovery"
        elif any(word in query_lower for word in ["analyze", "analysis", "quality", "issues", "statistics"]):
            return "analysis"
        else:
            return "basic_query"
    
    def query(self, user_query: str) -> str:
        """Process a user query using LangGraph workflows with Phase 2 intelligent routing.
        
        This is the main interface method that maintains compatibility
        with the existing SchemaAgent interface while providing enhanced
        multi-model capabilities.
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Formatted response string
        """
        start_time = time.time()
        
        try:
            # Initialize state
            initial_state = self._create_initial_state(user_query)
            
            # Route to appropriate workflow using intelligent routing
            workflow_type = self.router(initial_state)
            workflow = self.workflows[workflow_type]
            
            self.logger.info(f"Processing query with {workflow_type} workflow: {user_query}")
            
            # Add classification info to logs if available
            if self._last_classification:
                self.logger.debug(f"Classification: {self._last_classification.reasoning} (confidence: {self._last_classification.confidence:.2f})")
            
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
        """Check if the agent is available."""
        if self.is_initialized:
            # Check if at least one model client is available
            for client in self.model_manager.clients.values():
                if client.is_available:
                    return True
            return False
        else:
            # Fallback mode is always available
            return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information for compatibility with enhanced Phase 2 info."""
        base_status = {
            "agent_type": "WorkflowAgent",
            "mode": "LangGraph Workflows (Phase 2)", 
            "model_name": self.model_name,  # Legacy compatibility
            "llm_available": self.check_llm_availability(),
            "function_calling": True,
            "capabilities": [
                "Sequential function calling",
                "Workflow orchestration", 
                "Error handling",
                "Multi-step reasoning",
                "Intelligent query routing",  # Phase 2
                "Multi-model support"        # Phase 2
            ],
            "workflows_available": list(self.workflows.keys()),
            "tools_available": len(self.tool_registry.tools),
            "last_execution_time": self._last_execution_time
        }
        
        # Add Phase 2 specific information
        if self.is_initialized:
            model_status = self.model_manager.get_status()
            base_status.update({
                "phase": "2",
                "model_manager": model_status,
                "routing_method": "intelligent" if self.is_initialized else "keyword_based",
                "cost_tracking": self.model_manager.get_cost_summary()
            })
            
            # Add last classification info
            if self._last_classification:
                base_status["last_classification"] = {
                    "workflow": self._last_classification.workflow_type,
                    "confidence": self._last_classification.confidence,
                    "reasoning": self._last_classification.reasoning[:100] + "..." if len(self._last_classification.reasoning) > 100 else self._last_classification.reasoning
                }
        else:
            base_status.update({
                "phase": "1 (fallback)",
                "routing_method": "keyword_based"
            })
            
        return base_status
    
    def _process_with_function_calling(self, query: str) -> Tuple[str, List[str]]:
        """Compatibility method - redirects to main query method."""
        response = self.query(query)
        return response, self._last_tools_used
        
    def _detect_function_calling(self) -> bool:
        """Compatibility method - WorkflowAgent always supports structured execution."""
        return True
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed information about available models."""
        if self.is_initialized:
            return self.model_manager.get_status()
        else:
            return {
                "mode": "fallback",
                "primary_model": self.model_name,
                "base_url": self.base_url
            }
            
    def get_cost_summary(self) -> Dict[str, float]:
        """Get cost summary for API usage."""
        if self.is_initialized:
            return self.model_manager.get_cost_summary()
        else:
            return {"total": 0.0}  # Phase 1 fallback is free
            
    async def close(self):
        """Clean up resources asynchronously."""
        if self.is_initialized:
            await self.model_manager.close_all()
            self.logger.info("WorkflowAgent resources cleaned up")
            
    def __del__(self):
        """Ensure resources are cleaned up."""
        if self.is_initialized and hasattr(self, 'model_manager'):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule cleanup for later
                    loop.create_task(self.model_manager.close_all())
                else:
                    loop.run_until_complete(self.model_manager.close_all())
            except Exception as e:
                self.logger.warning(f"Failed to cleanup resources in destructor: {e}")