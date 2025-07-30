"""Base strategy interface for query processing in TableTalk."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class QueryProcessingStrategy(ABC):
    """Abstract base class for query processing strategies."""
    
    @abstractmethod
    def parse_query(self, query: str, available_files: List[str] = None) -> Dict[str, Any]:
        """Parse a user query and determine the appropriate tool to use.
        
        Args:
            query: The user's natural language query
            available_files: List of available files for context
            
        Returns:
            Dictionary containing:
            - intent: Brief description of what the query is asking
            - steps: List of tool execution steps
            - insights: List of insights about the query processing
            - Additional metadata (llm_mode, fallback, etc.)
        """
        pass
    
    @abstractmethod
    def execute_plan(self, plan: Dict[str, Any], schema_tools) -> str:
        """Execute the parsed plan using schema tools.
        
        Args:
            plan: The plan returned by parse_query
            schema_tools: SchemaTools instance for executing operations
            
        Returns:
            Formatted results string
        """
        pass
    
    @abstractmethod
    def synthesize_response(self, results: str, query: str, plan: Dict[str, Any] = None) -> str:
        """Synthesize the final response for the user.
        
        Args:
            results: Raw results from tool execution
            query: Original user query
            plan: The execution plan (optional)
            
        Returns:
            Final formatted response for the user
        """
        pass
    
    @abstractmethod
    def get_help_text(self) -> str:
        """Get help text for this strategy.
        
        Returns:
            Help text string
        """
        pass
    
    @abstractmethod
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about this strategy.
        
        Returns:
            Dictionary with strategy metadata
        """
        pass
