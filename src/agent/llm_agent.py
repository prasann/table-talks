"""LLM Agent for natural language query processing."""

import logging
from typing import List
import requests

try:
    from ..utils.logger import get_logger
    from .context_manager import ContextManager
    from ..tools.schema_tools import SchemaTools
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.logger import get_logger
    from agent.context_manager import ContextManager
    from tools.schema_tools import SchemaTools


class LLMAgent:
    """Agent for processing natural language queries about data schemas."""
    
    def __init__(self, schema_tools: SchemaTools, model_name: str = "phi3", base_url: str = "http://localhost:11434"):
        """Initialize the LLM agent."""
        self.schema_tools = schema_tools
        self.model_name = model_name
        self.base_url = base_url
        self.logger = get_logger("tabletalk.llm_agent")
        
        # Initialize LLM
        self.llm = None
        self._initialize_llm()
        
        # Initialize context manager with LLM if available
        self.context_manager = ContextManager(self if self.llm else None)
    
    def _initialize_llm(self):
        """Initialize the LLM connection."""
        try:
            from langchain_ollama import ChatOllama
            
            # Test if Ollama is available
            test_response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if test_response.status_code == 200:
                self.llm = ChatOllama(
                    model=self.model_name,
                    base_url=self.base_url,
                    temperature=0.1
                )
                self.logger.info(f"LLM initialized with model: {self.model_name}")
            else:
                self.logger.warning("Ollama not available, using basic mode")
                
        except Exception as e:
            self.logger.warning(f"Failed to initialize LLM: {str(e)}. Using basic mode.")
    
    def query(self, user_query: str) -> str:
        """Process a user query and return a response."""
        self.logger.info(f"Processing query: {user_query[:100]}...")
        
        try:
            # Get available files for context
            available_files = self._get_available_files()
            
            # Parse query (will use LLM if available for complex queries)
            plan = self.context_manager.parse_query(user_query, available_files)
            
            # Execute the plan
            results = self.context_manager.execute_plan(plan, self.schema_tools)
            
            # Synthesize response
            response = self.context_manager.synthesize_response(results, user_query, plan)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return f"I encountered an error: {str(e)}\n\nPlease try rephrasing your question."
    
    def _get_available_files(self) -> List[str]:
        """Get list of available files for context."""
        try:
            files_result = self.schema_tools.list_all_files()
            # Simple extraction - just get lines with file extensions
            lines = files_result.split('\n')
            file_names = []
            for line in lines:
                if '.csv' in line or '.parquet' in line:
                    # Extract filename from lines like "- customers.csv: 6 cols, 6 rows"
                    if ':' in line:
                        filename = line.split(':')[0].strip().lstrip('- ')
                        if filename.endswith(('.csv', '.parquet')):
                            file_names.append(filename)
            return file_names
        except Exception:
            return []
    
    def check_llm_availability(self) -> bool:
        """Check if LLM is available."""
        return self.llm is not None

    def get_status(self) -> dict:
        """Get agent status information."""
        return {
            'llm_available': self.llm is not None,
            'model_name': self.model_name,
            'base_url': self.base_url
        }
