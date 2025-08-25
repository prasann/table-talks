"""LangGraph state schema for TableTalk workflows."""

from typing import Dict, List, Optional, Any, TypedDict
from langchain_core.messages import BaseMessage


class TableTalkState(TypedDict):
    """Unified state schema for all TableTalk workflows.
    
    This state schema supports all existing TableTalk functionality
    while enabling LangGraph-based orchestration and multi-agent workflows.
    """
    # Core request data
    original_request: str                   # User's original question
    request_type: str                      # "schema", "search", "analysis", "comparison" 
    
    # Query processing state
    parsed_query: Optional[Dict[str, Any]]  # Structured query information
    selected_tools: List[str]              # Tools selected for execution
    
    # Tool execution results
    tool_results: Dict[str, Any]           # Results from each tool execution
    search_results: Optional[Dict]         # Results from search_metadata
    file_list: Optional[List[str]]         # File names found
    schema_data: Optional[Dict]            # Schema information
    analysis_results: Optional[Dict]       # Analysis results
    
    # Workflow orchestration
    workflow_stage: str                    # Current stage: "planning", "execution", "formatting"
    execution_history: List[str]           # Ordered list of executed tools
    error_context: Optional[str]           # Error handling context
    retry_count: int                       # Number of retries attempted
    
    # Output formatting
    formatted_response: str                # Final formatted response
    export_ready: bool                     # Whether result should be exported
    
    # LangGraph internals
    messages: List[BaseMessage]            # Chat history for LLM interactions
    next_action: Optional[str]             # Next workflow action to take